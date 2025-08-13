# template_filler.py
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO


def build_template_resume(data):
    """
    Builds a DOCX resume from structured resume data.
    Returns BytesIO for download.
    """
    doc = Document()

    # ===== Name & Contact =====
    name = doc.add_paragraph()
    run = name.add_run(data.get("name", ""))
    run.font.size = Pt(20)
    run.bold = True
    name.alignment = WD_ALIGN_PARAGRAPH.CENTER

    contact = doc.add_paragraph(data.get("contact", ""))
    contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact.runs[0].font.size = Pt(10)
    contact.runs[0].font.color.rgb = RGBColor(100, 100, 100)

    doc.add_paragraph("")

    # ===== Summary =====
    if data.get("summary"):
        add_heading(doc, "Professional Summary")
        doc.add_paragraph(data["summary"])

    # ===== Skills =====
    if data.get("skills"):
        add_heading(doc, "Key Skills")
        doc.add_paragraph(", ".join(data["skills"]))

    # ===== Experience =====
    if data.get("experience"):
        add_heading(doc, "Professional Experience")
        for exp in data["experience"]:
            add_experience_block(doc, exp)

    # ===== Projects =====
    if data.get("projects"):
        add_heading(doc, "Projects")
        for proj in data["projects"]:
            add_project_block(doc, proj)

    # ===== Education =====
    if data.get("education"):
        add_heading(doc, "Education")
        if isinstance(data["education"], list):
            for edu in data["education"]:
                doc.add_paragraph(str(edu))
        else:
            doc.add_paragraph(str(data["education"]))

    # ===== Certifications =====
    if data.get("certifications"):
        add_heading(doc, "Certifications")
        doc.add_paragraph(", ".join(data["certifications"]))

    # Save to buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ===================== HELPERS ===================== #

def add_heading(doc, text):
    p = doc.add_paragraph()
    run = p.add_run(text.upper())
    run.font.size = Pt(12)
    run.bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run.font.color.rgb = RGBColor(0, 51, 102)  # Dark blue


def add_experience_block(doc, exp):
    role_line = f"{exp.get('role', '')} – {exp.get('company', '')}"
    if exp.get("duration"):
        role_line += f" ({exp['duration']})"
    p = doc.add_paragraph()
    run = p.add_run(role_line)
    run.font.size = Pt(11)
    run.bold = True

    for detail in exp.get("details", []):
        bullet = doc.add_paragraph(style="List Bullet")
        bullet.add_run(detail)


def add_project_block(doc, proj):
    title_line = f"{proj.get('name', '')}"
    if proj.get("tech"):
        title_line += f" – {proj['tech']}"
    p = doc.add_paragraph()
    run = p.add_run(title_line)
    run.font.size = Pt(11)
    run.bold = True
    add_section_divider()
    for detail in proj.get("details", []):
        bullet = doc.add_paragraph(style="List Bullet")
        bullet.add_run(detail)
    
def add_section_divider(doc):
    p=doc.add_paragraph()
    run=p.add_run("-"*40)
    run.bold=True
