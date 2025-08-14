import os
import re
import json
import requests
from copy import deepcopy
from typing import Dict, Any, List
from matcher import calculate_match_score

API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama3-8b-8192"
BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


# ===================== DEGREE & UNIVERSITY EXTRACTION ===================== #
def extract_degree_and_university(education_field):
    """Extracts degree, university, and year from education field (string/list)."""
    if isinstance(education_field, list):
        edu_text = " | ".join(str(e) for e in education_field)
    else:
        edu_text = str(education_field)

    # Degree detection patterns
    degree_patterns = [
        r"(Master(?:s)?\s+of\s+[A-Za-z\s]+)",
        r"(Bachelor(?:s)?\s+of\s+[A-Za-z\s]+)",
        r"(B\.Tech|BTech|MCA|MBA|B\.Sc|BSc|M\.Sc|MSc)"
    ]

    degree_full_form = ""
    for pat in degree_patterns:
        match = re.search(pat, edu_text, re.IGNORECASE)
        if match:
            degree_full_form = match.group(1).strip()
            break

    # University name
    university_name = ""
    uni_match = re.search(r"from\s+([A-Za-z\s]+(?:University|College|Institute|School))", edu_text, re.IGNORECASE)
    if not uni_match:
        uni_match = re.search(r"-\s*([A-Za-z\s]+(?:University|College|Institute|School))", edu_text, re.IGNORECASE)
    if uni_match:
        university_name = uni_match.group(1).strip()

    # Academic year
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", edu_text)
    academic_year = year_match.group(1) if year_match else ""

    if not degree_full_form:
        degree_full_form = "[Degree]"
    if not university_name:
        university_name = "[University Name]"

    return degree_full_form, university_name, academic_year


# ===================== MAIN OPTIMIZER ===================== #
def optimize_resume_for_role(parsed_resume: Dict[str, Any], job_desc: str, target_score: int = 90, max_rounds: int = 2) -> Dict[str, Any]:
    if not API_KEY:
        return _coerce_resume_dict(parsed_resume)

    current_text = _dict_to_plain_text(parsed_resume)
    _, missing_kw, score = calculate_match_score(current_text, job_desc)
    working = deepcopy(parsed_resume)

    degree_full_form, university_name, _ = extract_degree_and_university(working.get("education", ""))

    for _ in range(max_rounds):
        json_schema = _json_schema_prompt(
            missing_kw, target_score, job_desc, working, current_text, degree_full_form, university_name
        )

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system",
                 "content": (
                     "You are an expert ATS resume writer. "
                     "Return ONLY valid JSON that matches the requested schema. "
                     "No Markdown, no backticks, no commentary."
                 )},
                {"role": "user", "content": json_schema}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = _post_json(payload)
            if "error" in resp:
                break
            if "choices" not in resp or not resp["choices"]:
                break

            raw = resp["choices"][0]["message"]["content"]
            json_text = _extract_json(raw)
            model_out = _safe_json_loads(json_text)
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


# ===================== PROMPT ===================== #
def _json_schema_prompt(missing_kw: List[str], target_score: int, job_desc: str,
                        working_dict: Dict[str, Any], current_text: str,
                        degree_full_form: str, university_name: str) -> str:
    missing_str = ", ".join(missing_kw) if missing_kw else "none"
    baseline_json = json.dumps(_coerce_resume_dict(working_dict), ensure_ascii=False)

    fixed_summary = (
        f"Enthusiastic and highly motivated recent graduate with a {degree_full_form} from {university_name}. "
        f"Possess strong foundational knowledge in [key skills relevant to the job description]."
    )

    return f"""
You will transform the resume for the given job description and return STRICT JSON ONLY.
Do NOT include any text outside JSON. Do NOT use markdown or backticks.

OBJECTIVE:
- Improve ATS alignment while staying truthful.
- Insert missing keywords naturally: {missing_str}
- Target ATS score: {target_score}+.

SPECIAL RULES:
- Keep truthful, no fake experience.
- Do not remove candidate's real projects or education, only reformat.
- Projects must always have exactly 3 bullet points: Objective, Tech Stack, Features.
- Summary MUST be EXACTLY:
    "{fixed_summary}"
- Education must have only top 2 qualifications (latest first) with degree full form, university/school name, and academic year.

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
""".strip()


