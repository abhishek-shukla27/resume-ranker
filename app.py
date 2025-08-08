import streamlit as st
import fitz  # PyMuPDF
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth as admin_auth
from matcher import calculate_match_score
from ai_suggester import get_suggestions
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Resume Ranker", page_icon="📄", layout="wide", initial_sidebar_state="collapsed")
load_dotenv()

FIREBASE_JSON_PATH = "resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json"
LOGIN_URL = "https://resume-ranker-auth.web.app/"

# ------------- CSS Styling (Glassmorphism) --------------
glass_css = """
<style>
/* Hide Streamlit default menu and footer */
#MainMenu, header, footer {visibility: hidden;}

/* Background */
.stApp {
    background: linear-gradient(135deg, rgba(240,240,255,1) 0%, rgba(225,245,255,1) 100%);
    background-attachment: fixed;
    font-family: 'Segoe UI', sans-serif;
}

/* Glass card */
.glass-card {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 16px;
    padding: 2rem;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
}

/* Headings */
h1, h2, h3 {
    text-align: center;
    font-weight: 700;
    color: #1e293b;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #4f46e5, #3b82f6);
    color: white;
    padding: 12px 28px;
    font-size: 16px;
    border-radius: 12px;
    border: none;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transition: 0.3s ease;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #4338ca, #2563eb);
}

/* Textarea */
textarea {
    background: rgba(255, 255, 255, 0.25) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.4) !important;
    color: #111827 !important;
    padding: 12px !important;
    font-size: 16px !important;
}

/* Keyword tags */
.keyword-tag {
    display: inline-block;
    padding: 4px 10px;
    margin: 4px;
    border-radius: 8px;
    font-size: 14px;
    color: white;
}

</style>
"""
st.markdown(glass_css, unsafe_allow_html=True)

# ---------------- FIREBASE INIT ----------------
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_JSON_PATH)
    firebase_admin.initialize_app(cred)

def verify_token(id_token):
    try:
        decoded = admin_auth.verify_id_token(id_token)
        return decoded
    except:
        return None

# ---------------- SESSION LOGIN ----------------
query_params = st.query_params
if "token" in query_params and "user" not in st.session_state:
    token = query_params["token"]
    user = verify_token(token)
    if user:
        st.session_state["user"] = user
        st.session_state["token"] = token

# ---------------- LANDING PAGE ----------------
if "user" not in st.session_state:
    st.markdown("<h1>📄 Resume Ranker</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:18px; color:gray;'>AI-powered resume optimization — upload, match, and improve your resume for specific job descriptions.</p>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center;'><a href='{LOGIN_URL}' style='background:linear-gradient(90deg,#4f46e5,#3b82f6);padding:14px 32px;color:white;border-radius:12px;text-decoration:none;font-weight:bold;'>Login with Google</a></div>", unsafe_allow_html=True)
    st.stop()

# ---------------- ANALYZER PAGE ----------------
st.sidebar.success(f"✅ Logged in as {st.session_state['user']['email']}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("<h1>📄 Resume Ranker with AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:18px; color:#334155;'>Upload your resume & paste the job description to get a score and improvement suggestions.</p>", unsafe_allow_html=True)

resume_file = st.file_uploader("📄 Upload Your Resume (PDF)", type=["pdf"])
job_desc_input = st.text_area("🧾 Paste Job Description", height=200, placeholder="Paste the job description here...")

if st.button("🔍 Analyze Resume"):
    if not resume_file or not job_desc_input:
        st.warning("Please upload a resume and enter a job description.")
    else:
        with st.spinner("Processing..."):
            try:
                # Extract resume text
                pdf_doc = fitz.open(stream=resume_file.read(), filetype="pdf")
                resume_text = "".join([page.get_text() for page in pdf_doc])

                matched, missing, score = calculate_match_score(resume_text, job_desc_input)
                st.markdown(f"<h3>✅ Match Score: {score}%</h3>", unsafe_allow_html=True)

                def tagify(words, color):
                    return " ".join([f"<span class='keyword-tag' style='background:{color};'>{word}</span>" for word in words])

                st.markdown("#### ✅ Matched Keywords")
                st.markdown(tagify(matched, "#16a34a"), unsafe_allow_html=True)

                st.markdown("#### ❌ Missing Keywords")
                st.markdown(tagify(missing, "#dc2626"), unsafe_allow_html=True)

                st.markdown("### 🤖 AI Suggestions")
                result = get_suggestions(resume_text.strip(), job_desc_input.strip())
                if result:
                    st.markdown(f"<div style='background:rgba(255,255,255,0.2);padding:15px;border-radius:12px;'>{result}</div>", unsafe_allow_html=True)
                else:
                    st.info("No suggestions returned.")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("</div>", unsafe_allow_html=True)