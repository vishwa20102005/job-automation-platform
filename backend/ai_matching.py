import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "nodejs",
    "fastapi",
    "django",
    "flask",
    "spring boot",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "ai",
    "tensorflow",
    "pytorch",
    "langchain",
    "git",
    "github",
    "html",
    "css",
    "rest api",
    "api",
}


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_skills(text: str) -> set[str]:
    text = normalize_text(text)

    found_skills = set()

    for skill in COMMON_SKILLS:

        if skill in text:
            found_skills.add(skill)

    return found_skills


def calculate_match(
    resume_text: str,
    job_text: str
):
    resume_text = normalize_text(resume_text)
    job_text = normalize_text(job_text)

    if not resume_text:
        return {
            "match_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "recommendation": "Resume text is empty"
        }

    if not job_text:
        return {
            "match_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "recommendation": "Job description is empty"
        }

    # -------------------------------------------------
    # TF-IDF similarity
    # -------------------------------------------------

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    try:

        vectors = vectorizer.fit_transform(
            [resume_text, job_text]
        )

        similarity = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0]

    except ValueError:

        similarity = 0.0

    similarity_score = similarity * 100


    # -------------------------------------------------
    # Skill matching
    # -------------------------------------------------

    resume_skills = extract_skills(
        resume_text
    )

    job_skills = extract_skills(
        job_text
    )

    matched_skills = sorted(
        resume_skills.intersection(
            job_skills
        )
    )

    missing_skills = sorted(
        job_skills - resume_skills
    )


    # -------------------------------------------------
    # Skill score
    # -------------------------------------------------

    if job_skills:

        skill_score = (
            len(matched_skills)
            / len(job_skills)
        ) * 100

    else:

        skill_score = similarity_score


    # -------------------------------------------------
    # Final score
    # -------------------------------------------------

    if job_skills:

        final_score = (
            similarity_score * 0.4
            +
            skill_score * 0.6
        )

    else:

        final_score = similarity_score


    final_score = round(
        min(final_score, 100),
        2
    )


    # -------------------------------------------------
    # Recommendation
    # -------------------------------------------------

    if final_score >= 80:

        recommendation = "Excellent Match"

    elif final_score >= 65:

        recommendation = "Strong Match"

    elif final_score >= 50:

        recommendation = "Moderate Match"

    elif final_score >= 30:

        recommendation = "Weak Match"

    else:

        recommendation = "Poor Match"


    return {
        "match_score": final_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommendation": recommendation
    }