# ===================== HELPERS ===================== #
def _post_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    r = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    try:
        return r.json()
    except Exception:
        return {"error": {"message": f"Non-JSON response (status {r.status_code})"}}


def _extract_json(s: str) -> str:
    first = s.find("{")
    last = s.rfind("}")
    if first != -1 and last != -1 and last > first:
        return s[first:last+1]
    return s


def _safe_json_loads(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None


def _ensure_list(x) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _coerce_string(val: Any, default: str = "") -> str:
    return str(val).strip() if val is not None else default


def _normalize_model_output(model_out: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    out["name"] = _coerce_string(model_out.get("name"), fallback.get("name", ""))
    out["contact"] = _coerce_string(model_out.get("contact"), fallback.get("contact", ""))
    out["summary"] = _coerce_string(model_out.get("summary"), fallback.get("summary", ""))
    out["skills"] = _ensure_list(model_out.get("skills")) or _ensure_list(fallback.get("skills", []))

    out["experience"] = []
    for item in _ensure_list(model_out.get("experience")):
        if isinstance(item, dict):
            out["experience"].append({
                "role": _coerce_string(item.get("role"), ""),
                "company": _coerce_string(item.get("company"), ""),
                "duration": _coerce_string(item.get("duration"), ""),
                "details": _ensure_list(item.get("details"))
            })

    out["projects"] = []
    for item in _ensure_list(model_out.get("projects")):
        if isinstance(item, dict):
            out["projects"].append({
                "name": _coerce_string(item.get("name"), ""),
                "tech": _coerce_string(item.get("tech"), ""),
                "details": _ensure_list(item.get("details"))
            })

    out["education"] = model_out.get("education", fallback.get("education", ""))
    out["certifications"] = _ensure_list(model_out.get("certifications"))

    return out


def _coerce_resume_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    coerced = {
        "name": _coerce_string(d.get("name"), ""),
        "contact": _coerce_string(d.get("contact"), ""),
        "summary": _coerce_string(d.get("summary"), ""),
        "skills": _ensure_list(d.get("skills")),
        "experience": [],
        "projects": [],
        "education": d.get("education", ""),
        "certifications": _ensure_list(d.get("certifications"))
    }

    for item in _ensure_list(d.get("experience")):
        if isinstance(item, dict):
            coerced["experience"].append({
                "role": _coerce_string(item.get("role"), ""),
                "company": _coerce_string(item.get("company"), ""),
                "duration": _coerce_string(item.get("duration"), ""),
                "details": _ensure_list(item.get("details"))
            })

    for item in _ensure_list(d.get("projects")):
        if isinstance(item, dict):
            coerced["projects"].append({
                "name": _coerce_string(item.get("name"), ""),
                "tech": _coerce_string(item.get("tech"), ""),
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
        parts.append(", ".join([str(s) for s in data["skills"]]))
    if data.get("experience"):
        parts.append("\nExperience:")
        for exp in data["experience"]:
            line = f"{exp.get('role','')} @ {exp.get('company','')} ({exp.get('duration','')})"
            parts.append(line)
            for b in _ensure_list(exp.get("details")):
                parts.append(f"- {b}")
    if data.get("projects"):
        parts.append("\nProjects:")
        for pr in data["projects"]:
            line = f"{pr.get('name','')} — {pr.get('tech','')}"
            parts.append(line)
            for b in _ensure_list(pr.get("details")):
                parts.append(f"- {b}")
    if data.get("education"):
        parts.append("\nEducation:")
        if isinstance(data["education"], list):
            parts.extend([str(e) for e in data["education"]])
        else:
            parts.append(str(data["education"]))
    if data.get("certifications"):
        parts.append("\nCertifications:")
        parts.append(", ".join([str(c) for c in _ensure_list(data["certifications"])]))
    return "\n".join([p for p in parts if str(p).strip()])
