# template_filler.py
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

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
        skills_dict=data["skills"]
        if isinstance(skills_dict,list):
            skills_dict={"Skills":skills_dict}
        
        add_skills_section(doc,skills_dict)

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
    run.font.color.rgb = RGBColor(0, 0, 0)  # Dark blue


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

    for detail in proj.get("details", []):
        bullet = doc.add_paragraph(style="List Bullet")
        bullet.add_run(detail)
    
    add_section_divider(doc)
    
def filter_relevant_skills(resume_skills, jd_skills):
    """
    resume_skills: list of skills from user's resume
    jd_skills: list of skills extracted from Job Description
    Returns only the skills that are relevant for this job
    """
    relevant = [skill for skill in resume_skills if skill.lower() in [s.lower() for s in jd_skills]]
    return relevant


def add_skills_section(doc, skills_dict):
   
    from docx.shared import Pt
    
    if not skills_dict:
        return
    
    add_heading(doc, "Key Skills")
    
    for category, items in skills_dict.items():
        if not items:
            continue
        p = doc.add_paragraph()
        run_cat = p.add_run(f"{category:<35}")  # category name aligned left
        run_cat.bold = True
        run_cat.font.size = Pt(11)
        run_items = p.add_run(", ".join(items))
        run_items.font.size = Pt(11)

def add_section_divider(doc):
    """
    Inserts a straight horizontal line in the DOCX document.
    """
    p = doc.add_paragraph()
    
    # Create a border element
    p_border = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')     # type of line: single
    bottom.set(qn('w:sz'), '6')           # thickness
    bottom.set(qn('w:space'), '1')        # space above line
    bottom.set(qn('w:color'), '000000')   # color (black)
    
    p_border.append(bottom)
    p._p.get_or_add_pPr().append(p_border)
    
    return p
