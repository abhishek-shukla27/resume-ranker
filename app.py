import streamlit as st
from ai_suggester import get_suggestions, optimize_resume_for_role
from matcher import calculate_match_score
import fitz  # PyMuPDF
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth as admin_auth, firestore
from resume_paser import parse_resume_auto
from jd_analyzer import extract_jd_keywords, format_keyword_prompt
import os
from io import BytesIO
from cleaner import extract_text_from_pdf
from template_filler import build_template_resume

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="Resume Ranker", layout="centered", page_icon="📄")

# --- Hide Streamlit branding + toolbar completely ---
st.markdown("""
    <style>
    #MainMenu, header, footer {visibility: hidden !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# --- Custom Theme (matching landing page) ---
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #0f172a, #1e293b, #0f172a);
        font-family: 'Poppins', sans-serif;
        color: white;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.07);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.15);
    }
    textarea, input, .stTextInput>div>div>input {
        background-color: rgba(255,255,255,0.15) !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
    }
    textarea:focus, .stTextInput>div>div>input:focus {
        border: 1px solid #38bdf8 !important;
        outline: none !important;
    }
    h1,h2,h3,h4 {color: white !important;}
    </style>
""", unsafe_allow_html=True)

# ---------------- FIREBASE AUTH + DB ---------------- #
FIREBASE_JSON_PATH = "resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_JSON_PATH)
    firebase_admin.initialize_app(cred)
db = firestore.client()

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

# ---------------- SIDEBAR ---------------- #
st.sidebar.success(f"✅ Logged in as {st.session_state['user']['email']}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ---------------- MAIN ---------------- #
load_dotenv()
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.title("📄 Resume Ranker")
st.markdown("Upload your resume and paste the job description to get instant ATS score & AI suggestions.")

resume_file = st.file_uploader("📄 Upload Your Resume (PDF)", type=["pdf"])
job_desc_input = st.text_area("🧾 Paste Job Description", height=200)

if resume_file and job_desc_input.strip():
    raw_bytes = resume_file.read()
    resume_text = extract_text_from_pdf(raw_bytes)
    parsed_resume = parse_resume_auto(raw_bytes, getattr(resume_file, "name", "resume.pdf"))
    st.session_state.resume_text = resume_text
    st.session_state.parsed_resume = parsed_resume
    st.session_state.job_desc = job_desc_input
    st.success("✅ Resume and Job Description uploaded successfully!")

# --- AI Suggestions ---
if "resume_text" in st.session_state and st.button("🔍 Get AI Suggestions"):
    
    ats_score,match_score,suggestions = get_suggestions(
        st.session_state.resume_text,
        st.session_state.job_desc
    )
    st.session_state.ats_score=ats_score
    st.session_state.match_score=match_score
    st.session_state.suggestions=suggestions
    st.session_state.show_transform_button = True

if "ats_score" in st.session_state:
    st.markdown("### 📊 Analysis Results")
    st.write(f"**ATS Score:** {st.session_state.ats_score}")
    st.write(f"**Match Score:** {st.session_state.match_score}")

    st.subheader("✅ Strengths")
    for s in st.session_state.suggestions["strengths"]:
        st.write(f"- {s}")

    st.subheader("🛠️ Areas to Improve")
    for s in st.session_state.suggestions["improvements"]:
        st.write(f"- {s}")


# Always show AI suggestions if available
if "suggestions" in st.session_state:
    st.markdown("### 📢 AI Suggestions")
    st.write(st.session_state.suggestions)


# --- Transform Resume ---
if st.session_state.get("show_transform_button"):
    st.markdown("### 🚀 Do you want to transform your resume into an ATS-optimized template?")
    if st.button("✅ Yes, Transform My Resume"):
        with st.spinner("Optimizing your resume for the given job role..."):
            optimized_data = optimize_resume_for_role(
                st.session_state.parsed_resume, st.session_state.job_desc
            )
            buffer = build_template_resume(optimized_data)
        if buffer:
            st.success("Resume transformed successfully!")
            st.download_button(
                label="📥 Download Updated Resume (.docx)",
                data=buffer,
                file_name="updated_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

st.markdown("</div>", unsafe_allow_html=True)

# --- Disclaimer ---
st.markdown("---")
st.markdown("""
<div style='padding:15px; border-radius:10px; background-color:rgba(255,0,0,0.1); border:1px solid #ef4444;'>
⚠️ <b>Important Notice:</b><br>
These resumes are <b>AI-generated</b> and may sometimes contain errors or missing info.<br>
<u>Please verify all details before using for job applications.</u>
</div>
""", unsafe_allow_html=True)

# --- Feedback Form (Saved to Firestore) ---
st.markdown("## 💬 Share Your Feedback")
with st.form("feedback_form", clear_on_submit=True):
    rating = st.radio("How helpful was Resume Ranker?", ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"])
    comments = st.text_area("Any suggestions or issues?", placeholder="Tell us what we can improve...")
    submitted = st.form_submit_button("Submit Feedback")
    if submitted:
        feedback_data = {
            "user": st.session_state["user"]["email"],
            "rating": rating,
            "comments": comments,
        }
        db.collection("feedback").add(feedback_data)
        st.success("✅ Thanks for your feedback! It helps us improve.")

st.markdown("---")
st.markdown("Built with ❤️ | © Resume-Ranker. All rights reserved.")
