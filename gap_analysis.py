from matcher import calculate_match_score
from jd_analyzer import extract_jd_keywords


def analyze_role_gap(resume_text, job_desc):
    """Returns missing keywords and score."""
    jd_keywords = extract_jd_keywords(job_desc)
    matched, missing, score = calculate_match_score(resume_text, job_desc)
    return {
        "jd_keywords": jd_keywords,
        "matched": matched,
        "missing": missing,
        "score": score
    }