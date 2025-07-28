import streamlit as st
from resume_paser import parse_resume
from jd_parser import parse_jd
from matcher import calculate_match_score

st.set_page_config(page_title="AI RESUME RANKER",layout="centered")
st.title("Resume Ranker AI")
st.write("Upload your Resume and Job Description to see how well you match!")

resume_file=st.file_uploader("Upload your resume(PDF)",type=["pdf"])
job_desc_input=st.text_area("Paste the job Description here",height=250)

if st.button("Analyze") and resume_file and job_desc_input:
    with st.spinner("Analyzing resume...."):
        resume_text=parse_resume(resume_file)
        jd_keywords=parse_jd(job_desc_input)
        score,matched,missing=calculate_match_score(resume_text,jd_keywords)

        st.success(f"Match Score:{score}%")
        st.markdown(f"** Matched Keywords:** {','.join(matched)}")
        st.markdown(f"** Missing Keywords:**{','.join(missing)}")


elif st.button("Analyze"):
    st.warning("Please upload a resume and paste a job description")