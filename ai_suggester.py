import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

def get_suggestions(resume_text: str, job_description: str) -> str:
    client = Groq(api_key=groq_api_key)

    system_message = (
        "You are a strict and concise resume evaluation AI. "
        "Do not ask for the resume or job description again. "
        "Only respond with score, strengths, and improvement suggestions."
    )

    prompt = f"""
Compare the following resume and job description and return:

1. **Score:** x/10  
2. **Strengths:** (2-3 lines)  
3. **Suggestions:** (3-5 bullet points to improve)

Resume:
{resume_text}

Job Description:
{job_description}
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()
