from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from io import BytesIO
def build_template_resume(data):
    """
    Builds a DOCX resume from structured resume data.
    Returns BytesIO for download.
    """
    doc = Document()

    # Name & contact
    name_para = doc.add_paragraph(data.get("name", ""))
    name_para.style.font.size = Pt(18)
    name_para.style.font.bold = True
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    contact_para = doc.add_paragraph(data.get("contact", ""))
    contact_para.style.font.size = Pt(10)
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_section(doc, "SUMMARY")
    doc.add_paragraph(data.get("summary", ""), style="Normal")

    add_section(doc, "SKILLS")
    skills = ", ".join(data.get("skills", []))
    doc.add_paragraph(skills, style="Normal")

    add_section(doc, "EXPERIENCE")
    for exp in data.get("experience", []):
        if exp.get("role"):
            p = doc.add_paragraph(f"{exp['role']} – {exp.get('company', '')} ({exp.get('duration', '')})")
            p.style.font.bold = True
            for detail in exp.get("details", []):
                add_bullet(doc, detail)

    add_section(doc, "PROJECTS")
    for proj in _format_projects(data.get("projects", [])):
        proj_title = doc.add_paragraph(proj["name"].upper())
        proj_title.style.font.bold = True
        for bullet in proj["details"]:
            add_bullet(doc, bullet)

    add_section(doc, "EDUCATION")
    if isinstance(data.get("education"), list):
        for edu in data["education"]:
            doc.add_paragraph(str(edu))
    else:
        doc.add_paragraph(str(data.get("education", "")))

    if data.get("certifications"):
        add_section(doc, "CERTIFICATIONS")
        for cert in data["certifications"]:
            add_bullet(doc, cert)

    

    buffer=BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def add_section(doc, title):
    """
    Adds a section heading with a thin underline and minimal spacing.
    """
    heading = doc.add_paragraph(title.upper())
    run = heading.runs[0]
    run.font.bold = True
    run.font.size = Pt(11)
    heading.paragraph_format.space_after = Pt(2)
    heading.paragraph_format.space_before = Pt(6)
    add_horizontal_line(doc)


def add_horizontal_line(doc):
    """
    Adds a thin horizontal line like in Prabhat Jha's resume.
    """
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(0)
    p._element.get_or_add_pPr().insert(0, _create_hrule())


def _create_hrule():
    """
    Creates a thin solid horizontal line.
    """
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    p.append(pPr)
    pBdr = OxmlElement('w:pBdr')
    pPr.append(pBdr)
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')  # Thin line (1pt)
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    return p


def add_bullet(doc, text):
    """
    Adds a bullet point with proper spacing.
    """
    para = doc.add_paragraph(text, style="List Bullet")
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.left_indent = Inches(0.25)


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
