import streamlit as st
from ai_suggester import get_suggestions, rewrite_resume_for_job
from matcher import calculate_match_score
import fitz  # PyMuPDF
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth as admin_auth
from resume_paser import parse_resume_auto
from jd_analyzer import extract_jd_keywords, format_keyword_prompt
import os
import tempfile
from io import BytesIO
from pdf2docx import Converter
from docx import Document

# --------------- CONFIG & THEME ---------------- #
st.set_page_config(page_title="Resume Ranker", layout="centered", page_icon="📄")

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

if st.button("🔍 Analyze Resume"):
    if not resume_file or not job_desc_input.strip():
        st.warning("Please upload a resume and enter a job description.")
    else:
        with st.spinner("Processing..."):
            try:
                # ✅ Read file once & save temp PDF
                raw_bytes = resume_file.read()
                resume_file.seek(0)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(resume_file.read())
                    uploaded_path = tmp.name

                # Extract text from PDF
                pdf_doc = fitz.open(uploaded_path)
                resume_text = "".join([page.get_text() for page in pdf_doc])

                # Parse resume metadata
                parsed = parse_resume_auto(raw_bytes, getattr(resume_file, "name", "resume.pdf"))
                #st.json(parsed)  # Debug output

                # ✅ Extract JD keywords
                jd_kw = extract_jd_keywords(job_desc_input)
                st.write("Extracted JD keywords:", jd_kw[:30])
                st.write(format_keyword_prompt(jd_kw))

                # Keyword Match - OLD score
                matched, missing, old_score = calculate_match_score(resume_text, job_desc_input)
                st.markdown(f"### 🏁 Original ATS Score: **{old_score}%**")

                # Display keywords
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

                # ✅ AI Rewrite with Missing Keywords
                st.markdown("### ✍️ Updated ATS-Optimized Resume")
                updated_resume = rewrite_resume_for_job(
                    resume_text.strip(),
                    job_desc_input.strip(),
                    missing_keywords=missing
                )
                st.text_area("Updated Resume Preview", value=updated_resume, height=400)

                # New ATS score
                _, _, new_score = calculate_match_score(updated_resume, job_desc_input)
                st.success(f"📈 ATS Score Improved: {old_score}% → {new_score}%")

                # ✅ Preserve formatting: Convert PDF → DOCX → Edit → Save
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as docx_tmp:
                    converter = Converter(uploaded_path)
                    converter.convert(docx_tmp.name, start=0, end=None)
                    converter.close()

                    doc = Document(docx_tmp.name)
                    # Replace paragraphs with updated text (simple version)
                    new_lines = updated_resume.split("\n")
                    idx = 0
                    for p in doc.paragraphs:
                        if idx < len(new_lines) and p.text.strip():
                            p.text = new_lines[idx]
                            idx += 1

                    buffer = BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)

                st.download_button(
                    label="📥 Download Updated Resume (.docx)",
                    data=buffer,
                    file_name="updated_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("Built with ❤️ by Abhishek | Powered by Streamlit + LLMs")