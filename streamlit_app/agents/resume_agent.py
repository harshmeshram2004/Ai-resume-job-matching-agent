"""Resume Extraction Agent."""
from __future__ import annotations
import json

from ..models.schemas import ResumeProfile
from ..llm.base import LLMProvider
from ..tools.extraction import rule_based_resume
from ..utils.helpers import extract_json, normalize_skills
from ..utils.logging import log, warn


RESUME_EXTRACTION_SYSTEM = """You extract structured information from resumes. \
Return ONLY valid JSON matching the requested schema. Do NOT invent facts. \
If a field is not clearly present, use an empty string or empty list."""


RESUME_EXTRACTION_TEMPLATE = """Extract structured information from the following RESUME.

Return STRICT JSON with these keys (all optional, no extras):
{{
  "name": "",
  "email": "",
  "phone": "",
  "summary": "",
  "education": [{{"degree": "", "institution": "", "year": "", "details": ""}}],
  "skills": [],
  "programming_languages": [],
  "frameworks": [],
  "libraries": [],
  "tools": [],
  "databases": [],
  "cloud": [],
  "projects": [{{"name": "", "description": "", "technologies": []}}],
  "experience": [{{"role": "", "company": "", "duration": "", "description": "", "is_internship": false}}],
  "internships": [{{"role": "", "company": "", "duration": "", "description": "", "is_internship": true}}],
  "certifications": [],
  "achievements": [],
  "soft_skills": [],
  "years_of_experience": 0
}}

Rules:
- Do NOT invent skills, projects, or certifications that are not in the resume.
- Copy exact terms from the resume when possible.
- If unsure, leave the field empty.

RESUME:
---
{resume_text}
---
"""


def extract_resume_information(text: str, llm: LLMProvider) -> ResumeProfile:
    """Use LLM if available, else fall back to rule-based extraction."""
    data = None
    if llm and llm.available:
        try:
            raw = llm.complete(RESUME_EXTRACTION_SYSTEM, RESUME_EXTRACTION_TEMPLATE.format(resume_text=text[:12000]))
            data = extract_json(raw)
        except Exception as e:  # pragma: no cover
            warn(f"Resume LLM extraction failed: {e}")
            data = None
    if not data or not isinstance(data, dict):
        log("Using rule-based resume extraction")
        data = rule_based_resume(text)

    # Merge with rule-based to fill gaps
    fallback = rule_based_resume(text)
    for key, val in fallback.items():
        if not data.get(key):
            data[key] = val

    # Normalize skill lists
    for k in ("skills", "programming_languages", "frameworks", "libraries", "tools", "databases", "cloud", "soft_skills"):
        data[k] = normalize_skills(data.get(k, []))

    data["raw_text"] = text
    try:
        return ResumeProfile(**data)
    except Exception as e:
        warn(f"Resume schema validation failed: {e}; using minimal profile")
        minimal = rule_based_resume(text)
        minimal["raw_text"] = text
        return ResumeProfile(**minimal)
