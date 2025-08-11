# resume_parser.py
"""
Resume parser utilities.

Functions:
- parse_pdf_resume(file_bytes) -> dict
- parse_docx_resume(file_bytes) -> dict
- parse_resume_auto(file_bytes, filename) -> dict  # chooses PDF vs DOCX
"""

from typing import List, Dict
import fitz  # PyMuPDF
from docx import Document
import re
import io

SECTION_KEYWORDS = {
    "summary": ["summary", "professional summary", "profile", "about"],
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic", "qualifications"],
    "skills": ["skills", "technical skills", "key skills"],
    "certifications": ["certification", "certifications", "licenses"],
    "projects": ["projects", "personal projects"],
}

def _clean_text(s: str) -> str:
    return re.sub(r'\r', '\n', s).strip()

def _split_paragraphs(text: str) -> List[str]:
    # Split on two or more newlines, or lines that look like section breaks
    paras = re.split(r'\n\s*\n+', text)
    return [p.strip() for p in paras if p.strip()]

def _find_section_by_heading(paras: List[str]) -> Dict[str, List[str]]:
    sections = {k: [] for k in SECTION_KEYWORDS.keys()}
    sections['other'] = []

    current = "other"
    for p in paras:
        low = p.lower()
        matched = False
        for sec, keys in SECTION_KEYWORDS.items():
            for k in keys:
                # heading detection: paragraph equals heading or starts with heading
                if (low == k) or low.startswith(k + ":") or low.startswith(k + " -") or low.startswith(k + " —") or re.match(rf'^{k}\b', low):
                    current = sec
                    matched = True
                    break
            if matched:
                break
        if not matched:
            sections[current].append(p)
    return sections

def parse_pdf_resume(file_bytes: bytes) -> Dict:
    """
    Parse a PDF resume (bytes) and return a structured dict.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise RuntimeError(f"Failed to open PDF: {e}")

    pages_text = []
    for page in doc:
        txt = page.get_text("text")
        pages_text.append(txt)
    full_text = "\n\n".join(pages_text)
    full_text = _clean_text(full_text)

    # heuristics: split into paragraphs and detect sections
    paras = _split_paragraphs(full_text)
    sections = _find_section_by_heading(paras)

    # Try to guess name + contact from top paragraphs
    name = ""
    contact = ""
    if paras:
        top = paras[0].splitlines()
        if len(top) > 0:
            # name often first short line
            candidate = top[0].strip()
            if 2 <= len(candidate.split()) <= 4 and len(candidate) < 60:
                name = candidate
        # contact often in first 2-3 lines
        for line in top[:4]:
            if re.search(r'@|phone|tel|@gmail|@\w+\.\w+', line.lower()) or re.search(r'\+?\d{7,}', line):
                contact += line.strip() + " | "

    contact = contact.strip(" | ")

    structured = {
        "name": name,
        "contact": contact,
        "summary": "\n\n".join(sections.get("summary", [])).strip(),
        "experience": sections.get("experience", []),
        "education": sections.get("education", []),
        "skills": sections.get("skills", []),
        "certifications": sections.get("certifications", []),
        "projects": sections.get("projects", []),
        "other": sections.get("other", []),
        "raw_text": full_text
    }
    return structured

def parse_docx_resume(file_bytes: bytes) -> Dict:
    """
    Parse a DOCX resume (bytes) and return a structured dict.
    """
    bio = io.BytesIO(file_bytes)
    doc = Document(bio)
    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paras)
    paras_split = _split_paragraphs(text)
    sections = _find_section_by_heading(paras_split)

    # guess name/contact similar to PDF
    name = ""
    contact = ""
    if paras_split:
        top = paras_split[0].splitlines()
        if top:
            candidate = top[0].strip()
            if 2 <= len(candidate.split()) <= 4 and len(candidate) < 60:
                name = candidate
        for line in top[:4]:
            if re.search(r'@|phone|tel|@gmail|@\w+\.\w+', line.lower()) or re.search(r'\+?\d{7,}', line):
                contact += line.strip() + " | "
    contact = contact.strip(" | ")

    structured = {
        "name": name,
        "contact": contact,
        "summary": "\n\n".join(sections.get("summary", [])).strip(),
        "experience": sections.get("experience", []),
        "education": sections.get("education", []),
        "skills": sections.get("skills", []),
        "certifications": sections.get("certifications", []),
        "projects": sections.get("projects", []),
        "other": sections.get("other", []),
        "raw_text": text
    }
    return structured

def parse_resume_auto(file_bytes: bytes, filename: str = "") -> Dict:
    """
    Auto-detect PDF vs DOCX (by filename) and parse accordingly.
    Returns the same structured dict.
    """
    name = filename.lower()
    if name.endswith(".pdf") or (b"%PDF" in file_bytes[:4]):
        return parse_pdf_resume(file_bytes)
    elif name.endswith(".docx"):
        return parse_docx_resume(file_bytes)
    else:
        # fallback try PDF first then DOCX
        try:
            return parse_pdf_resume(file_bytes)
        except Exception:
            return parse_docx_resume(file_bytes)
