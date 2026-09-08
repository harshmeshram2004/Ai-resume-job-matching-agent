"""Deterministic explainable scoring engine."""
from __future__ import annotations
from typing import List

from ..models.schemas import RequirementMatch, MatchScore, ResumeProfile, JobRequirements
from ..utils.config import DEFAULT_WEIGHTS, SCORE_LABELS
from ..utils.helpers import clamp


STATUS_POINTS = {
    "MATCHED": 1.0,
    "PARTIALLY_MATCHED": 0.6,
    "RELATED": 0.3,
    "UNKNOWN": 0.15,
    "MISSING": 0.0,
}


def _avg_score(matches: List[RequirementMatch]) -> float:
    if not matches:
        return 0.0
    total = sum(STATUS_POINTS.get(m.status, 0.0) for m in matches) / len(matches)
    return round(total * 100, 2)


def _experience_score(resume: ResumeProfile, job: JobRequirements) -> float:
    needed = job.min_years_experience or 0.0
    have = resume.years_of_experience or 0.0
    if needed <= 0:
        # If years unknown, base on experience/internship count
        n = len(resume.experience) + len(resume.internships)
        if n == 0:
            return 40.0
        return clamp(50 + n * 15, 0, 95)
    if have <= 0:
        return 30.0
    if have >= needed:
        return 100.0
    return clamp((have / needed) * 100.0, 0, 100)


def _projects_score(resume: ResumeProfile, job: JobRequirements) -> float:
    n = len(resume.projects)
    if n == 0:
        return 30.0
    # Reward alignment of project techs with required skills
    req_low = {s.lower() for s in job.required_skills + job.preferred_skills}
    hits = 0
    for p in resume.projects:
        for t in (p.technologies or []):
            if t.lower() in req_low:
                hits += 1
    base = clamp(50 + n * 10, 0, 90)
    bonus = clamp(hits * 5, 0, 30)
    return clamp(base + bonus - 20 if hits == 0 else base + bonus, 0, 100)


def _education_score(resume: ResumeProfile, job: JobRequirements) -> float:
    if not job.education_requirements:
        return 100.0 if resume.education else 70.0
    if not resume.education:
        return 40.0
    # Simple text overlap
    text = " ".join(f"{e.degree} {e.details}" for e in resume.education).lower()
    hits = sum(1 for req in job.education_requirements if any(w in text for w in req.lower().split() if len(w) > 3))
    if hits == 0:
        return 55.0
    return clamp(70 + hits * 10, 0, 100)


def calculate_match_score(
    matches: List[RequirementMatch],
    resume: ResumeProfile,
    job: JobRequirements,
    weights: dict | None = None,
) -> MatchScore:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    required = [m for m in matches if m.importance == "REQUIRED"]
    preferred = [m for m in matches if m.importance == "PREFERRED"]
    other = [m for m in matches if m.importance == "OPTIONAL"]

    required_score = _avg_score(required) if required else 60.0
    preferred_score = _avg_score(preferred) if preferred else 60.0
    other_score = _avg_score(other) if other else 70.0

    exp_score = _experience_score(resume, job)
    proj_score = _projects_score(resume, job)
    edu_score = _education_score(resume, job)

    overall = (
        required_score * w["required_skills"]
        + exp_score * w["experience"]
        + proj_score * w["projects"]
        + edu_score * w["education"]
        + preferred_score * w["preferred_skills"]
        + other_score * w["other_evidence"]
    )
    overall = round(clamp(overall, 0, 100), 1)

    category = "Low Match"
    for threshold, label in SCORE_LABELS:
        if overall >= threshold:
            category = label
            break

    return MatchScore(
        overall=overall,
        category=category,
        required_skills_score=round(required_score, 1),
        experience_score=round(exp_score, 1),
        projects_score=round(proj_score, 1),
        education_score=round(edu_score, 1),
        preferred_skills_score=round(preferred_score, 1),
        other_evidence_score=round(other_score, 1),
        weights=w,
        breakdown_note=(
            "Score is computed deterministically by code — the LLM does not choose the number."
        ),
    )
