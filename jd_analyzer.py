# jd_analyzer.py
"""
Job description analyzer: extracts prioritized keywords/phrases.

Functions:
- extract_jd_keywords(text, top_n=25) -> List[str]
- format_keyword_prompt(keywords) -> str
"""

from typing import List
import re
from collections import Counter

# small english stopword set (keeps file lightweight)
STOPWORDS = set("""
a about above after again against all am an and any are aren't as at be because been before being below between both but by can
can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further had hadn't has hasn't
have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into
is isn't it it's its itself let's me more most mustn't my myself no nor not of off on once only or other ought our ours
ourselves out over own same shan't she she'd she'll she's should shouldn't so some such than that that's the their theirs them
themselves then there there's these they they'd they'll they're they've this those through to too under until up very was wasn't we
we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's with won't would
wouldn't you you'd you'll you're you've your yours yourself yourselves
""".split())

def _tokenize(text: str) -> List[str]:
    text = re.sub(r'[^A-Za-z0-9\s\-\/\+\#\&]', ' ', text)  # keep slashes + hashtags
    tokens = [t.lower().strip() for t in text.split() if t.strip()]
    return tokens

def _bigrams(tokens: List[str]) -> List[str]:
    out = []
    for i in range(len(tokens)-1):
        a, b = tokens[i], tokens[i+1]
        if a not in STOPWORDS and b not in STOPWORDS:
            out.append(f"{a} {b}")
    return out

def extract_jd_keywords(text: str, top_n: int = 25) -> List[str]:
    """
    Extract keyword candidates from a job description text.
    Tries to find multi-word skills/phrases and high-frequency tokens.
    """
    if not text or not text.strip():
        return []

    # Try to use spaCy if available (better noun phrase extraction)
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            # attempt to download? skip and fallback
            nlp = None
        if nlp:
            doc = nlp(text)
            # noun chunks and entities
            phrases = []
            for chunk in doc.noun_chunks:
                ph = chunk.text.strip()
                if len(ph) > 1 and any(c.isalpha() for c in ph):
                    phrases.append(ph.lower())
            # also entities (ORG, PRODUCT, SKILL-like)
            for ent in doc.ents:
                phrases.append(ent.text.lower())
            # score by frequency
            c = Counter([p for p in phrases if p not in STOPWORDS])
            keywords = [k for k, _ in c.most_common(top_n)]
            if keywords:
                return keywords
    except Exception:
        # spaCy not available — fallback
        pass

    # Fallback lightweight extractor:
    tokens = _tokenize(text)
    # filter tokens
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1 and not t.isdigit()]

    uni_counts = Counter(tokens)
    bi_counts = Counter(_bigrams(tokens))

    # take top bigrams first (they're often skill phrases)
    keywords = []
    for k, _ in bi_counts.most_common(top_n):
        if k not in keywords:
            keywords.append(k)
    # then fill with unigrams
    for k, _ in uni_counts.most_common(top_n):
        if k not in keywords:
            keywords.append(k)
        if len(keywords) >= top_n:
            break
    # post-clean: remove overly generic words
    keywords = [k for k in keywords if k not in {"app", "experience", "role", "team", "work"}][:top_n]
    return keywords

def format_keyword_prompt(keywords: List[str], max_display: int = 20) -> str:
    """
    Format a clean instruction block for the LLM including the top keywords.
    """
    if not keywords:
        return ""
    kws = keywords[:max_display]
    return "Important keywords to include (prioritized):\n" + ", ".join(kws)
