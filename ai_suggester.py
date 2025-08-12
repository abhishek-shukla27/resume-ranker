import os
from groq import Groq
from dotenv import load_dotenv
import requests
from matcher import calculate_match_score
load_dotenv()  # Load .env file (for local dev)
API_KEY=os.getenv("GROQ_API_KEY")
MODEL_NAME="llama3-8b-8192"
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
def get_suggestions(resume_text, job_description):
    try:
        # Fetch Groq API key from environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "❌ Error: GROQ_API_KEY not found in environment."

        # Initialize Groq client
        client = Groq(api_key=api_key)

        # Construct the prompt
        prompt = f"""
You are a helpful AI assistant reviewing a resume for a job application. Your job is to evaluate the resume against the job description and provide suggestions.

Resume:
{resume_text}

Job Description:
{job_description}

Give your feedback in the following format:
✅ Match Score (out of 10)
⭐ Strengths
🛠️ Areas to Improve
📢 Overall Suggestion
"""

        # Send to LLM
        response = client.chat.completions.create(
            model="llama3-8b-8192",  # ✅ Use non-deprecated model
            messages=[
                {"role": "system", "content": "You are a helpful resume evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI Suggestion Failed: {str(e)}"

def rewrite_resume_for_role(resume_text, job_desc, missing_keywords, target_score=90, max_rounds=3):
    current_resume = resume_text
    for round_num in range(1, max_rounds+1):
        prompt = f"""
You are an expert ATS resume writer.
Transform the following resume for the given job description.
---
Job Description:
{job_desc}
---
Guidelines:
- Remove irrelevant skills/experience.
- Add missing keywords naturally: {', '.join(missing_keywords)}.
- Keep truthful (no fake experience).
- Maintain sections: Summary, Skills, Experience, Education, Projects.
- Target ATS score: {target_score}+.
- Preserve professional tone and formatting.
---
Original Resume:
{current_resume}
---
Rewritten Resume:
"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }
        resp = requests.post(BASE_URL, headers=headers, json=payload).json()
        rewritten_resume = resp["choices"][0]["message"]["content"].strip()

        _, missing_after, score = calculate_match_score(rewritten_resume, job_desc)
        if score >= target_score:
            return rewritten_resume
        current_resume = rewritten_resume
        missing_keywords = missing_after
    return current_resume