"""Interview preparation generator."""
from __future__ import annotations
from typing import List

from ..models.schemas import ResumeProfile, JobRequirements, RequirementMatch, SkillGap, InterviewTopic


def generate_interview_topics(
    resume: ResumeProfile,
    job: JobRequirements,
    matches: List[RequirementMatch],
    gaps: List[SkillGap],
) -> List[InterviewTopic]:
    topics: List[InterviewTopic] = []

    # 1. Technical fundamentals from required skills
    for m in matches:
        if m.importance == "REQUIRED" and m.status in ("MATCHED", "PARTIALLY_MATCHED"):
            topics.append(InterviewTopic(
                category="Technical Fundamentals",
                topic=m.requirement,
                why_it_matters=f"'{m.requirement}' is a required skill for this position.",
                preparation_guidance=(
                    f"Revise core concepts of {m.requirement} and be ready to discuss where you used it."
                ),
                example_question=f"Can you walk me through a project where you used {m.requirement}?",
            ))

    # 2. Project deep dives
    for p in resume.projects[:2]:
        if p.name:
            topics.append(InterviewTopic(
                category="Project Questions",
                topic=p.name,
                why_it_matters="Interviewers often deep-dive into resume projects.",
                preparation_guidance=(
                    "Prepare a 90-second summary and be ready to justify design decisions."
                ),
                example_question=f"Walk me through your {p.name} project — what was the hardest part?",
            ))

    # 3. Skill-gap awareness
    for g in gaps[:3]:
        topics.append(InterviewTopic(
            category="Skill-Gap Questions",
            topic=g.skill,
            why_it_matters=(
                f"You may be asked how you plan to ramp up on {g.skill} if hired."
            ),
            preparation_guidance=(
                f"Learn the basics of {g.skill} and prepare an honest, growth-oriented answer."
            ),
            example_question=f"How would you approach learning {g.skill} in your first month?",
        ))

    # 4. Behavioral
    topics.append(InterviewTopic(
        category="Behavioral Topics",
        topic="Ownership & impact",
        why_it_matters="Most interviews include behavioral rounds.",
        preparation_guidance="Prepare 3-4 STAR-format stories from your projects/internships.",
        example_question="Tell me about a time you had to learn something new to unblock a project.",
    ))

    return topics[:12]
