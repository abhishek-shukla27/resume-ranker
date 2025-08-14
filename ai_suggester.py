import os
import requests
from dotenv import load_dotenv
from matcher import calculate_match_score
import json
import requests
from copy import deepcopy
from typing import Any,Dict,List
import re
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
def extract_degree_and_university(education_data):
    """
    Extract degree full form and university name from education string or list.
    """
    degree_full_form = "Degree"
    university_name = "University"

    if isinstance(education_data, list):
        edu_text = " ".join([str(e) for e in education_data])
    else:
        edu_text = str(education_data)

    # Degree mapping
    degree_map = {
        "mca": "Masters in Computer Application",
        "master of computer applications": "Masters in Computer Application",
        "mba": "Masters in Business Administration",
        "btech": "Bachelor of Technology",
        "bachelor of technology": "Bachelor of Technology",
        "bsc": "Bachelor of Science",
        "bachelor of science": "Bachelor of Science",
        "bcom": "Bachelor of Commerce",
        "bachelor of commerce": "Bachelor of Commerce"
    }

    for key, full in degree_map.items():
        if re.search(rf"\b{key}\b", edu_text, re.IGNORECASE):
            degree_full_form = full
            break

    # University extraction (simple heuristic)
    uni_match = re.search(r"(University|Institute|College|School)\s?[A-Za-z\s]*", edu_text, re.IGNORECASE)
    if uni_match:
        university_name = uni_match.group(0).strip()

    return degree_full_form, university_name

# ======= Summary Builder =======
def build_summary(education_data, relevant_skills):
    degree, university = extract_degree_and_university(education_data)
    skills_str = ", ".join(relevant_skills[:3])  # only top 3 relevant skills
    return f"Enthusiastic and highly motivated recent graduate with a {degree} from {university}. " \
           f"Possess strong foundational knowledge in {skills_str}."

# ======= Main Optimizer =======
def optimize_resume_for_role(parsed_resume: Dict[str, Any], job_desc: str,
                              target_score: int = 90, max_rounds: int = 1) -> Dict[str, Any]:
    """
    Optimize resume while keeping fixed structure.
    """
    working = deepcopy(parsed_resume)

    # Extract initial match score & missing keywords
    current_text = _dict_to_plain_text(parsed_resume)
    _, missing_kw, _ = calculate_match_score(current_text, job_desc)

    # Build AI prompt for skills optimization
    ai_prompt = f"""
You are an expert ATS resume optimizer.
Given the current skills: {parsed_resume.get('skills', [])}
And job description: {job_desc}
Add missing keywords if relevant: {', '.join(missing_kw)}
Return ONLY a JSON array of optimized skills, no extra text.
"""

    optimized_skills = parsed_resume.get("skills", [])

    if API_KEY:
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "Return only JSON array of skills."},
                    {"role": "user", "content": ai_prompt}
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"}
            }
            resp = _post_json(payload)
            if "choices" in resp:
                raw = resp["choices"][0]["message"]["content"]
                skills_out = json.loads(_extract_json(raw))
                if isinstance(skills_out, list):
                    optimized_skills = skills_out
        except Exception:
            pass

    # Build fixed format summary
    working["summary"] = build_summary(parsed_resume.get("education", ""), optimized_skills)

    # Fix projects format: exactly 3 bullet points
    fixed_projects = []
    for pr in parsed_resume.get("projects", []):
        fixed_projects.append({
            "name": pr.get("name", ""),
            "tech": pr.get("tech", ""),
            "details": [
                f"Objective: {pr.get('objective', 'Describe the main purpose of the project.')}",
                f"Tech Stack: {pr.get('tech', '')}",
                f"Features: {', '.join(pr.get('features', [])) if pr.get('features') else 'List main features here.'}"
            ]
        })
    working["projects"] = fixed_projects

    # Keep only top 2 education entries
    if isinstance(parsed_resume.get("education"), list):
        working["education"] = parsed_resume["education"][:2]
    else:
        working["education"] = parsed_resume.get("education", "")

    # Replace skills with optimized ones
    working["skills"] = optimized_skills

    return _coerce_resume_dict(working)

# ======= Helpers =======
def _post_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    r = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    try:
        return r.json()
    except Exception:
        return {"error": {"message": f"Non-JSON response (status {r.status_code})"}}

def _extract_json(s: str) -> str:
    first = s.find("[")
    last = s.rfind("]")
    if first != -1 and last != -1 and last > first:
        return s[first:last+1]
    return s

def _ensure_list(x) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]

def _coerce_string(val: Any, default: str = "") -> str:
    return str(val).strip() if val is not None else default

def _coerce_resume_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": _coerce_string(d.get("name")),
        "contact": _coerce_string(d.get("contact")),
        "summary": _coerce_string(d.get("summary")),
        "skills": _ensure_list(d.get("skills")),
        "experience": _ensure_list(d.get("experience")),
        "projects": _ensure_list(d.get("projects")),
        "education": d.get("education", ""),
        "certifications": _ensure_list(d.get("certifications"))
    }

def _dict_to_plain_text(data: Dict[str, Any]) -> str:
    parts = [
        str(data.get("name", "")),
        str(data.get("contact", "")),
        f"Summary: {data.get('summary', '')}",
        f"Skills: {', '.join(_ensure_list(data.get('skills')))}"
    ]
    return "\n".join(parts)