"""Helper utilities: normalization, JSON extraction, tokenization."""
from __future__ import annotations
import json
import re
from typing import Any


SKILL_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "py": "python",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "aws": "aws",
    "gcp": "google cloud platform",
    "k8s": "kubernetes",
    "rest api": "rest api",
    "restful": "rest api",
    "rest apis": "rest api",
    "sql": "sql",
    "nosql": "nosql",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
}


RELATED_SKILLS = {
    "rest api": ["flask", "django", "fastapi", "express", "spring", "node.js"],
    "machine learning": ["scikit-learn", "tensorflow", "pytorch", "xgboost", "keras"],
    "deep learning": ["tensorflow", "pytorch", "keras", "neural network"],
    "natural language processing": ["nltk", "spacy", "transformers", "bert", "gpt"],
    "computer vision": ["opencv", "yolo", "cnn"],
    "cloud": ["aws", "azure", "gcp", "google cloud platform"],
    "containerization": ["docker", "kubernetes", "k8s"],
    "sql": ["postgresql", "mysql", "sqlite", "mssql", "oracle"],
    "nosql": ["mongodb", "cassandra", "redis", "dynamodb"],
}


def normalize_skill(s: str) -> str:
    if not s:
        return ""
    k = s.strip().lower()
    k = re.sub(r"\s+", " ", k)
    return SKILL_ALIASES.get(k, k)


def normalize_skills(items):
    seen = set()
    out = []
    for s in items or []:
        n = normalize_skill(s)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def is_related(a: str, b: str) -> bool:
    a = normalize_skill(a)
    b = normalize_skill(b)
    if a == b:
        return True
    if a in RELATED_SKILLS and b in RELATED_SKILLS[a]:
        return True
    if b in RELATED_SKILLS and a in RELATED_SKILLS[b]:
        return True
    return False


def extract_json(text: str) -> Any:
    """Best-effort JSON extraction from an LLM response."""
    if not text:
        return None
    text = text.strip()
    # Strip code fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    # Find first { ... } or [ ... ]
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            return None
    return None


def find_evidence_snippet(resume_text: str, term: str, window: int = 120) -> str:
    """Return a snippet from the resume that contains the term, or empty string."""
    if not resume_text or not term:
        return ""
    t = term.lower()
    idx = resume_text.lower().find(t)
    if idx == -1:
        # Try related expressions
        for word in t.split():
            if len(word) < 3:
                continue
            idx = resume_text.lower().find(word)
            if idx != -1:
                break
        if idx == -1:
            return ""
    start = max(0, idx - window // 2)
    end = min(len(resume_text), idx + len(term) + window // 2)
    snippet = resume_text[start:end].replace("\n", " ").strip()
    return snippet


def clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))
