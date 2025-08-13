import os
import requests
from dotenv import load_dotenv
from matcher import calculate_match_score

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama3-8b-8192"
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

# ------------------- AI Suggestions ------------------- #
def get_suggestions(resume_text, job_description):
    """Get AI feedback on resume vs job description."""
    try:
        if not API_KEY:
            return "❌ Error: GROQ_API_KEY not found in environment."

        prompt = f"""
You are a helpful AI assistant reviewing a resume for a job application.
Evaluate the resume against the job description and provide actionable suggestions.

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

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a helpful resume evaluator."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        resp = requests.post(BASE_URL, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }, json=payload).json()

        if "error" in resp:
            return f"❌ API Error: {resp['error'].get('message', 'Unknown error')}"

        if "choices" not in resp or not resp["choices"]:
            return "❌ No response from AI model."

        return resp["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"❌ AI Suggestion Failed: {str(e)}"

# ------------------- Resume Optimization ------------------- #
def optimize_resume_for_role(parsed_resume, job_desc, target_score=90, max_rounds=3):
    """
    Take parsed_resume dict and optimize for the given job description.
    Returns updated dict ready for template filling.
    """
    current_resume_text = build_resume_text(parsed_resume)

    # Initial missing keywords check
    _, missing_keywords, score = calculate_match_score(current_resume_text, job_desc)

    for round_num in range(1, max_rounds + 1):
        prompt = f"""
You are an expert ATS resume writer.
Transform the following resume for the given job description.

Job Description:
{job_desc}

Guidelines:
- Remove irrelevant skills/experience.
- Add missing keywords naturally: {', '.join(missing_keywords)}.
- Keep truthful (no fake experience).
- Maintain sections: Summary, Skills, Experience, Education, Projects.
- Target ATS score: {target_score}+.
- Preserve professional tone and formatting.

Original Resume:
{current_resume_text}
"""

        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }

        resp = requests.post(BASE_URL, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }, json=payload).json()

        if "error" in resp:
            print(f"API Error: {resp['error'].get('message', 'Unknown error')}")
            break

        if "choices" not in resp or not resp["choices"]:
            print("No AI response received.")
            break

        rewritten_resume = resp["choices"][0]["message"]["content"].strip()
        _, missing_after, score = calculate_match_score(rewritten_resume, job_desc)

        current_resume_text = rewritten_resume
        missing_keywords = missing_after

        if score >= target_score:
            break

    # Convert rewritten resume back into structured dict
    optimized_data = parse_rewritten_resume(rewritten_resume, parsed_resume)
    return optimized_data

# ------------------- Helper Functions ------------------- #
def build_resume_text(data):
    """Convert structured resume dict into plain text for AI."""
    text = f"{data.get('name', '')}\n{data.get('contact', '')}\n\n"
    text += f"Summary:\n{data.get('summary', '')}\n\n"
    text += "Skills:\n" + ", ".join(data.get('skills', [])) + "\n\n"

    if data.get("experience"):
        text += "Experience:\n"
        for exp in data["experience"]:
            text += f"- {exp}\n"

    if data.get("projects"):
        text += "\nProjects:\n"
        for proj in data["projects"]:
            text += f"- {proj}\n"

    text += f"\nEducation:\n{data.get('education', '')}\n"
    if data.get("certifications"):
        text += "\nCertifications:\n" + ", ".join(data["certifications"]) + "\n"

    return text

def parse_rewritten_resume(text, original_data):
    """
    Convert AI rewritten plain text back into dict for template_filler.
    If AI fails to structure data, fallback to original sections.
    """
    optimized = original_data.copy()

    # Simple skill extraction (line starting with Skills)
    for line in text.splitlines():
        if "skill" in line.lower():
            skills_part = line.split(":")[-1]
            optimized["skills"] = [s.strip() for s in skills_part.split(",") if s.strip()]

    # Summary extraction
    if "summary" in text.lower():
        summary_idx = text.lower().index("summary")
        optimized["summary"] = text[summary_idx:].split("\n", 1)[-1].strip()

    # Experience extraction (skip if fresher)
    if original_data.get("experience"):
        exp_lines = []
        if "experience" in text.lower():
            exp_idx = text.lower().index("experience")
            exp_lines = text[exp_idx:].split("\n")
            exp_lines = [l.strip("- ").strip() for l in exp_lines if l.strip()]
        optimized["experience"] = exp_lines

    # Projects extraction
    if "projects" in text.lower():
        proj_idx = text.lower().index("projects")
        proj_lines = text[proj_idx:].split("\n")
        proj_lines = [l.strip("- ").strip() for l in proj_lines if l.strip()]
        optimized["projects"] = proj_lines

    return optimized
