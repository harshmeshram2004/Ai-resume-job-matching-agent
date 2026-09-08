"""Learning roadmap generator."""
from __future__ import annotations
from typing import List

from ..models.schemas import SkillGap, LearningItem


TIMEFRAME_BY_PRIORITY = {
    1: "IMMEDIATE",
    2: "1-2 WEEKS",
    3: "1 MONTH",
}


def generate_learning_roadmap(gaps: List[SkillGap]) -> List[LearningItem]:
    items: List[LearningItem] = []
    for i, g in enumerate(gaps[:8], start=1):
        timeframe = TIMEFRAME_BY_PRIORITY.get(g.priority, "2-3 MONTHS")
        items.append(LearningItem(
            skill=g.skill,
            why_learn=(
                f"'{g.skill}' is listed as a {g.importance.lower().replace('_', ' ')} for this role."
            ),
            job_relevance=g.importance,
            current_level="Not found in resume" if "Not found" in g.current_evidence else "Partial",
            suggested_project=f"Build a small project or exercise that clearly demonstrates {g.skill}.",
            priority=g.priority,
            timeframe=timeframe,  # type: ignore
        ))
    return items
