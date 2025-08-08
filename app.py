import streamlit as st
st.set_page_config(page_title="Resume Ranker", layout="centered")
from ai_suggester import get_suggestions
from matcher import calculate_match_score
from resume_paser import parse_resume
import fitz  # PyMuPDF
from dotenv import load_dotenv
from streamlit_extras.badges import badge
import firebase_admin 
import requests
from firebase_admin import credentials ,auth as admin_auth
import urllib.parse
from urllib.parse import urlparse,parse_qs
from firebase_config import auth
import os

FIREBASE_JSON_PATH = "resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json"

# ✅ Initialize Firebase Admin SDK (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_JSON_PATH)
    firebase_admin.initialize_app(cred)

# ✅ Function to verify token
def verify_token(id_token):
    try:
        decoded = admin_auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        st.error("❌ Invalid or expired token.")
        st.stop()

# ✅ Get token from query params and verify
query_params = st.query_params
if "token" in query_params and "user" not in st.session_state:
    id_token = query_params["token"]
    user = verify_token(id_token)
    st.session_state["user"] = user
    st.session_state["token"] = id_token

# ✅ Check login
if "user" not in st.session_state:
    st.warning("Please log in to use Resume Ranker.")
    st.markdown("[Login with Google](https://resume-ranker-auth.web.app/)")
    st.stop()

# ✅ Logged in
st.sidebar.success(f"✅ Logged in as {st.session_state['user']['email']}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()


load_dotenv()
st.markdown("""
<style>
/* Background */
.main {
    background-color: #f9fafc;
    font-family: 'Inter', sans-serif;
}

/* Title */
h1, h2, h3, h4 {
    font-weight: 600;
    color: #1a1a1a;
}

/* Text Area */
textarea {
    background-color: #ffffff !important;
    color: #333333 !important;
    border: 2px solid #d1d5db !important;
    border-radius: 12px !important;
    padding: 15px !important;
    font-size: 15px !important;
}

/* File uploader */
.stFileUploader {
    border: 2px dashed #4f46e5 !important;
    background-color: #f5f3ff !important;
    border-radius: 15px !important;
}

/* Buttons */
.stButton > button {
    background-color: #4f46e5 !important;
    color: white !important;
    font-size: 16px !important;
    padding: 10px 25px !important;
    border-radius: 10px !important;
    border: none !important;
    transition: all 0.3s ease-in-out;
}

.stButton > button:hover {
    background-color: #4338ca !important;
}

/* Keyword tags */
span {
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)


st.title("📄 Resume Ranker with AI")
st.markdown("Upload your resume and paste the job description to get feedback.")

# Upload resume
resume_file = st.file_uploader("📄 Upload Your Resume (PDF)", type=["pdf"])

# Job description input
job_desc_input = st.text_area("🧾 Paste Job Description", height=200)

# Analyze button
if st.button("🔍 Analyze Resume"):
    if not resume_file or not job_desc_input:
        st.warning("Please upload a resume and enter a job description.")
    else:
        with st.spinner("Processing..."):
            try:
                # Extract text from PDF
                pdf_doc = fitz.open(stream=resume_file.read(), filetype="pdf")
                resume_text = ""
                for page in pdf_doc:
                    resume_text += page.get_text()

                # Keyword Match
                matched, missing, score = calculate_match_score(resume_text, job_desc_input)
                st.markdown(f"### ✅ Match Score: **{score}%**")

                def tagify(words,color):
                    return " ".join([f"<span style='background-color:{color}; padding:3px 8px; border-radius:8px; color:white; margin:2px; display:inline-block;'>{word}</span>" for word in words])
                st.markdown("#### ✅ Matched Keywords")
                st.markdown(tagify(matched,"#28a745"), unsafe_allow_html=True)

                st.markdown("#### ❌ Missing Keywords")
                st.markdown(tagify(missing,"#dc3545"),unsafe_allow_html=True)

                # AI Suggestions
                st.markdown("### 🤖 AI Suggestions to Improve Your Resume")
                result = get_suggestions(resume_text.strip(), job_desc_input.strip())
            

                if result:
                    sections=result.split("\n")
                    for line in sections:
                        line=line.strip()
                        if line.lower().startswith("score"):
                            st.markdown(f"#### {line}")
                        elif "strength" in line.lower():
                            st.markdown(f"#### {line}")
                        elif "suggestions" in line.lower():
                            st.markdown(f"#### {line}")
                        else:
                            st.markdown(line)
                
                else:
                    st.info("AI did not return a detailed suggestion.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit + Groq + LLMs by Abhishek")
