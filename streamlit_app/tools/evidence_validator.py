"""Evidence validation & extraction against raw resume text."""
from __future__ import annotations
from typing import Tuple

from ..models.schemas import Evidence, EvidenceType
from ..utils.helpers import find_evidence_snippet, normalize_skill, is_related


def validate_skill_evidence(skill: str, resume_text: str, resume_skills: list) -> Evidence:
    """Return Evidence for a given required skill from the raw resume text and
    normalized skill list. Never invents evidence."""
    norm = normalize_skill(skill)
    resume_skills_norm = {normalize_skill(s) for s in resume_skills}

    # 1) Exact skill list match with a supporting snippet from resume
    if norm in resume_skills_norm:
        snippet = find_evidence_snippet(resume_text, skill) or find_evidence_snippet(resume_text, norm)
        if snippet:
            return Evidence(skill=skill, evidence=snippet, evidence_type="EXPLICIT", confidence=0.95)
        # Skill mentioned in structured list but not narratively - still explicit but weaker
        return Evidence(
            skill=skill,
            evidence=f"Listed in the candidate's skills section: {norm}",
            evidence_type="EXPLICIT",
            confidence=0.8,
        )

    # 2) Snippet found in raw text (mentioned in projects/experience narrative)
    snippet = find_evidence_snippet(resume_text, skill)
    if snippet and norm and norm in snippet.lower():
        return Evidence(skill=skill, evidence=snippet, evidence_type="EXPLICIT", confidence=0.85)

    # 3) Related-skill inference (no direct evidence)
    for rs in resume_skills_norm:
        if is_related(skill, rs):
            snippet_r = find_evidence_snippet(resume_text, rs)
            return Evidence(
                skill=skill,
                evidence=snippet_r or f"Related skill present: {rs}",
                evidence_type="INFERRED",
                confidence=0.55,
                source="Resume (related skill)",
            )

    # 4) Nothing found
    return Evidence(skill=skill, evidence="", evidence_type="NOT_FOUND", confidence=0.0)


def evidence_to_status(ev: Evidence) -> Tuple[str, float]:
    """Map evidence to a match status + confidence."""
    if ev.evidence_type == "EXPLICIT" and ev.confidence >= 0.8:
        return "MATCHED", ev.confidence
    if ev.evidence_type == "EXPLICIT":
        return "PARTIALLY_MATCHED", ev.confidence
    if ev.evidence_type == "INFERRED":
        return "RELATED", ev.confidence
    if ev.evidence_type == "WEAK":
        return "PARTIALLY_MATCHED", ev.confidence
    return "MISSING", 0.0
