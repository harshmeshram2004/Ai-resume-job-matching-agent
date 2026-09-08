"""App configuration."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_ENV = Path("/app/backend/.env")
if BACKEND_ENV.exists():
    load_dotenv(BACKEND_ENV)

APP_ENV = Path(__file__).resolve().parent.parent / ".env"
if APP_ENV.exists():
    load_dotenv(APP_ENV)

try:
    import streamlit as st
    if hasattr(st, "secrets") and "EMERGENT_LLM_KEY" in st.secrets:
        os.environ["EMERGENT_LLM_KEY"] = st.secrets["EMERGENT_LLM_KEY"]
except Exception:
    pass


DEFAULT_WEIGHTS = {
    "required_skills": 0.40,
    "experience": 0.25,
    "projects": 0.15,
    "education": 0.10,
    "preferred_skills": 0.05,
    "other_evidence": 0.05,
}


SCORE_LABELS = [
    (90, "Excellent Match"),
    (80, "Strong Match"),
    (70, "Good Match"),
    (60, "Moderate Match"),
    (40, "Weak Match"),
    (0, "Low Match"),
]


def get_llm_key() -> str:
    return os.environ.get("EMERGENT_LLM_KEY", "")


def get_provider_defaults():
    return {
        "provider": os.environ.get("LLM_PROVIDER", "openai"),
        "model": os.environ.get("MODEL_NAME", "gpt-5.4"),
    }