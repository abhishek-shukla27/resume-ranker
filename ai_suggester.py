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
DEGREE_MAP = {
    "mca": "Master of Computer Applications",
    "mba": "Master of Business Administration",
    "bba": "Bachelor of Business Administration",
    "bpharma": "Bachelor of Pharmacy",
    "b.pharma": "Bachelor of Pharmacy",
    "ballb": "Bachelor of Arts + Bachelor of Laws",
    "b.tech": "Bachelor of Technology",
    "btech": "Bachelor of Technology",
    "mtech": "Master of Technology",
    "msc": "Master of Science",
    "bsc": "Bachelor of Science",
    "llb": "Bachelor of Laws",
    "ba": "Bachelor of Arts",
    "ma": "Master of Arts",
    "phd": "Doctor of Philosophy"
}

def detect_degree_and_university(education_field: Any) -> (str, str):
    if not education_field:
        return "", ""

    text = ""
    if isinstance(education_field, list):
        text = " ".join(map(str, education_field))
    elif isinstance(education_field, str):
        text = education_field

    text_lower = text.lower()
    detected_degree = ""
    for short, full in DEGREE_MAP.items():
        if short in text_lower:
            detected_degree = full
            break

    uni_match = re.search(r"(?:University|College|Institute|School)[^\n,]*", text, re.IGNORECASE)
    university_name = uni_match.group(0).strip() if uni_match else ""

    return detected_degree, university_name


# ------------------- MAIN OPTIMIZER ------------------- #
def optimize_resume_for_role(parsed_resume: Dict[str, Any], job_desc: str,
                             target_score: int = 90, max_rounds: int = 2) -> Dict[str, Any]:
    if not API_KEY:
        return _coerce_resume_dict(parsed_resume)

    degree_full_form, university_name = detect_degree_and_university(parsed_resume.get("education"))

    current_text = _dict_to_plain_text(parsed_resume)
    _, missing_kw, score = calculate_match_score(current_text, job_desc)
    working = deepcopy(parsed_resume)

    for _ in range(max_rounds):
        json_schema = _json_schema_prompt(
            missing_kw, target_score, job_desc,
            working, current_text,
            degree_full_form, university_name
        )

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are an expert ATS resume writer. Return ONLY valid JSON matching schema exactly."},
                {"role": "user", "content": json_schema}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = _post_json(payload)
            if "choices" not in resp:
                break

            raw = resp["choices"][0]["message"]["content"]
            model_out = _safe_json_loads(_extract_json(raw))

            if not isinstance(model_out, dict):
                break

            optimized = _normalize_model_output(model_out, fallback=working)
            new_text = _dict_to_plain_text(optimized)
            _, missing_kw, score = calculate_match_score(new_text, job_desc)
            working = optimized
            current_text = new_text

            if score >= target_score:
                break

        except Exception:
            break

    return _coerce_resume_dict(working)


# ------------------- PROMPT BUILDER ------------------- #
def _json_schema_prompt(missing_kw: List[str], target_score: int, job_desc: str,
                        working_dict: Dict[str, Any], current_text: str,
                        degree_full_form: str, university_name: str) -> str:
    missing_str = ", ".join(missing_kw) if missing_kw else "none"
    baseline_json = json.dumps(_coerce_resume_dict(working_dict), ensure_ascii=False)

    return f"""
You will transform the resume for the given job description and return STRICT JSON ONLY.

RULES:
- Keep truthful, no fake experience.
- Do not remove candidate's real projects or education, only reformat & enhance for ATS.
- If degree is detected as "{degree_full_form}", KEEP IT UNCHANGED.
- Summary MUST be EXACTLY 2 sentences:
  "Enthusiastic and highly motivated professional with a {degree_full_form} from {university_name}. Possess strong foundational knowledge in [two most relevant skills from both resume and job description]."
- Skills list must merge relevant skills from resume and JD, remove unrelated ones.
- Each project must have:
  1. Name (UPPERCASE) — If missing, use original parsed name.
  2. Objective
  3. Tech Stack
  4. Features
- Education must have only top 2 qualifications (latest first) with degree full form, university name, and academic year.
- Insert missing keywords naturally: {missing_str}
- Target ATS score: {target_score}+
- Output ONLY JSON.

INPUTS:
Job Description:
{job_desc}

Current Resume (structured):
{baseline_json}

Current Resume (plain text):
{current_text}

OUTPUT SCHEMA:
{{
  "name": "string",
  "contact": "string",
  "summary": "string",
  "skills": ["string"],
  "experience": [
    {{
      "role": "string",
      "company": "string",
      "duration": "string",
      "details": ["string"]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "tech": "string",
      "details": ["string"]
    }}
  ],
  "education": "string or list",
  "certifications": ["string"]
}}
"""


