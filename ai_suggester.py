import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # Load .env file (for local dev)

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
