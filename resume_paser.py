
# Robust auto parser for PDF/DOCX uploads -> normalized structured resume dict.

import re
from io import BytesIO
from typing import Dict, Any, List, Tuple

# External libs
import fitz            # PyMuPDF
import docx            # python-docx

# -------- Degree expansion map (extendable) -------- #
DEGREE_MAP = {
    "MCA": "Master of Computer Applications",
    "MBA": "Master of Business Administration",
    "MTECH": "Master of Technology",
    "M.TECH": "Master of Technology",
    "MSC": "Master of Science",
    "M.SC": "Master of Science",
    "BTECH": "Bachelor of Technology",
    "B.TECH": "Bachelor of Technology",
    "BE": "Bachelor of Engineering",
    "B.E.": "Bachelor of Engineering",
    "BCA": "Bachelor of Computer Applications",
    "BSC": "Bachelor of Science",
    "B.SC": "Bachelor of Science",
    "BCOM": "Bachelor of Commerce",
    "B.COM": "Bachelor of Commerce",
    "MCOM": "Master of Commerce",
    "M.COM": "Master of Commerce",
    "BBA": "Bachelor of Business Administration",
    "BPHARMA": "Bachelor of Pharmacy",
    "B.PHARMA": "Bachelor of Pharmacy",
    "BALLB": "Bachelor of Arts and Bachelor of Laws",
    "BA LLB": "Bachelor of Arts and Bachelor of Laws",
    "LLB": "Bachelor of Laws",
}

SECTION_NAMES = {
    "summary": {"SUMMARY", "PROFILE", "OBJECTIVE", "ABOUT", "PROFESSIONAL SUMMARY"},
    "skills": {"SKILLS", "TECHNICAL SKILLS", "TOOLS", "TECH STACK"},
    "experience": {"EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT", "PROFESSIONAL EXPERIENCE"},
    "projects": {"PROJECTS", "ACADEMIC PROJECTS", "PERSONAL PROJECTS"},
    "education": {"EDUCATION", "ACADEMICS", "QUALIFICATION"},
    "certifications": {"CERTIFICATIONS", "COURSES", "LICENSES"},
}

BULLET_PREFIXES = ("•", "-", "–", "—", "*")


