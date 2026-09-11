import re
from typing import Set, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# COMMON TECHNICAL SKILLS
# ============================================================

COMMON_SKILLS = {
    # Programming
    "python",
    "java",
    "c",
    "c++",
    "c#",
    "javascript",
    "typescript",
    "sql",

    # Web Development
    "html",
    "css",
    "react",
    "react.js",
    "node.js",
    "nodejs",
    "express",
    "fastapi",
    "django",
    "flask",
    "spring boot",
    "rest api",
    "restful api",

    # Databases
    "mysql",
    "postgresql",
    "mongodb",
    "sqlite",
    "redis",

    # Cloud
    "azure",
    "microsoft azure",
    "aws",
    "amazon web services",
    "gcp",
    "google cloud",
    "cloud computing",
    "azure ai",
    "azure openai",

    # AI / ML
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",
    "computer vision",
    "generative ai",
    "genai",
    "large language models",
    "llm",
    "llms",
    "prompt engineering",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "sklearn",
    "keras",
    "hugging face",

    # AI frameworks / tools
    "langchain",
    "langgraph",
    "faiss",
    "rag",
    "retrieval augmented generation",
    "openai",
    "gemini",

    # DevOps / Tools
    "git",
    "github",
    "docker",
    "kubernetes",
    "linux",
    "ci/cd",
    "jenkins",

    # APIs / Automation
    "api",
    "microservices",
    "web scraping",
    "automation",
    "n8n",

    # Data
    "data analysis",
    "data science",
    "pandas",
    "numpy",
    "power bi",
    "tableau",

    # Microsoft certifications / technologies
    "ai-900",
    "ai-102",
    "azure ai engineer",
    "azure machine learning",
}


# ============================================================
# WORDS THAT MUST NOT BE TREATED AS SKILLS
# ============================================================

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "this",
    "to",
    "under",
    "using",
    "we",
    "with",
    "you",
    "your",
    "will",
    "work",
    "working",
    "skills",
    "skill",
    "experience",
    "role",
    "job",
    "candidate",
    "team",
    "years",
    "year",
}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = str(text).lower()

    # Normalize common symbols
    text = text.replace("&", " and ")
    text = text.replace("/", " ")
    text = text.replace("_", " ")

    # Keep letters, numbers, +, #, dots and hyphens
    text = re.sub(r"[^a-z0-9+#.\- ]+", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# SKILL MATCHING
# ============================================================

def skill_pattern(skill: str) -> str:
    """
    Create a safe regex pattern for a skill.
    Prevents words such as 'ai' from matching inside unrelated words.
    """

    escaped = re.escape(skill.lower())

    # Allow spaces between multi-word skills
    escaped = escaped.replace(r"\ ", r"\s+")

    return rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"


def extract_skills(text: str) -> Set[str]:
    """
    Extract only known technical skills.
    Uses word boundaries so stopwords/noise are not counted.
    """

    text = normalize_text(text)

    found_skills = set()

    if not text:
        return found_skills

    for skill in COMMON_SKILLS:

        if skill in STOPWORDS:
            continue

        pattern = skill_pattern(skill)

        if re.search(pattern, text, re.IGNORECASE):
            found_skills.add(skill)

    # Remove duplicate concept aliases where appropriate
    if "node.js" in found_skills and "nodejs" in found_skills:
        found_skills.discard("nodejs")

    if "sklearn" in found_skills and "scikit-learn" in found_skills:
        found_skills.discard("sklearn")

    if "llm" in found_skills and "large language models" in found_skills:
        found_skills.discard("llm")

    if "llms" in found_skills:
        found_skills.discard("llms")

    if "genai" in found_skills and "generative ai" in found_skills:
        found_skills.discard("genai")

    return found_skills


# ============================================================
# TF-IDF SIMILARITY
# ============================================================

def calculate_text_similarity(
    resume_text: str,
    job_text: str
) -> float:

    if not resume_text or not job_text:
        return 0.0

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000,
    )

    try:
        vectors = vectorizer.fit_transform(
            [resume_text, job_text]
        )

        similarity = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0]

        return float(similarity * 100)

    except ValueError:
        return 0.0


# ============================================================
# CALCULATE MATCH
# ============================================================

def calculate_match(
    resume_text: str,
    job_text: str
) -> Dict[str, Any]:

    resume_text = normalize_text(resume_text)
    job_text = normalize_text(job_text)

    # --------------------------------------------------------
    # Empty input
    # --------------------------------------------------------

    if not resume_text:
        return {
            "match_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "recommendation": "Resume text is empty",
        }

    if not job_text:
        return {
            "match_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "recommendation": "Job description is empty",
        }

    # --------------------------------------------------------
    # Extract technical skills
    # --------------------------------------------------------

    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)

    matched_skills = sorted(
        resume_skills.intersection(job_skills)
    )

    missing_skills = sorted(
        job_skills - resume_skills
    )

    # --------------------------------------------------------
    # Text similarity
    # --------------------------------------------------------

    similarity_score = calculate_text_similarity(
        resume_text,
        job_text
    )

    # --------------------------------------------------------
    # Skill score
    # --------------------------------------------------------

    if job_skills:

        skill_score = (
            len(matched_skills)
            / len(job_skills)
        ) * 100

    else:

        skill_score = similarity_score

    # --------------------------------------------------------
    # Final score
    #
    # Technical skill matching has more weight than
    # general text similarity.
    # --------------------------------------------------------

    if job_skills:

        final_score = (
            skill_score * 0.70
            +
            similarity_score * 0.30
        )

    else:

        final_score = similarity_score

    # Keep score between 0 and 100
    final_score = max(
        0.0,
        min(
            round(final_score, 2),
            100.0
        )
    )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    if final_score >= 80:

        recommendation = "Excellent Match"

    elif final_score >= 65:

        recommendation = "Strong Match"

    elif final_score >= 55:

        recommendation = "Moderate Match"

    elif final_score >= 30:

        recommendation = "Weak Match"

    else:

        recommendation = "Poor Match"

    return {
        "match_score": final_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommendation": recommendation,
    }


# ============================================================
# FASTAPI COMPATIBILITY FUNCTION
# ============================================================

def calculate_match_score(
    resume_text: str,
    job_text: str
) -> Dict[str, Any]:

    result = calculate_match(
        resume_text,
        job_text
    )

    # FastAPI / n8n expects these names
    return {
        "score": result["match_score"],
        "matched_keywords": result["matched_skills"],
        "missing_keywords": result["missing_skills"],
        "recommendation": result["recommendation"],

        # Keep original fields too
        "match_score": result["match_score"],
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
    }