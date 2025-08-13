from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import io

def build_template_resume(data):
    doc = Document()

    # Set page margins (0.75 inch all sides)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # ===== NAME =====
    add_name_section(doc, data.get("name", ""), data.get("contact", ""))

    # ===== SUMMARY =====
    if data.get("summary"):
        add_section(doc, "PROFESSIONAL SUMMARY", data["summary"])

    # ===== SKILLS =====
    if data.get("skills"):
        add_section(doc, "SKILLS", format_skills(data["skills"]))

    # ===== EXPERIENCE =====
    if data.get("experience"):
        add_experience_section(doc, data["experience"])

    # ===== PROJECTS =====
    if data.get("projects"):
        add_projects_section(doc, data["projects"])

    # ===== EDUCATION =====
    if data.get("education"):
        add_section(doc, "EDUCATION", data["education"])

    # ===== CERTIFICATIONS =====
    if data.get("certifications"):
        add_section(doc, "CERTIFICATIONS", data["certifications"])

    # Save in memory
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ---------------- Helper Functions ---------------- #

def add_name_section(doc, name, contact):
    # Name - 16pt Bold, Center
    p = doc.add_paragraph(name)
    run = p.runs[0]
    run.bold = True
    run.font.size = Pt(16)
    run.font.name = "Calibri"
    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Contact Info - 10pt Center
    if contact:
        p = doc.add_paragraph(contact)
        run = p.runs[0]
        run.font.size = Pt(10)
        run.font.name = "Calibri"
        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER


def add_section(doc, title, content):
    # Heading - 11pt Bold, Caps
    p = doc.add_paragraph(title.upper())
    run = p.runs[0]
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = "Calibri"
    run.font.color.rgb = RGBColor(0, 0, 0)

    # Content - 10pt Body
    if isinstance(content, list):
        for item in content:
            para = doc.add_paragraph("• " + item)
            para.style.font.name = "Calibri"
            para.style.font.size = Pt(10)
    else:
        para = doc.add_paragraph(content)
        para.style.font.name = "Calibri"
        para.style.font.size = Pt(10)


def add_experience_section(doc, experiences):
    # Heading
    p = doc.add_paragraph("EXPERIENCE")
    run = p.runs[0]
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = "Calibri"

    for exp in experiences:
        # Role & Company line
        role_line = f"{exp.get('role', '')} – {exp.get('company', '')} ({exp.get('dates', '')})"
        p = doc.add_paragraph(role_line)
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(10)
        p.runs[0].font.name = "Calibri"

        # Bullets
        for bullet in exp.get("details", []):
            para = doc.add_paragraph("• " + bullet)
            para.style.font.name = "Calibri"
            para.style.font.size = Pt(10)


def add_projects_section(doc, projects):
    # Heading
    p = doc.add_paragraph("PROJECTS")
    run = p.runs[0]
    run.bold = True
    run.font.size = Pt(11)
    run.font.name = "Calibri"

    for proj in projects:
        # Title line
        title_line = f"{proj.get('name', '')} – {proj.get('tech', '')}"
        p = doc.add_paragraph(title_line)
        p.runs[0].bold = True
        p.runs[0].font.size = Pt(10)
        p.runs[0].font.name = "Calibri"

        # Bullets
        for bullet in proj.get("details", []):
            para = doc.add_paragraph("• " + bullet)
            para.style.font.name = "Calibri"
            para.style.font.size = Pt(10)


def format_skills(skills):
    """Join skills with separator for inline look"""
    if isinstance(skills, list):
        return " | ".join(skills)
    return skills
