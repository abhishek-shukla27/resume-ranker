import fitz
import re
import language_tool_python

tool=language_tool_python.LanguageTool('en-US')

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes."""
    doc=fitz.open(stream=pdf_bytes,filetype="pdf")
    text="\n".join(page.get_text()for page in doc)
    return text

def clean_resume_text(text):
    """Remove useless parts & fixes grammar."""
    text=re.sub(r'\n?\s*\d+\s*\n?','\n',text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    matches = tool.check(text)
    corrected = language_tool_python.utils.correct(text, matches)
    return corrected.strip()