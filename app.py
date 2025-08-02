import streamlit as st
from ai_suggester import get_suggestions
from matcher import calculate_match_score
from resume_paser import parse_resume
import fitz  # PyMuPDF
from dotenv import load_dotenv
from streamlit_extras.badges import badge
import os

load_dotenv()

st.set_page_config(page_title="Resume Ranker", layout="centered")
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
