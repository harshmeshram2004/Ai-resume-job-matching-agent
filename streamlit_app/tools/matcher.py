"""Matching engine: compare structured resume vs structured job requirements."""
from __future__ import annotations
from typing import List

from ..models.schemas import ResumeProfile, JobRequirements, RequirementMatch, Importance
from .evidence_validator import validate_skill_evidence, evidence_to_status


def _iter_requirements(job: JobRequirements):
    for s in job.required_skills:
        yield s, "REQUIRED", "skill"
    for s in job.preferred_skills:
        yield s, "PREFERRED", "skill"
    for s in job.optional_skills:
        yield s, "OPTIONAL", "skill"
    for e in job.experience_requirements:
        yield e, "REQUIRED", "experience"
    for e in job.education_requirements:
        yield e, "PREFERRED", "education"
    for c in job.certifications:
        yield c, "PREFERRED", "certification"


def match_requirements(resume: ResumeProfile, job: JobRequirements) -> List[RequirementMatch]:
    matches: List[RequirementMatch] = []
    resume_all_skills = (
        (resume.skills or [])
        + (resume.programming_languages or [])
        + (resume.frameworks or [])
        + (resume.libraries or [])
        + (resume.tools or [])
        + (resume.databases or [])
        + (resume.cloud or [])
    )
    for req, importance, category in _iter_requirements(job):
        if category in ("skill", "certification", "education"):
            ev = validate_skill_evidence(req, resume.raw_text, resume_all_skills)
            status, conf = evidence_to_status(ev)
            explanation = _explain(ev, status, category, importance)
            matches.append(RequirementMatch(
                requirement=req,
                importance=importance,  # type: ignore
                status=status,  # type: ignore
                confidence=round(conf, 2),
                evidence_type=ev.evidence_type,
                evidence=ev.evidence,
                explanation=explanation,
            ))
        elif category == "experience":
            m = _match_experience_requirement(req, resume, job)
            matches.append(m)
    return matches


def _explain(ev, status, category, importance) -> str:
    if status == "MATCHED":
        return f"Explicitly demonstrated in resume; category={category}, importance={importance}."
    if status == "PARTIALLY_MATCHED":
        return f"Partial evidence found in resume; treat with caution ({category})."
    if status == "RELATED":
        return "No direct evidence, but a related skill is present. Not equivalent to direct experience."
    if status == "MISSING":
        return "Not found in the provided resume."
    return "Insufficient information."


def _match_experience_requirement(req: str, resume: ResumeProfile, job: JobRequirements) -> RequirementMatch:
    yrs = resume.years_of_experience or 0.0
    needed = job.min_years_experience or 0.0
    if needed <= 0 and yrs <= 0:
        return RequirementMatch(
            requirement=req,
            importance="REQUIRED",
            status="UNKNOWN",
            confidence=0.3,
            evidence_type="WEAK",
            evidence="Years of experience not clearly stated in the resume.",
            explanation="Insufficient information to verify duration of experience.",
        )
    if needed <= 0:
        return RequirementMatch(
            requirement=req,
            importance="REQUIRED",
            status="PARTIALLY_MATCHED",
            confidence=0.6,
            evidence_type="INFERRED",
            evidence=f"Resume suggests ~{yrs} year(s) of experience.",
            explanation="Job does not state a strict year requirement; candidate has some experience.",
        )
    if yrs >= needed:
        return RequirementMatch(
            requirement=req,
            importance="REQUIRED",
            status="MATCHED",
            confidence=0.9,
            evidence_type="EXPLICIT",
            evidence=f"Resume indicates ~{yrs} year(s) of experience (>= {needed}).",
            explanation="Meets or exceeds the stated years of experience requirement.",
        )
    return RequirementMatch(
        requirement=req,
        importance="REQUIRED",
        status="PARTIALLY_MATCHED",
        confidence=0.5,
        evidence_type="WEAK",
        evidence=f"Resume indicates ~{yrs} year(s) of experience; job asks for {needed}+.",
        explanation="Some relevant experience but below the stated duration threshold.",
    )
