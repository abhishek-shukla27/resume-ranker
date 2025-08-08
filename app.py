import streamlit as st
from ai_suggester import get_suggestions
from matcher import calculate_match_score
import fitz  # PyMuPDF
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth as admin_auth
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Space
from reportlab.lib.units import mm

# --------------- CONFIG & THEME ---------------- #
st.set_page_config(page_title="Resume Ranker", layout="centered", page_icon="📄")

# Hide Streamlit default menu & footer
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Custom CSS
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #0f172a, #1e293b, #0f172a);
        color: white;
        font-family: 'Segoe UI', sans-serif;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.07);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    textarea, .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border-radius: 10px;
        border: none;
    }
    textarea:focus, .stTextInput>div>div>input:focus {
        border: 1px solid #38bdf8 !important;
        outline: none !important;
    }
    .keyword-chip {
        display: inline-block;
        padding: 5px 12px;
        margin: 4px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 500;
        color: white;
    }
    .matched { background-color: #22c55e; }
    .missing { background-color: #ef4444; }
    .suggest-card {
        background: rgba(255, 255, 255, 0.12);
        padding: 1rem;
        border-radius: 15px;
        margin-top: 1rem;
    }
    h1, h2, h3, h4 { color: white; }
    </style>
""", unsafe_allow_html=True)

# --------------- FIREBASE AUTH ---------------- #
FIREBASE_JSON_PATH = "resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_JSON_PATH)
    firebase_admin.initialize_app(cred)

def verify_token(id_token):
    try:
        decoded = admin_auth.verify_id_token(id_token)
        return decoded
    except Exception:
        st.error("❌ Invalid or expired token.")
        st.stop()

query_params = st.query_params
if "token" in query_params and "user" not in st.session_state:
    id_token = query_params["token"]
    user = verify_token(id_token)
    st.session_state["user"] = user
    st.session_state["token"] = id_token

if "user" not in st.session_state:
    st.warning("Please log in to use Resume Ranker.")
    st.markdown("[Login with Google](https://resume-ranker-auth.web.app/)")
    st.stop()

# --------------- SIDEBAR ---------------- #
st.sidebar.success(f"✅ Logged in as {st.session_state['user']['email']}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# --------------- MAIN CONTENT ---------------- #
load_dotenv()
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.title("📄 Resume Ranker")
st.markdown("Upload your resume and paste the job description to get instant ATS score & AI suggestions.")

resume_file = st.file_uploader("📄 Upload Your Resume (PDF)", type=["pdf"])
job_desc_input = st.text_area("🧾 Paste Job Description", height=200)

def generate_pdf_bytes(text: str, title: str = "Optimized Resume") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Helvetica"
    normal.fontSize = 11
    normal.leading = 14

    title_style = ParagraphStyle("title", parent=styles["Heading1"], alignment=0, fontSize=16, leading=20, spaceAfter=6)
    story = []
    # Title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 6))

    # Split the text into paragraphs for PDF
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        # Replace plain newlines inside paragraphs with <br/> to keep formatting
        safe_para = para.replace("\n", "<br/>")
        story.append(Paragraph(safe_para, normal))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# Inside your analyzer UI (after parsing resume_text and job_desc_input)
if st.button("🔍 Analyze Resume"):
    if not resume_file or not job_desc_input:
        st.warning("Please upload a resume and paste the job description.")
    else:
        with st.spinner("Analyzing..."):
            try:
                # Extract resume text from PDF
                pdf_doc = fitz.open(stream=resume_file.read(), filetype="pdf")
                resume_text = ""
                for page in pdf_doc:
                    resume_text += page.get_text()

                # Existing matcher (if present)
                try:
                    matched, missing, score = calculate_match_score(resume_text, job_desc_input)
                    st.markdown(f"### ✅ Match Score: **{score}%**")
                    # display tags
                    if matched:
                        st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                        for w in matched[:60]:
                            st.markdown(f"<span class='tag-match'>{w}</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    if missing:
                        st.markdown("<div style='margin-top:12px;'>", unsafe_allow_html=True)
                        for w in missing[:60]:
                            st.markdown(f"<span class='tag-miss'>{w}</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                except Exception:
                    st.info("Matcher unavailable (placeholder).")

                # AI suggestions (existing)
                suggestions = None
                try:
                    suggestions = get_suggestions(resume_text.strip(), job_desc_input.strip())
                    if suggestions:
                        st.markdown("### 🤖 AI Suggestions")
                        st.markdown(f"<div style='background:#f8fafc;padding:12px;border-radius:8px'>{suggestions}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.info("AI suggester not available (placeholder).")

                # ---------------- Auto-Optimize (FREE for now) ----------------
                st.markdown("---")
                st.markdown("### 🔄 Auto-Optimize Resume (Free)")
                st.markdown("Click the button below to let AI rewrite and optimize your resume content according to the job description. You will get a downloadable PDF.")

                if st.button("Auto-Optimize Resume (Free)"):
                    with st.spinner("Generating optimized resume..."):
                        try:
                            # Get optimized text from your AI suggester
                            # NOTE: we are using the same get_suggestions function — if your suggester returns bullets,
                            # you might want to format it into paragraphs. Adjust as needed.
                            optimized_text = None
                            try:
                                optimized_text = get_suggestions(resume_text.strip(), job_desc_input.strip())
                            except Exception:
                                optimized_text = None

                            # Fallback if suggester not available
                            if not optimized_text or len(optimized_text.strip()) < 20:
                                # Simple fallback: append missing keywords + short suggestions
                                fallback_parts = []
                                if 'missing' in locals() and missing:
                                    fallback_parts.append("Missing keywords to add:\n- " + "\n- ".join(missing[:30]))
                                fallback_parts.append("\nSuggested improvements:\n- Consider adding quantifiable achievements, strong verbs, and keywords from the JD.")
                                optimized_text = "\n\n".join([resume_text, "\n\n---\n\nAI Suggestions:\n\n" + "\n".join(fallback_parts)])

                            # Build a neat PDF using the optimized text
                            pdf_bytes = generate_pdf_bytes(optimized_text, title="Optimized Resume - Resume Ranker")

                            # Provide a download button
                            st.success("✅ Optimized resume generated.")
                            st.download_button(
                                label="📥 Download Optimized Resume (PDF)",
                                data=pdf_bytes,
                                file_name="optimized_resume.pdf",
                                mime="application/pdf",
                            )
                        except Exception as err:
                            st.error(f"Failed to generate optimized resume: {err}")

            except Exception as e:
                st.error(f"Something went wrong while processing the file: {e}")

if st.button("🔍 Analyze Resume"):
    if not resume_file or not job_desc_input.strip():
        st.warning("Please upload a resume and enter a job description.")
    else:
        with st.spinner("Processing..."):
            try:
                # Extract text from PDF
                pdf_doc = fitz.open(stream=resume_file.read(), filetype="pdf")
                resume_text = "".join([page.get_text() for page in pdf_doc])

                # Keyword Match
                matched, missing, score = calculate_match_score(resume_text, job_desc_input)
                st.markdown(f"### ✅ Match Score: **{score}%**")

                # Display Matched & Missing Keywords
                matched_html = "".join([f"<span class='keyword-chip matched'>{word}</span>" for word in matched])
                missing_html = "".join([f"<span class='keyword-chip missing'>{word}</span>" for word in missing])

                st.markdown("#### ✅ Matched Keywords", unsafe_allow_html=True)
                st.markdown(matched_html, unsafe_allow_html=True)
                st.markdown("#### ❌ Missing Keywords", unsafe_allow_html=True)
                st.markdown(missing_html, unsafe_allow_html=True)

                # AI Suggestions
                st.markdown("### 🤖 AI Suggestions to Improve Your Resume")
                ai_result = get_suggestions(resume_text.strip(), job_desc_input.strip())
                if ai_result:
                    st.markdown(f"<div class='suggest-card'>{ai_result}</div>", unsafe_allow_html=True)
                else:
                    st.info("AI did not return a detailed suggestion.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ by Abhishek | Powered by Streamlit + LLMs")