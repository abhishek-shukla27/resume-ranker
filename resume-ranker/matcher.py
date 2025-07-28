
def calculate_match_score(resume_text,jd_keywords):
    resume_words=set(resume_text.split())
    matched=[kw for kw in jd_keywords if kw in resume_words]
    missing=[kw for kw in jd_keywords if kw not in resume_words]
    score=int((len(matched)/len(jd_keywords))*100) if jd_keywords else 0
    return score,matched,missing
