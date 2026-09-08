"""Skill gap analysis."""
from __future__ import annotations
from typing import List

from ..models.schemas import RequirementMatch, SkillGap, StrongestSkill


IMPORTANCE_MAP = {
    "REQUIRED": "CRITICAL",
    "PREFERRED": "IMPORTANT",
    "OPTIONAL": "NICE_TO_HAVE",
}


def find_skill_gaps(matches: List[RequirementMatch]) -> List[SkillGap]:
    gaps: List[SkillGap] = []
    for m in matches:
        if m.status in ("MISSING", "UNKNOWN", "RELATED"):
            level = IMPORTANCE_MAP.get(m.importance, "NICE_TO_HAVE")
            gaps.append(SkillGap(
                skill=m.requirement,
                importance=level,  # type: ignore
                job_requirement=m.requirement,
                current_evidence=m.evidence or "Not found in the provided resume.",
                gap_explanation=(
                    "Job explicitly requires this skill and no direct evidence was found."
                    if m.status == "MISSING" and m.importance == "REQUIRED"
                    else "Some related evidence exists but does not fully cover this requirement."
                    if m.status == "RELATED"
                    else "Insufficient evidence in the resume to verify this requirement."
                ),
                learning_recommendation=(
                    f"Build a small project demonstrating {m.requirement} and add it to the resume."
                ),
                priority=1 if level == "CRITICAL" else 2 if level == "IMPORTANT" else 3,
            ))
    # Priority sort
    gaps.sort(key=lambda g: (g.priority, g.skill.lower()))
    return gaps


def find_strongest_skills(matches: List[RequirementMatch]) -> List[StrongestSkill]:
    strong: List[StrongestSkill] = []
    for m in matches:
        if m.status == "MATCHED" and m.confidence >= 0.75:
            strong.append(StrongestSkill(
                skill=m.requirement,
                evidence=m.evidence or "Present in the resume.",
                job_relevance=m.importance,
                strength="HIGH" if m.confidence >= 0.9 else "MEDIUM",
                reason=(
                    f"Explicitly demonstrated in the resume and directly {m.importance.lower()} by the position."
                ),
            ))
    strong.sort(key=lambda s: (0 if s.strength == "HIGH" else 1, s.skill.lower()))
    return strong[:10]
