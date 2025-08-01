import re
import spacy
nlp=spacy.load("en_core_web_sm")

def parse_jd(jd_text):
    doc=nlp(jd_text.lower())
    keywords=[token.text for token in doc if token.is_alpha and not token.is_stop]
    return list(set(keywords))