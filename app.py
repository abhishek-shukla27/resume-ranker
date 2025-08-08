import streamlit as st
import fitz  # PyMuPDF
from ai_suggester import get_suggestions
from matcher import calculate_match_score
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth as admin_auth

# ---- CONFIG ----
st.set_page_config(page_title="Resume Ranker", layout="centered", initial_sidebar_state="collapsed")

# ---- CUSTOM CSS ----
st.markdown("""
    <style>
        /* Hide Streamlit Branding */
        #MainMenu, header, footer {visibility: hidden;}
        .stApp {
            background: linear-gradient(135deg, rgba(255,255,255,0.2), rgba(255,255,255,0.05));
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            min-height: 100vh;
            padding: 2rem;
            color: #1e293b;
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3, h4 {
            color: #1e293b;
            font-weight: 600;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.25);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            margin-bottom: 1.5rem;
        }
        .keyword {
            padding: 6px 12px;
            border-radius: 12px;
            margin: 4px;
            display: inline-block;
            font-size: 0.9rem;
            font-weight: 600;
        }
        .matched { background: #22c55e; color: white; }
        .missing { background: #ef4444; color: white; }
        textarea, .stTextArea textarea {
            background-color: rgba(255,255,255,0.85) !important;
            color: #1e293b !important;
            border-radius: 10px;
            border: 1px solid #d1d5db;
            font-size: 1rem;
        }
        .stButton button {
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            color: white;
            border-radius: 12px;
            padding: 0.6rem 1.2rem;
            font-size: 1rem;
            font-weight: 600;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            transform: scale(1.05);
            background: linear-gradient(135deg, #1d4ed8, #2563eb);
        }
    </style>
""", unsafe_allow_html=True)

# ---- FIREBASE INIT ----
FIREBASE_JSON_PATH = "resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json"
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_JSON_PATH)
    firebase_admin.initialize_app(cred)

def verify_token(id_token):
    try:
        decoded = admin_auth.verify_id_token(id_token)
        return decoded
    except:
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

# Sidebar
st.sidebar.success(f"✅ Logged in as {st.session_state['user']['email']}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

load_dotenv()

# ---- UI ----
st.markdown("<h1 style='text-align:center;'>📄 Resume Ranker</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;font-size:1.1rem;'>Upload your resume, paste the job description, and get AI-powered feedback instantly.</p>", unsafe_allow_html=True)

with st.container():
    with st.form("resume_form"):
        with st.container():
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            resume_file = st.file_uploader("📄 Upload Your Resume (PDF)", type=["pdf"])
            st.markdown("</div>", unsafe_allow_html=True)

        with st.container():
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            job_desc_input = st.text_area("🧾 Paste Job Description", height=180)
            st.markdown("</div>", unsafe_allow_html=True)

        analyze = st.form_submit_button("🔍 Analyze Resume")

if analyze:
    if not resume_file or not job_desc_input:
        st.warning("Please upload a resume and enter a job description.")
    else:
        with st.spinner("Processing..."):
            try:
                # Extract text from PDF
                pdf_doc = fitz.open(stream=resume_file.read(), filetype="pdf")
                resume_text = "".join([page.get_text() for page in pdf_doc])

                matched, missing, score = calculate_match_score(resume_text, job_desc_input)

                st.markdown(f"<div class='glass-card'><h3>✅ Match Score: {score}%</h3></div>", unsafe_allow_html=True)

                # Matched Keywords
                st.markdown("<div class='glass-card'><h4>✅ Matched Keywords</h4>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='keyword matched'>{w}</span>" for w in matched]), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # Missing Keywords
                st.markdown("<div class='glass-card'><h4>❌ Missing Keywords</h4>", unsafe_allow_html=True)
                st.markdown("".join([f"<span class='keyword missing'>{w}</span>" for w in missing]), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # AI Suggestions
                st.markdown("<div class='glass-card'><h4>🤖 AI Suggestions to Improve Your Resume</h4>", unsafe_allow_html=True)
                result = get_suggestions(resume_text.strip(), job_desc_input.strip())
                if result:
                    for line in result.split("\n"):
                        st.markdown(f"- {line.strip()}")
                else:
                    st.info("AI did not return detailed suggestions.")
                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Something went wrong: {e}")

# Footer
st.markdown("<p style='text-align:center;color:gray;font-size:0.9rem;margin-top:2rem;'>Built with ❤️ using Streamlit + Groq + LLMs</p>", unsafe_allow_html=True)
