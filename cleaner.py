import fitz  # PyMuPDF
from textblob import TextBlob
import re

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes."""
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in pdf_doc:
        text += page.get_text()
    return text

def clean_resume_text(text):
    """Clean and correct grammar in the resume text."""
    # Remove extra spaces and line breaks
    text = re.sub(r'\s+', ' ', text).strip()

    # Grammar correction using TextBlob (no Java required)
    blob = TextBlob(text)
    corrected_text = str(blob.correct())

    return corrected_text
