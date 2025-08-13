import os
import json
import requests
from dotenv import load_dotenv
from matcher import calculate_match_score

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama3-8b-8192"
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_suggestions(resume_text, job_description):
    try:
        prompt = f"""
You are an expert ATS resume reviewer.
Evaluate the resume against the job description and give a short analysis.

Resume:
{resume_text}

Job Description:
{job_description}

Give your feedback in the following format (plain text only):
✅ Match Score (out of 10)
⭐ Strengths
🛠️ Areas to Improve
📢 Overall Suggestion
"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        resp = requests.post(BASE_URL, headers=headers, json=payload).json()
        return resp["choices"][0]["message"]["content"]

    except Exception as e:
        return f"❌ AI Suggestion Failed: {str(e)}"


def rewrite_resume_for_role(resume_text, job_desc, missing_keywords, target_score=90, max_rounds=2):
    """
    Rewrite the resume in a structured JSON format.
    Always preserve original structure & sections from the source resume.
    Only modify skills & descriptions relevant to the job.
    """

    prompt = f"""
You are an ATS-optimized resume rewriting AI.
You will rewrite the given resume for the provided job description.

RULES:
1. Preserve all existing sections (do NOT remove any section).
2. Maintain factual correctness (do not invent experiences).
3. Only modify the following:
   - Skills: tailor them to match the job description & missing keywords.
   - Summary: slightly adjust to highlight job-specific expertise.
   - Experience: tweak bullet points to include missing keywords naturally.
4. Keep Education, Projects, Certifications as in original unless there are obvious grammatical fixes.
5. DO NOT skip any section. If no content, return an empty string or empty list.
6. Output must be STRICTLY in this JSON format:

{{
    "name": "",
    "contact": "",
    "summary": "",
    "skills": [],
    "experience": [
        {{ "role": "", "company": "", "duration": "", "details": [] }}
    ],
    "projects": [
        {{ "name": "", "tech": "", "details": [] }}
    ],
    "education": [],
    "certifications": []
}}

Here is the data to work with:

--- RESUME TEXT ---
{resume_text}

--- JOB DESCRIPTION ---
{job_desc}

--- MISSING KEYWORDS ---
{', '.join(missing_keywords)}
"""

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    resp = requests.post(BASE_URL, headers=headers, json=payload).json()

    try:
        json_data = json.loads(resp["choices"][0]["message"]["content"])
    except json.JSONDecodeError:
        raise ValueError("AI did not return valid JSON. Full response:\n" + str(resp))

    return json_data
