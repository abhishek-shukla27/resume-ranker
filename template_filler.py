from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO

# Degree mapping for full form
DEGREE_MAP = {
    "mca": "Master of Computer Applications",
    "mba": "Master of Business Administration",
    "btech": "Bachelor of Technology",
    "bca": "Bachelor of Computer Applications",
    "bba": "Bachelor of Business Administration",
    "bcom": "Bachelor of Commerce",
    "bpharma": "Bachelor of Pharmacy",
    "ballb": "Bachelor of Arts and Bachelor of Laws"
}

def build_template_resume(data):
    """
    Builds a DOCX resume from structured data with fixed formatting rules.
    """
    doc = Document()

    # ===== Name =====
    name_para = doc.add_paragraph(data.get("name", ""))
    name_para.runs[0].bold = True
    name_para.runs[0].font.size = Pt(16)
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ===== Contact =====
    contact_para = doc.add_paragraph(data.get("contact", ""))
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ===== Summary =====
    _add_section_heading(doc, "Professional Summary")
    doc.add_paragraph(_format_summary(data))

    _add_horizontal_line(doc)

    # ===== Skills =====
    if data.get("skills"):
        _add_section_heading(doc, "Skills")
        doc.add_paragraph(", ".join(data["skills"]))
        _add_horizontal_line(doc)

    # ===== Projects =====
    if data.get("projects"):
        _add_section_heading(doc, "Projects")
        for proj in _format_projects(data.get("projects", [])):
            doc.add_paragraph(proj["name"], style="List Bullet")
            for detail in proj["details"]:
                doc.add_paragraph(f"- {detail}", style="List Bullet 2")
        _add_horizontal_line(doc)

    # ===== Education =====
    if data.get("education"):
        _add_section_heading(doc, "Education")
        for edu in _format_education(data.get("education", [])):
            doc.add_paragraph(edu)
        _add_horizontal_line(doc)

    # ===== Certifications =====
    if data.get("certifications"):
        _add_section_heading(doc, "Certifications")
        for cert in data["certifications"]:
            doc.add_paragraph(cert, style="List Bullet")

    # Output to BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ================= Helper Functions ================= #

def _add_section_heading(doc, title):
    p = doc.add_paragraph(title)
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(12)

def _add_horizontal_line(doc):
    # Just adding empty paragraph to simulate line break
    doc.add_paragraph("")

def _format_summary(data):
    """
    Fixed 2-line summary format based on degree, university, and top skills.
    """
    # Extract degree & university
    degree_full = ""
    university = ""
    edu_list = data.get("education", [])

    if isinstance(edu_list, str):
        edu_list = [edu_list]

    if edu_list:
        edu_text = edu_list[0].lower()
        for key, val in DEGREE_MAP.items():
            if key in edu_text:
                degree_full = val
                break
        university = " ".join(edu_list[0].split()[3:])  # crude extract

    # Extract top 3 skills
    skills = data.get("skills", [])
    top_skills = ", ".join(skills[:3]) if skills else "relevant technologies"

    return f"Enthusiastic and highly motivated recent graduate with a {degree_full} from {university}. Possess strong foundational knowledge in {top_skills}."

def _format_projects(projects):
    """
    Format projects with exactly 3 bullet points: Objective, Tech Stack, Features.
    """
    formatted = []
    for proj in projects:
        name = proj.get("name", "Untitled Project")
        tech = proj.get("tech", "N/A")
        details = proj.get("details", [])

        bullets = []
        bullets.append(f"Objective: {details[0] if details else 'N/A'}")
        bullets.append(f"Tech Stack: {tech}")
        bullets.append(f"Features: {details[1] if len(details) > 1 else 'N/A'}")

        formatted.append({"name": name, "details": bullets})
    return formatted

def _format_education(education):
    """
    Returns top 2 qualifications with full form and year.
    """
    if isinstance(education, str):
        education = [education]

    formatted = []
    for entry in education[:2]:
        text = entry
        lower_text = text.lower()
        for key, val in DEGREE_MAP.items():
            if key in lower_text:
                text = text.replace(key.upper(), val).replace(key.capitalize(), val)
        formatted.append(text)
    return formatted
