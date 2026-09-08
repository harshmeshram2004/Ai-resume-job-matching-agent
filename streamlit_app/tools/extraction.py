"""Rule-based extraction fallback used when the LLM is unavailable or fails."""
from __future__ import annotations
import re
from typing import List


COMMON_LANGS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "kotlin", "swift", "scala", "r", "matlab", "bash", "sql",
]
COMMON_FRAMEWORKS = [
    "react", "angular", "vue", "next.js", "django", "flask", "fastapi", "spring",
    "express", "node.js", "rails", ".net", "laravel", "tensorflow", "pytorch",
    "keras", "scikit-learn", "sklearn", "xgboost", "huggingface", "transformers",
    "langchain",
]
COMMON_TOOLS = [
    "git", "docker", "kubernetes", "k8s", "jenkins", "terraform", "ansible",
    "airflow", "kafka", "spark", "hadoop", "linux", "jira", "postman",
]
COMMON_DBS = [
    "mysql", "postgresql", "mongodb", "sqlite", "redis", "cassandra",
    "dynamodb", "elasticsearch", "oracle", "mssql", "neo4j",
]
COMMON_CLOUD = ["aws", "azure", "gcp", "google cloud", "heroku", "vercel", "netlify"]
COMMON_SOFT = [
    "communication", "leadership", "teamwork", "problem solving", "collaboration",
    "adaptability", "time management", "critical thinking", "creativity",
]


def _find_in_text(text: str, vocab: List[str]) -> List[str]:
    found = []
    low = text.lower()
    for term in vocab:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(term) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, low):
            found.append(term)
    # de-dup preserving order
    seen = set()
    out = []
    for t in found:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def extract_name(text: str) -> str:
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^[A-Z][a-zA-Z\.\-']+(?:\s+[A-Z][a-zA-Z\.\-']+){1,3}$", line):
            return line
        return line[:60]
    return ""


def extract_email(text: str) -> str:
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else ""


def extract_phone(text: str) -> str:
    m = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text)
    return m.group(1).strip() if m else ""


def extract_years_experience(text: str) -> float:
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s*(?:of)?\s*experience", text.lower())
    if matches:
        try:
            return max(float(x) for x in matches)
        except Exception:
            return 0.0
    return 0.0


def rule_based_resume(text: str) -> dict:
    langs = _find_in_text(text, COMMON_LANGS)
    frameworks = _find_in_text(text, COMMON_FRAMEWORKS)
    tools = _find_in_text(text, COMMON_TOOLS)
    dbs = _find_in_text(text, COMMON_DBS)
    cloud = _find_in_text(text, COMMON_CLOUD)
    soft = _find_in_text(text, COMMON_SOFT)
    all_skills = list(dict.fromkeys(langs + frameworks + tools + dbs + cloud))
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "summary": "",
        "education": [],
        "skills": all_skills,
        "programming_languages": langs,
        "frameworks": frameworks,
        "libraries": [],
        "tools": tools,
        "databases": dbs,
        "cloud": cloud,
        "projects": [],
        "experience": [],
        "internships": [],
        "certifications": [],
        "achievements": [],
        "soft_skills": soft,
        "years_of_experience": extract_years_experience(text),
    }


def rule_based_job(text: str) -> dict:
    langs = _find_in_text(text, COMMON_LANGS)
    frameworks = _find_in_text(text, COMMON_FRAMEWORKS)
    tools = _find_in_text(text, COMMON_TOOLS)
    dbs = _find_in_text(text, COMMON_DBS)
    cloud = _find_in_text(text, COMMON_CLOUD)
    soft = _find_in_text(text, COMMON_SOFT)
    # Split required vs preferred based on section keywords
    low = text.lower()
    required_skills = list(dict.fromkeys(langs + frameworks + tools + dbs + cloud))
    preferred_skills = []
    # Very naive title
    title = ""
    first_lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if first_lines:
        title = first_lines[0][:80]
    yrs = 0.0
    m = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", low)
    if m:
        try:
            yrs = float(m.group(1))
        except Exception:
            yrs = 0.0
    return {
        "job_title": title,
        "company": "",
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "optional_skills": [],
        "programming_languages": langs,
        "frameworks": frameworks,
        "libraries": [],
        "tools": tools,
        "databases": dbs,
        "cloud": cloud,
        "education_requirements": [],
        "experience_requirements": [],
        "certifications": [],
        "responsibilities": [],
        "soft_skills": soft,
        "domain_knowledge": [],
        "min_years_experience": yrs,
    }
