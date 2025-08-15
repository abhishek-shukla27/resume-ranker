from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from io import BytesIO

def build_template_resume(data):
    """
    Builds a DOCX resume from structured resume data.
    Returns BytesIO buffer for download.
    """
    doc = Document()

    # ===== Name =====
    name_para = doc.add_paragraph(data.get("name", "").strip())
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = name_para.runs[0]
    run.bold = True
    run.font.size = Pt(16)

    # ===== Contact =====
    contact_para = doc.add_paragraph(data.get("contact", "").strip())
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_para.runs[0].font.size = Pt(10)

    # ===== SUMMARY =====
    add_heading_with_line(doc, "SUMMARY")
    doc.add_paragraph(data.get("summary", "").strip())

    # ===== SKILLS =====
    add_heading_with_line(doc, "SKILLS")
    skills = ", ".join(data.get("skills", []))
    doc.add_paragraph(skills.strip())

    # ===== EXPERIENCE =====
    if data.get("experience"):
        add_heading_with_line(doc, "EXPERIENCE")
        for exp in data["experience"]:
            role_line = f"{exp.get('role', '')} – {exp.get('company', '')} ({exp.get('duration', '')})"
            role_para = doc.add_paragraph(role_line.strip())
            role_para.runs[0].bold = True
            for detail in exp.get("details", []):
                doc.add_paragraph(detail.strip(), style="List Bullet")

    # ===== PROJECTS =====
    if data.get("projects"):
        add_heading_with_line(doc, "PROJECTS")
        for proj in _format_projects(data["projects"]):
            proj_para = doc.add_paragraph(proj["name"].upper().strip())
            proj_para.runs[0].bold = True
            for bullet in proj["details"]:
                doc.add_paragraph(bullet.strip(), style="List Bullet")

    # ===== EDUCATION =====
    if data.get("education"):
        add_heading_with_line(doc, "EDUCATION")
        edu_list = data["education"]
        if isinstance(edu_list, str):
            doc.add_paragraph(edu_list.strip())
        elif isinstance(edu_list, list):
            for e in edu_list[:2]:
                        if isinstance(e, dict):
                            line = " • ".join(filter(None, [
                                e.get("degree", "").strip(),
                                e.get("university", "").strip(),
                                e.get("year", "").strip()
            ]))
                            doc.add_paragraph(line)
                        else:
                            doc.add_paragraph(str(e).strip())


    # ===== CERTIFICATIONS =====
    if data.get("certifications"):
        add_heading_with_line(doc, "CERTIFICATIONS")
        for cert in data["certifications"]:
            doc.add_paragraph(cert.strip(), style="List Bullet")

    # Save to BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def add_heading_with_line(doc, text):
    """
    Adds a bold uppercase heading with a thin solid line immediately below.
    """
    para = doc.add_paragraph()
    run = para.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(12)
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    para.paragraph_format.space_before = Pt(2)
    para.paragraph_format.space_after = Pt(0)

    # Add bottom border (solid thin line)
    p_pr = para._p.get_or_add_pPr()
    p_borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")  # normal thin line
    bottom.set(qn("w:space"), "0")
    bottom.set(qn("w:color"), "000000")
    p_borders.append(bottom)
    p_pr.append(p_borders)

def _format_projects(projects):
    """
    Format projects with exactly 3 bullet points: Objective, Tech Stack, Features.
    """
    formatted = []
    for proj in projects:
        name = proj.get("name", "UNTITLED PROJECT").strip()
        tech = proj.get("tech", "").strip()
        details = proj.get("details", [])

        bullets = []
        if details:
            bullets.append(f"Objective: {details[0].strip() if details[0] else 'N/A'}")
        else:
            bullets.append("Objective: N/A")
        bullets.append(f"Tech Stack: {tech if tech else 'N/A'}")
        if len(details) > 1 and details[1]:
            bullets.append(f"Features: {details[1].strip()}")
        else:
            bullets.append("Features: N/A")

        formatted.append({"name": name, "details": bullets})
    return formatted
