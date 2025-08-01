
def calculate_match_score(resume_text,job_description):
    resume_words = set(resume_text.lower().split())
    jd_words = set(job_description.lower().split())

    matched = list(jd_words & resume_words)
    missing = list(jd_words - resume_words)

    total = len(jd_words)
    score = round((len(matched) / total) * 100) if total > 0 else 0

    return matched, missing, score
