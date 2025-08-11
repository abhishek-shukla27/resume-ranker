import os
from groq import Groq
from dotenv import load_dotenv
import requests

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

def rewrite_resume_for_job(resume_text, job_desc, missing_keywords=None, target_score=90, max_rounds=3):
    if missing_keywords is None:
        missing_keywords = []

    current_resume = resume_text
    last_score = 0

    for round_num in range(1, max_rounds + 1):
        prompt = f"""
You are an expert ATS resume writer.
Rewrite the provided resume so that:
- ATS score ≥ {target_score} for the given job description
- Keep original order, headings, and layout as much as possible
- Add these missing keywords naturally without stuffing: {", ".join(missing_keywords)}
- Improve bullet points for clarity and impact
- Do NOT invent or add false experience or skills
- Keep professional tone and consistent formatting
- Return ONLY the rewritten resume in plain text (no markdown, no extra commentary)

---
Job Description:
{job_desc}

---
Original Resume:
{current_resume}

---
Updated Resume:
"""
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }

        try:
            response = requests.post(BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            rewritten_resume = data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"❌ Resume Rewrite Failed: {e}"

        # Score new resume
        from matcher import calculate_match_score
        matched, missing, score = calculate_match_score(rewritten_resume, job_desc)

        if score >= target_score:
            return rewritten_resume  # Done

        # Prepare for next round
        current_resume = rewritten_resume
        missing_keywords = missing
        last_score = score

    return current_resume
