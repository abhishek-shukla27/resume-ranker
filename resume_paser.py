import fitz

def parse_resume(file):
    doc=fitz.open(stream=file.read(),filetype="pdf")
    text=""

    for page in doc:
        text+=page.get_text()
    
    return text.lower()