import os
import requests
from dotenv import load_dotenv
from matcher import calculate_match_score
import json
import requests
from copy import deepcopy
from typing import Any,Dict,List
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
def optimize_resume_for_role(parsed_resume: Dict[str, Any], job_desc: str, target_score: int = 90, max_rounds: int = 2) -> Dict[str, Any]:
    """
    Takes a parsed_resume dict (from your parser) and returns an optimized dict
    ready to feed into template_filler.build_template_resume(data).
    """
    if not API_KEY:
        return _coerce_resume_dict(parsed_resume)

    current_text = _dict_to_plain_text(parsed_resume)
    _, missing_kw, score = calculate_match_score(current_text, job_desc)

    working = deepcopy(parsed_resume)

    for _ in range(max_rounds):
        json_schema = _json_schema_prompt(missing_kw, target_score, job_desc, working, current_text)

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


# ===================== Helpers ===================== #

def _post_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    r = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
    try:
        return r.json()
    except Exception:
        return {"error": {"message": f"Non-JSON response (status {r.status_code})"}}


def _json_schema_prompt(missing_kw: List[str], target_score: int, job_desc: str, working_dict: Dict[str, Any], current_text: str) -> str:
    missing_str = ", ".join(missing_kw) if missing_kw else "none"
    baseline_json = json.dumps(_coerce_resume_dict(working_dict), ensure_ascii=False)

    return f"""
You will transform the resume for the given job description and return STRICT JSON ONLY.
Do NOT include any text outside JSON. Do NOT use markdown or backticks.

RULES:
-Keep truthful,no fake experience.
-Do not remove candidate's real project or education,only reformat.
-Project must always have exactly 3 bullet points: Objective, Tech Stack,Features.
-Summary MUST be EXACTLY 2 sentences in this fixed format:
    "Enthusiastic and highly motivated recent graduate with a [Degree Full Form] from [University Name]. Possess strong foundational knowledge in [key skills relevant to the job description]."
-Replace [Degree Full Form] and [University Name] from actual resume education data.
-Replace [key skills relevant to the job description] with most relevant skills from both resume and job description.
- Education must have only top 2 qualifications (latest first) with degree full form, university/school name, and academic year.
- Insert missing keywords naturally: {missing_str}
- Target ATS score: {target_score}+.
-Return JSON ONLY.No markdown, no text outside JSON.

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
  "summary": "string"string (MUST be exactly 2 sentences in this format: 'Enthusiastic and highly motivated recent graduate with a [Degree Full Form] from [University Name]. Possess strong foundational knowledge in [key skills relevant to the job description].')",
  "skills": ["string"],,
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

RULES:
- Keep truthful, no fake experience.
- Remove irrelevant content.
- If fresher, keep "experience" empty.
- Return ONLY the JSON.
""".strip()


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

    skills = model_out.get("skills")
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    out["skills"] = _ensure_list(skills) or _ensure_list(fallback.get("skills", []))

    out["experience"] = []
    for item in _ensure_list(model_out.get("experience")):
        if isinstance(item, str):
            out["experience"].append({"role": item, "company": "", "duration": "", "details": []})
        elif isinstance(item, dict):
            out["experience"].append({
                "role": _coerce_string(item.get("role"), ""),
                "company": _coerce_string(item.get("company"), ""),
                "duration": _coerce_string(item.get("duration"), ""),
                "details": _ensure_list(item.get("details"))
            })

    out["projects"] = []
    for item in _ensure_list(model_out.get("projects")):
        if isinstance(item, str):
            out["projects"].append({"name": item, "tech": "", "details": []})
        elif isinstance(item, dict):
            out["projects"].append({
                "name": _coerce_string(item.get("name"), ""),
                "tech": _coerce_string(item.get("tech"), ""),
                "details": _ensure_list(item.get("details"))
            })

    out["education"] = model_out.get("education", fallback.get("education", ""))
    certs = model_out.get("certifications")
    if isinstance(certs, str):
        certs = [c.strip() for c in certs.split(",") if c.strip()]
    out["certifications"] = _ensure_list(certs)

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
        elif isinstance(item, str):
            coerced["experience"].append({"role": item, "company": "", "duration": "", "details": []})

    for item in _ensure_list(d.get("projects")):
        if isinstance(item, dict):
            coerced["projects"].append({
                "name": _coerce_string(item.get("name"), ""),
                "tech": _coerce_string(item.get("tech"), ""),
                "details": _ensure_list(item.get("details"))
            })
        elif isinstance(item, str):
            coerced["projects"].append({"name": item, "tech": "", "details": []})

    return coerced


def _dict_to_plain_text(data: Dict[str, Any]) -> str:
    parts = [
        str(data.get("name", "")),
        str(data.get("contact", "")),
    ]

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