# ------------------- UTIL FUNCS ------------------- #
def _post_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    r = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    try:
        return r.json()
    except Exception:
        return {"error": {"message": f"Non-JSON response (status {r.status_code})"}}


def _extract_json(s: str) -> str:
    first, last = s.find("{"), s.rfind("}")
    return s[first:last+1] if first != -1 and last != -1 else s


def _safe_json_loads(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None


def _ensure_list(x) -> List[Any]:
    if isinstance(x, list):
        return x
    return [x] if x else []


def _coerce_string(val: Any, default: str = "") -> str:
    return str(val).strip() if val else default


def _clean_bullet_text(text: str) -> str:
    return re.sub(r'^[\s•\-\u2022]+', '', str(text)).strip()


def _normalize_model_output(model_out: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "name": _coerce_string(model_out.get("name"), fallback.get("name", "")),
        "contact": _coerce_string(model_out.get("contact"), fallback.get("contact", "")),
        "summary": _coerce_string(model_out.get("summary"), fallback.get("summary", "")),
        "skills": _ensure_list(model_out.get("skills")) or _ensure_list(fallback.get("skills", [])),
        "experience": [],
        "projects": [],
        "education": model_out.get("education", fallback.get("education", "")),
        "certifications": _ensure_list(model_out.get("certifications"))
    }

    for item in _ensure_list(model_out.get("experience")):
        out["experience"].append({
            "role": _coerce_string(item.get("role")),
            "company": _coerce_string(item.get("company")),
            "duration": _coerce_string(item.get("duration")),
            "details": [_clean_bullet_text(d) for d in _ensure_list(item.get("details"))]
        })

    for idx, item in enumerate(_ensure_list(model_out.get("projects"))):
        proj_name = _coerce_string(item.get("name"))
        if not proj_name and idx < len(_ensure_list(fallback.get("projects"))):
            proj_name = _coerce_string(fallback["projects"][idx].get("name"))
        out["projects"].append({
            "name": proj_name,
            "tech": _coerce_string(item.get("tech")),
            "details": _ensure_list(item.get("details"))
        })

    return out


def _coerce_resume_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    coerced = {
        "name": _coerce_string(d.get("name")),
        "contact": _coerce_string(d.get("contact")),
        "summary": _coerce_string(d.get("summary")),
        "skills": _ensure_list(d.get("skills")),
        "experience": [],
        "projects": [],
        "education": d.get("education", ""),
        "certifications": _ensure_list(d.get("certifications"))
    }

    for item in _ensure_list(d.get("experience")):
        coerced["experience"].append({
            "role": _coerce_string(item.get("role")),
            "company": _coerce_string(item.get("company")),
            "duration": _coerce_string(item.get("duration")),
            "details": _ensure_list(item.get("details"))
        })

    for item in _ensure_list(d.get("projects")):
        coerced["projects"].append({
            "name": _coerce_string(item.get("name")),
            "tech": _coerce_string(item.get("tech")),
            "details": _ensure_list(item.get("details"))
        })

    return coerced


def _dict_to_plain_text(data: Dict[str, Any]) -> str:
    parts = [str(data.get("name", "")), str(data.get("contact", ""))]
    if data.get("summary"):
        parts.append("\nSummary:")
        parts.append(str(data["summary"]))
    if data.get("skills"):
        parts.append("\nSkills:")
        parts.append(", ".join(map(str, data["skills"])))
    if data.get("experience"):
        parts.append("\nExperience:")
        for exp in data["experience"]:
            parts.append(f"{exp.get('role')} @ {exp.get('company')} ({exp.get('duration')})")
            for b in _ensure_list(exp.get("details")):
                parts.append(f"- {b}")
    if data.get("projects"):
        parts.append("\nProjects:")
        for pr in data["projects"]:
            parts.append(f"{pr.get('name')} — {pr.get('tech')}")
            for b in _ensure_list(pr.get("details")):
                parts.append(str(b))
    if data.get("education"):
        parts.append("\nEducation:")
        if isinstance(data["education"], list):
            parts.extend(map(str, data["education"]))
        else:
            parts.append(str(data["education"]))
    if data.get("certifications"):
        parts.append("\nCertifications:")
        parts.append(", ".join(map(str, data["certifications"])))
    return "\n".join([p for p in parts if str(p).strip()])