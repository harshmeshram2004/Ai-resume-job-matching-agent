"""Job Description Extraction Agent + requirement classifier."""
from __future__ import annotations

from ..models.schemas import JobRequirements
from ..llm.base import LLMProvider
from ..tools.extraction import rule_based_job
from ..utils.helpers import extract_json, normalize_skills
from ..utils.logging import log, warn


JD_EXTRACTION_SYSTEM = """You extract structured requirements from job descriptions. \
Return ONLY valid JSON. Do not invent skills that are not mentioned."""


JD_TEMPLATE = """Extract structured requirements from the following JOB DESCRIPTION.

Return STRICT JSON with these keys:
{{
  "job_title": "",
  "company": "",
  "required_skills": [],
  "preferred_skills": [],
  "optional_skills": [],
  "programming_languages": [],
  "frameworks": [],
  "libraries": [],
  "tools": [],
  "databases": [],
  "cloud": [],
  "education_requirements": [],
  "experience_requirements": [],
  "certifications": [],
  "responsibilities": [],
  "soft_skills": [],
  "domain_knowledge": [],
  "min_years_experience": 0
}}

Classification rules:
- required_skills: mentioned with "must", "required", "need", or listed as hard requirement.
- preferred_skills: "preferred", "plus", "nice to have", "bonus".
- optional_skills: "would be beneficial", "optional".
- Do NOT duplicate a skill across required/preferred.

JOB DESCRIPTION:
---
{jd_text}
---
"""


def extract_job_requirements(text: str, llm: LLMProvider) -> JobRequirements:
    data = None
    if llm and llm.available:
        try:
            raw = llm.complete(JD_EXTRACTION_SYSTEM, JD_TEMPLATE.format(jd_text=text[:10000]))
            data = extract_json(raw)
        except Exception as e:  # pragma: no cover
            warn(f"Job LLM extraction failed: {e}")
            data = None
    if not data or not isinstance(data, dict):
        log("Using rule-based job extraction")
        data = rule_based_job(text)

    fallback = rule_based_job(text)
    for key, val in fallback.items():
        if not data.get(key):
            data[key] = val

    for k in ("required_skills", "preferred_skills", "optional_skills", "programming_languages",
              "frameworks", "libraries", "tools", "databases", "cloud", "soft_skills"):
        data[k] = normalize_skills(data.get(k, []))

    # Ensure no overlap: required beats preferred beats optional
    req_set = set(data["required_skills"])
    data["preferred_skills"] = [s for s in data["preferred_skills"] if s not in req_set]
    pref_set = set(data["preferred_skills"])
    data["optional_skills"] = [s for s in data["optional_skills"] if s not in req_set and s not in pref_set]

    data["raw_text"] = text
    try:
        return JobRequirements(**data)
    except Exception as e:
        warn(f"Job schema validation failed: {e}; using minimal requirements")
        minimal = rule_based_job(text)
        minimal["raw_text"] = text
        return JobRequirements(**minimal)


def classify_requirements(job: JobRequirements) -> JobRequirements:
    """Requirement classification is already done in extraction; kept as a hook
    so the workflow trace can show a distinct step."""
    return job
