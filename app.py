import streamlit as st
from ai_suggester import get_suggestions  # Keep suggestions from old logic
from ai_suggester import optimize_resume_for_role  # New role-specific rewriting
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
from cleaner import extract_text_from_pdf, clean_resume_text
from gap_analysis import analyze_role_gap
from formatter import generate_docx_from_text
from template_filler import build_template_resume


# --------------- CONFIG & THEME ---------------- #
st.set_page_config(page_title="Resume Ranker", layout="centered", page_icon="📄")
st.markdown(
    """
    <style>
    @media (max-width: 600px) {
        .block-container {
            padding-left: 10px;
            padding-right: 10px;
        }
        textarea, input {
            font-size: 14px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Custom CSS (unchanged)
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

if resume_file and job_desc_input.strip():
    # Read raw PDF bytes
    raw_bytes = resume_file.read()

    # Extract raw text from PDF
    resume_text = extract_text_from_pdf(raw_bytes)

    # Parse into structured dict
    parsed_resume = parse_resume_auto(raw_bytes, getattr(resume_file, "name", "resume.pdf"))

    # Save in session for later steps
    st.session_state.resume_text = resume_text
    st.session_state.parsed_resume = parsed_resume
    st.session_state.job_desc = job_desc_input

    st.success("✅ Resume and Job Description uploaded successfully!")

# -------------------- AI SUGGESTIONS --------------------
if "resume_text" in st.session_state and st.button("🔍 Get AI Suggestions"):
    suggestions = get_suggestions(st.session_state.resume_text, st.session_state.job_desc)
    st.markdown("### 📢 AI Suggestions")
    st.write(suggestions)

    # Show transform button only after suggestions
    st.session_state.show_transform_button = True

# -------------------- TRANSFORM RESUME --------------------
if st.session_state.get("show_transform_button"):
    st.markdown("### 🚀 Do you want to transform your resume into an ATS-optimized template?")

    if st.button("✅ Yes, Transform My Resume"):
        with st.spinner("Optimizing your resume for the given job role..."):
            optimized_data = optimize_resume_for_role(
                st.session_state.parsed_resume,
                st.session_state.job_desc
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
        else:
            st.error("❌ Resume transformation failed. Please try again.")



st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("These are auto-generated AI Resumes and sometimes it may lead to wrong info, so kindly check all the details carefully before applying.")
st.markdown("Built with ❤️ |\u00A9 Resume-Ranker.All rights reserved.")