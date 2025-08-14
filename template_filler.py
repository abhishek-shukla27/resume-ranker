from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def build_template_resume(data):
    """
    Builds a DOCX resume from structured resume data.
    """
    doc = Document()

    # Name
    name_para = doc.add_paragraph(data.get("name", ""))
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_para.runs[0].bold = True
    name_para.runs[0].font.size = Pt(16)

    # Contact
    contact_para = doc.add_paragraph(data.get("contact", ""))
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # SUMMARY
    add_heading_with_line(doc, "SUMMARY")
    doc.add_paragraph(data.get("summary", ""))

    # SKILLS
    add_heading_with_line(doc, "SKILLS")
    skills = ", ".join(data.get("skills", []))
    doc.add_paragraph(skills)

    # EXPERIENCE (skip if fresher)
    if data.get("experience"):
        add_heading_with_line(doc, "EXPERIENCE")
        for exp in data["experience"]:
            role_line = f"{exp.get('role', '')} – {exp.get('company', '')} ({exp.get('duration', '')})"
            role_para = doc.add_paragraph(role_line)
            role_para.runs[0].bold = True
            for d in exp.get("details", []):
                doc.add_paragraph(f"• {d}", style="List Bullet")

    # PROJECTS
    if data.get("projects"):
        add_heading_with_line(doc, "PROJECTS")
        for proj in _format_projects(data["projects"]):
            proj_para = doc.add_paragraph(proj["name"].upper())
            proj_para.runs[0].bold = True
            for bullet in proj["details"]:
                doc.add_paragraph(f"• {bullet}", style="List Bullet")

    # EDUCATION
    if data.get("education"):
        add_heading_with_line(doc, "EDUCATION")
        edu_list = data["education"]
        if isinstance(edu_list, str):
            doc.add_paragraph(edu_list)
        elif isinstance(edu_list, list):
            top_two = edu_list[:2]
            for e in top_two:
                doc.add_paragraph(f"• {e}")

    # CERTIFICATIONS
    if data.get("certifications"):
        add_heading_with_line(doc, "CERTIFICATIONS")
        for cert in data["certifications"]:
            doc.add_paragraph(f"• {cert}")

    # Save to BytesIO
    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def add_heading_with_line(doc, text):
    """
    Adds a bold, capitalized heading with a solid line after it.
    """
    para = doc.add_paragraph(text.upper())
    run = para.runs[0]
    run.bold = True
    run.font.size = Pt(12)

    # Horizontal line
    p = doc.add_paragraph()
    p_para = p._p
    p_pr = p_para.get_or_add_pPr()
    p_borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    p_borders.append(bottom)
    p_pr.append(p_borders)


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
