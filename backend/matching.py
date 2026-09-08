import re


def extract_keywords(text: str) -> set[str]:
    """
    Convert text into a set of useful keywords.
    """

    if not text:
        return set()

    text = text.lower()

    # Keep words, numbers and common technology symbols
    words = re.findall(
        r"[a-zA-Z][a-zA-Z0-9+#.-]*",
        text
    )

    # Remove very common words
    stop_words = {
        "and",
        "the",
        "for",
        "with",
        "from",
        "this",
        "that",
        "are",
        "you",
        "your",
        "our",
        "will",
        "have",
        "has",
        "using",
        "into",
        "about",
        "job",
        "role",
        "work",
        "years"
    }

    keywords = {
        word
        for word in words
        if len(word) > 1
        and word not in stop_words
    }

    return keywords


def calculate_match_score(
    resume_text: str,
    job_text: str
):
    """
    Calculate resume/job keyword matching score.
    """

    resume_keywords = extract_keywords(
        resume_text
    )

    job_keywords = extract_keywords(
        job_text
    )

    if not job_keywords:

        return {
            "score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "match_level": "LOW"
        }

    matched_keywords = (
        resume_keywords & job_keywords
    )

    missing_keywords = (
        job_keywords - resume_keywords
    )

    score = (
        len(matched_keywords)
        / len(job_keywords)
    ) * 100

    score = round(
        score,
        2
    )

    if score >= 80:

        match_level = "EXCELLENT"

    elif score >= 60:

        match_level = "GOOD"

    elif score >= 40:

        match_level = "PARTIAL"

    else:

        match_level = "LOW"

    return {
        "score": score,
        "matched_keywords": sorted(
            matched_keywords
        ),
        "missing_keywords": sorted(
            missing_keywords
        ),
        "match_level": match_level
    }