# --------------------- Public API --------------------- #
def parse_resume_auto(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Auto-detect PDF/DOCX, parse, and return a normalized resume dict.
    """
    ext = (filename or "").lower()
    text = ""

    try:
        if ext.endswith(".pdf"):
            text = _extract_text_from_pdf_bytes(file_bytes)
        elif ext.endswith(".docx"):
            text = _extract_text_from_docx_bytes(file_bytes)
        else:
            # Try PDF first; if fails, try DOCX; else treat as plain text
            try:
                text = _extract_text_from_pdf_bytes(file_bytes)
            except Exception:
                try:
                    text = _extract_text_from_docx_bytes(file_bytes)
                except Exception:
                    # Fallback plain text (best effort)
                    text = file_bytes.decode(errors="ignore")
    except Exception:
        text = file_bytes.decode(errors="ignore")

    data = _extract_structured(text)
    return _normalize_resume_dict(data)


# ------------------- Low-level extractors ------------------- #
def _extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()
    return text


def _extract_text_from_docx_bytes(file_bytes: bytes) -> str:
    doc = docx.Document(BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)


# ------------------- Heuristic structure parser ------------------- #
def _extract_structured(text: str) -> Dict[str, Any]:
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]  # remove empty

    name = _guess_name(lines)
    contact = _extract_contact(text)

    sections = _split_into_sections(lines)

    summary_text = "\n".join(sections.get("summary", []))
    skills_list = _extract_skills(sections.get("skills", []))
    experience = _extract_experience(sections.get("experience", []))
    projects = _extract_projects(sections.get("projects", []))
    education = _extract_education(sections.get("education", []), full_text=text)
    certs = _extract_certifications(sections.get("certifications", []))

    return {
        "name": name,
        "contact": contact,
        "summary": summary_text.strip(),
        "skills": skills_list,
        "experience": experience,
        "projects": projects,
        "education": education,           # list[dict]: degree, university, year
        "certifications": certs,
    }


def _split_into_sections(lines: List[str]) -> Dict[str, List[str]]:
    """
    Split by detecting uppercase headings. Keep order; collect lines until next heading.
    """
    def is_heading(line: str) -> Tuple[str, bool]:
        up = re.sub(r"[^A-Z ]", "", line.upper()).strip()
        for key, names in SECTION_NAMES.items():
            if up in names:
                return key, True
        return "", False

    sections: Dict[str, List[str]] = {k: [] for k in SECTION_NAMES.keys()}
    current_key = None

    for ln in lines:
        key, is_head = is_heading(ln)
        if is_head:
            current_key = key
            continue
        if current_key:
            sections[current_key].append(ln)

    return sections


# ------------------- Field extractors ------------------- #
def _guess_name(lines: List[str]) -> str:
    """
    Try first non-empty line that doesn't look like contact.
    """
    for ln in lines[:5]:
        if _looks_like_contact(ln):
            continue
        # Heuristic: names often short, words start capital
        if 2 <= len(ln.split()) <= 5:
            return ln
    return lines[0] if lines else ""


def _looks_like_contact(s: str) -> bool:
    return bool(re.search(r"@|(\+?\d[\d\s\-]{8,}\d)", s))


def _extract_contact(text: str) -> str:
    phone = re.search(r"(\+?\d[\d\s\-]{8,}\d)", text)
    email = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    parts = []
    if phone:
        parts.append(phone.group(1))
    if email:
        parts.append(email.group(0))
    return " | ".join(parts)


def _extract_skills(skill_lines: List[str]) -> List[str]:
    if not skill_lines:
        return []
    joined = " ".join(skill_lines)
    # split by commas/semicolons/bullets
    items = re.split(r"[;,•\u2022]\s*|\s{2,}", joined)
    skills = [s.strip(" -•—\t") for s in items if s and len(s) < 50]
    # de-dup while preserving order
    seen = set()
    out = []
    for s in skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out


def _extract_experience(exp_lines: List[str]) -> List[Dict[str, Any]]:
    """
    Very forgiving: detect role/company/duration if present, gather bullet points.
    """
    if not exp_lines:
        return []

    entries: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {"role": "", "company": "", "duration": "", "details": []}

    role_line_pattern = re.compile(
        r"^(?P<role>.+?)\s+[–—-]\s+(?P<company>.+?)\s*\((?P<dur>[^)]+)\)$"
    )

    for ln in exp_lines:
        m = role_line_pattern.match(ln)
        if m:
            # start new block
            if current["role"] or current["details"]:
                entries.append(current)
            current = {
                "role": m.group("role").strip(),
                "company": m.group("company").strip(),
                "duration": m.group("dur").strip(),
                "details": [],
            }
        elif ln.startswith(BULLET_PREFIXES):
            current["details"].append(ln.lstrip("".join(BULLET_PREFIXES)).strip())
        else:
            # free text lines; attach as detail if not header-ish
            if ln and len(ln.split()) > 2:
                current["details"].append(ln.strip())

    if current["role"] or current["details"]:
        entries.append(current)

    # coerce detail lists
    for e in entries:
        e["details"] = e.get("details") or []

    return entries


def _extract_projects(proj_lines: List[str]) -> List[Dict[str, Any]]:
    """
    Heuristic: project title lines often not starting with bullet; details as bullets.
    """
    if not proj_lines:
        return []

    projects: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {"name": "", "tech": "", "details": []}

    for ln in proj_lines:
        if ln.startswith(BULLET_PREFIXES):
            bullet = ln.lstrip("".join(BULLET_PREFIXES)).strip()
            current["details"].append(bullet)
        else:
            # treat as a new project title if it's not empty and reasonably short
            if current["name"] or current["details"]:
                projects.append(current)
                current = {"name": "", "tech": "", "details": []}
            current["name"] = ln.strip()

    if current["name"] or current["details"]:
        projects.append(current)

    # Trim details and keep max few lines (template later formats 3 bullets anyway)
    for p in projects:
        p["details"] = [d.strip() for d in p.get("details", []) if d.strip()]

    return projects


def _extract_education(edu_lines: List[str], full_text: str) -> List[Dict[str, str]]:
    """
    Return list of dicts: {degree, university, year}
    Works from section lines, else falls back to scanning full text.
    """
    items: List[Dict[str, str]] = []

    def normalize_degree(text: str) -> str:
        up = text.upper()
        # find any degree token and map to full
        for k, v in DEGREE_MAP.items():
            if k in up:
                return v
        # expand common patterns
        if re.search(r"MASTER\S+\s+OF\s+COMPUTER\s+APPLICATIONS", up):
            return "Master of Computer Applications"
        if re.search(r"BACHELOR\S+\s+OF\s+TECHNOLOGY", up):
            return "Bachelor of Technology"
        return text.strip()

    # Try from section lines first
    for ln in edu_lines:
        year = _find_year(ln)
        degree = ""
        university = ""

        # degree guess
        deg_m = re.search(
            r"(M\.?C\.?A\.?|MCA|MBA|M\.?Tech|MTECH|B\.?Tech|BTECH|B\.?E\.?|BE|BCA|B\.?Sc|BSc|B\.?Com|BCom|BBA|B\.?Pharma|BPharma|BA\s*LLB|BALLB|LLB)",
            ln, re.IGNORECASE
        )
        if deg_m:
            degree = normalize_degree(deg_m.group(0))

        # university/college guess
        uni_m = re.search(r"(University|College|Institute|School)[^,|;]*", ln, re.IGNORECASE)
        if uni_m:
            university = uni_m.group(0).strip()

        if degree or university or year:
            items.append({"degree": degree, "university": university, "year": year})

    # Fallback: scan full text for degree patterns if nothing found
    if not items:
        for m in re.finditer(
            r"(?P<deg>M\.?C\.?A\.?|MCA|MBA|M\.?Tech|MTECH|B\.?Tech|BTECH|B\.?E\.?|BE|BCA|B\.?Sc|BSc|B\.?Com|BCom|BBA|B\.?Pharma|BPharma|BA\s*LLB|BALLB|LLB)[^,\n]*?(?P<uni>(University|College|Institute|School)[^,\n]*)?(?P<yr>\b(19|20)\d{2}\b)?",
            full_text, re.IGNORECASE
        ):
            degree = normalize_degree(m.group("deg") or "")
            university = (m.group("uni") or "").strip()
            year = (m.group("yr") or "").strip()
            items.append({"degree": degree, "university": university, "year": year})

    # Guarantee at least one dict (even if blank) so downstream never crashes
    if not items:
        items = [{"degree": "", "university": "", "year": ""}]

    # De-dup while preserving order
    deduped = []
    seen = set()
    for it in items:
        key = (it.get("degree", ""), it.get("university", ""), it.get("year", ""))
        if key not in seen:
            seen.add(key)
            deduped.append(it)

    return deduped


def _find_year(s: str) -> str:
    m = re.search(r"\b(19|20)\d{2}\b", s)
    return m.group(0) if m else ""


def _extract_certifications(cert_lines: List[str]) -> List[str]:
    if not cert_lines:
        return []
    # split bullets/commas
    joined = "\n".join(cert_lines)
    parts = re.split(r"[\n;,•\u2022]", joined)
    certs = [p.strip(" -•—\t") for p in parts if p.strip()]
    # de-dup
    seen = set()
    out = []
    for c in certs:
        low = c.lower()
        if low not in seen:
            seen.add(low)
            out.append(c)
    return out


# ------------------- Normalizer ------------------- #
def _normalize_resume_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure stable schema & types:
      - skills: list[str]
      - experience: list[{role, company, duration, details: list[str]}]
      - projects: list[{name, tech, details: list[str]}]
      - education: list[{degree, university, year}]
      - certifications: list[str]
    """
    out: Dict[str, Any] = {
        "name": str(d.get("name", "")).strip(),
        "contact": str(d.get("contact", "")).strip(),
        "summary": str(d.get("summary", "")).strip(),
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
    }

    # skills
    skills = d.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in re.split(r"[;,]", skills) if s.strip()]
    if isinstance(skills, list):
        out["skills"] = [str(s).strip() for s in skills if str(s).strip()]

    # experience
    for e in d.get("experience", []) or []:
        if isinstance(e, dict):
            out["experience"].append({
                "role": str(e.get("role", "")).strip(),
                "company": str(e.get("company", "")).strip(),
                "duration": str(e.get("duration", "")).strip(),
                "details": [str(x).strip() for x in (e.get("details") or []) if str(x).strip()]
            })

    # projects
    for p in d.get("projects", []) or []:
        if isinstance(p, dict):
            out["projects"].append({
                "name": str(p.get("name", "")).strip(),
                "tech": str(p.get("tech", "")).strip(),
                "details": [str(x).strip() for x in (p.get("details") or []) if str(x).strip()]
            })

    # education
    edu = d.get("education", [])
    if isinstance(edu, dict):
        edu = [edu]
    if isinstance(edu, list):
        norm_edu = []
        for it in edu:
            if isinstance(it, dict):
                norm_edu.append({
                    "degree": str(it.get("degree", "")).strip(),
                    "university": str(it.get("university", "")).strip(),
                    "year": str(it.get("year", "")).strip(),
                })
            else:
                # if plain string line, try light parse
                line = str(it).strip()
                degree = _degree_from_line(line)
                uni = _university_from_line(line)
                year = _find_year(line)
                norm_edu.append({"degree": degree, "university": uni, "year": year})
        out["education"] = norm_edu or [{"degree": "", "university": "", "year": ""}]

    # certifications
    certs = d.get("certifications", [])
    if isinstance(certs, str):
        certs = [c.strip() for c in re.split(r"[;,]", certs) if c.strip()]
    if isinstance(certs, list):
        out["certifications"] = [str(c).strip() for c in certs if str(c).strip()]

    return out


def _degree_from_line(line: str) -> str:
    up = line.upper()
    for k, v in DEGREE_MAP.items():
        if k in up:
            return v
    # generic expansions
    if "MASTER" in up and "COMPUTER" in up and "APPLICATION" in up:
        return "Master of Computer Applications"
    if "BACHELOR" in up and "TECHNOLOGY" in up:
        return "Bachelor of Technology"
    return line


def _university_from_line(line: str) -> str:
    m = re.search(r"(University|College|Institute|School)[^,;\n]*", line, re.IGNORECASE)
    return m.group(0).strip() if m else ""
