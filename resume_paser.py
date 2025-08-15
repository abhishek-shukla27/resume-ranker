import re
import fitz  # PyMuPDF
import docx
from typing import Dict, Any, List

# Degree abbreviation mapping
DEGREE_MAP = {
    "MBA": "Master of Business Administration",
    "MCA": "Master of Computer Applications",
    "BTECH": "Bachelor of Technology",
    "B.TECH": "Bachelor of Technology",
    "BBA": "Bachelor of Business Administration",
    "BPHARMA": "Bachelor of Pharmacy",
    "B.PHARMA": "Bachelor of Pharmacy",
    "BALLB": "Bachelor of Arts and Bachelor of Laws",
    "B.A.LLB": "Bachelor of Arts and Bachelor of Laws",
    "BSC": "Bachelor of Science",
    "B.SC": "Bachelor of Science",
    "BCA": "Bachelor of Computer Applications"
}

def normalize_degree(degree_text: str) -> str:
    """Expand degree abbreviations."""
    text = degree_text.upper()
    for short, full in DEGREE_MAP.items():
        if short in text:
            return full
    return degree_text.strip()

def parse_pdf_resume(file_path: str) -> Dict[str, Any]:
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()

    return extract_sections(text)

def parse_docx_resume(file_path: str) -> Dict[str, Any]:
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return extract_sections(text)

def extract_sections(text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    data = {
        "name": lines[0] if lines else "",
        "contact": extract_contact(text),
        "summary": "",
        "skills": extract_skills(text),
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": []
    }

    # Extract education section
    edu_matches = []
    edu_pattern = re.compile(
        r"(MCA|MBA|B\.?Tech|BBA|B\.?Pharma|BALLB|B\.?Sc|BCA).*?(University|College|School).*?(\d{4})?",
        re.IGNORECASE
    )
    for match in edu_pattern.finditer(text):
        degree_raw = match.group(1) or ""
        degree_full = normalize_degree(degree_raw)
        university = match.group(2) or ""
        year = match.group(3) or ""
        edu_matches.append({
            "degree": degree_full,
            "university": university.strip(),
            "year": year.strip()
        })

    # If no structured match, fallback
    if not edu_matches:
        edu_matches.append({
            "degree": "",
            "university": "",
            "year": ""
        })

    data["education"] = edu_matches

    return data

def extract_contact(text: str) -> str:
    phone = re.search(r"(\+?\d[\d\s-]{8,}\d)", text)
    email = re.search(r"[\w\.-]+@[\w\.-]+", text)
    contact_parts = []
    if phone:
        contact_parts.append(phone.group(1))
    if email:
        contact_parts.append(email.group(0))
    return " | ".join(contact_parts)

def extract_skills(text: str) -> List[str]:
    skills_pattern = re.compile(r"(Skills|Technical Skills)\s*:\s*(.+)", re.IGNORECASE)
    match = skills_pattern.search(text)
    if match:
        skills_str = match.group(2)
        return [s.strip() for s in re.split(r",|;", skills_str) if s.strip()]
    return []

