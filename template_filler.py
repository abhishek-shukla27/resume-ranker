from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from io import BytesIO


def build_template_resume(data):
    """
    Builds a clean, ATS-friendly DOCX resume from structured resume data.
    """
    doc = Document()

    # ===== NAME =====
    name_para = doc.add_paragraph(str(data.get("name", "")).strip())
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if name_para.runs:
        name_para.runs[0].bold = True
        name_para.runs[0].font.size = Pt(16)

    # ===== CONTACT =====
    contact_para = doc.add_paragraph(str(data.get("contact", "")).strip())
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ===== SUMMARY =====
    add_heading_with_line(doc, "SUMMARY")
    summary_text = str(data.get("summary", "")).strip()
    if summary_text:
        doc.add_paragraph(summary_text)

    # ===== SKILLS =====
    add_heading_with_line(doc, "SKILLS")
    skills_list = data.get("skills", [])
    for skill in skills_list:
        skill_str = str(skill).strip()
        if skill_str:
            doc.add_paragraph(skill_str, style="List Bullet")

    # ===== EXPERIENCE =====
    if data.get("experience"):
        add_heading_with_line(doc, "EXPERIENCE")
        for exp in data["experience"]:
            role_line = f"{exp.get('role', '')} — {exp.get('company', '')} ({exp.get('duration', '')})"
            role_para = doc.add_paragraph(role_line.strip())
            if role_para.runs:
                role_para.runs[0].bold = True
            for d in exp.get("details", []):
                d_str = str(d).strip()
                if d_str:
                    doc.add_paragraph(d_str, style="List Bullet")

    # ===== PROJECTS =====
    if data.get("projects"):
        add_heading_with_line(doc, "PROJECTS")
        for proj in _format_projects(data["projects"]):
            proj_para = doc.add_paragraph(str(proj["name"]).upper())
            if proj_para.runs:
                proj_para.runs[0].bold = True
            for bullet in proj["details"]:
                bullet_str = str(bullet).strip()
                if bullet_str:
                    doc.add_paragraph(bullet_str, style="List Bullet")

    # ===== EDUCATION =====
    if data.get("education"):
        add_heading_with_line(doc, "EDUCATION")
        edu_entries = data["education"]
        if isinstance(edu_entries, str):
            edu_str = edu_entries.strip()
            if edu_str:
                doc.add_paragraph(edu_str)
        elif isinstance(edu_entries, list):
            for e in edu_entries[:2]:
                e_str = str(e).strip()
                if e_str:
                    doc.add_paragraph(e_str, style="List Bullet")

    # ===== CERTIFICATIONS =====
    if data.get("certifications"):
        add_heading_with_line(doc, "CERTIFICATIONS")
        for cert in data["certifications"]:
            cert_str = str(cert).strip()
            if cert_str:
                doc.add_paragraph(cert_str, style="List Bullet")

    # ===== RETURN AS BYTESIO =====
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def add_heading_with_line(doc, text):
    """
    Add a heading in ALL CAPS + bold + underline line (no gap).
    """
    para = doc.add_paragraph()
    run = para.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(12)
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(0)

    # Add bottom border line
    p_pr = para._p.get_or_add_pPr()
    p_borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "0")
    bottom.set(qn("w:color"), "000000")
    p_borders.append(bottom)
    p_pr.append(p_borders)


def _format_projects(projects):
    """
    Ensure projects have 3 clean bullet points: Objective, Tech Stack, Features.
    """
    formatted = []
    for proj in projects:
        name = proj.get("name", "Untitled Project")
        tech = proj.get("tech", "")
        details = proj.get("details", [])

        bullets = []
        if details:
            if len(details) >= 1:
                bullets.append(f"Objective: {details[0]}")
            if tech:
                bullets.append(f"Tech Stack: {tech}")
            if len(details) >= 2:
                bullets.append(f"Features: {details[1]}")
        formatted.append({"name": name, "details": bullets})
    return formatted
