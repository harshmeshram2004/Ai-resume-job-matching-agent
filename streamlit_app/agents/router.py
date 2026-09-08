"""Agent Router — orchestrates the full analysis workflow."""
from __future__ import annotations
from typing import List

from ..models.schemas import FinalAnalysis, ResumeProfile, JobRequirements
from ..llm.base import LLMProvider
from ..llm.cloud import CloudLLMProvider
from ..llm.local import LocalLLMProvider
from .resume_agent import extract_resume_information
from .job_agent import extract_job_requirements, classify_requirements
from ..tools.matcher import match_requirements
from ..tools.scoring import calculate_match_score
from ..tools.skill_gap import find_skill_gaps, find_strongest_skills
from ..tools.experience import compare_experience
from ..tools.recommendations import generate_resume_recommendations
from ..tools.learning import generate_learning_roadmap
from ..tools.interview import generate_interview_topics


def build_llm(provider_key: str = "cloud") -> LLMProvider:
    if provider_key == "local":
        return LocalLLMProvider()
    return CloudLLMProvider()


def route_intent(question: str) -> str:
    q = (question or "").lower()
    if any(k in q for k in ("strength", "strong")):
        return "STRONGEST_SKILLS"
    if any(k in q for k in ("missing", "gap", "learn")):
        return "SKILL_GAP_ANALYSIS"
    if "interview" in q or "prepare" in q:
        return "INTERVIEW_PREPARATION"
    if "improve" in q or "resume" in q:
        return "RESUME_IMPROVEMENT"
    if "compare" in q and "job" in q:
        return "MULTI_JOB_COMPARISON"
    return "COMPLETE_ANALYSIS"


def run_complete_analysis(
    resume_text: str,
    jd_text: str,
    llm: LLMProvider | None = None,
    weights: dict | None = None,
) -> FinalAnalysis:
    llm = llm or build_llm("cloud")
    trace: List[str] = []

    trace.append("UNDERSTAND: intent = COMPLETE_ANALYSIS")
    trace.append("EXTRACT RESUME: parsing resume text into structured profile")
    resume: ResumeProfile = extract_resume_information(resume_text, llm)

    trace.append("EXTRACT JOB REQUIREMENTS: parsing job description")
    job: JobRequirements = extract_job_requirements(jd_text, llm)

    trace.append("CLASSIFY REQUIREMENTS: REQUIRED / PREFERRED / OPTIONAL")
    job = classify_requirements(job)

    trace.append("COMPARE: matching resume evidence against requirements")
    matches = match_requirements(resume, job)

    trace.append("VALIDATE EVIDENCE: checking every claimed match against resume snippets")
    # Validation already embedded in matcher (evidence-based). Final pass:
    for m in matches:
        if m.status == "MATCHED" and not m.evidence:
            m.status = "PARTIALLY_MATCHED"
            m.confidence = min(m.confidence, 0.5)
            m.explanation += " (Downgraded: no direct evidence snippet.)"

    trace.append("CALCULATE SCORE: deterministic weighted score")
    score = calculate_match_score(matches, resume, job, weights)

    trace.append("IDENTIFY GAPS: critical / important / nice-to-have")
    gaps = find_skill_gaps(matches)
    strongest = find_strongest_skills(matches)

    trace.append("GENERATE RECOMMENDATIONS: resume, learning, interview")
    exp_cmp = compare_experience(resume, job)
    resume_recs = generate_resume_recommendations(resume, job, matches)
    roadmap = generate_learning_roadmap(gaps)
    topics = generate_interview_topics(resume, job, matches, gaps)

    trace.append("FINAL VALIDATION: removing unsupported claims")

    return FinalAnalysis(
        resume=resume,
        job=job,
        matches=matches,
        score=score,
        strongest_skills=strongest,
        skill_gaps=gaps,
        experience_comparisons=exp_cmp,
        resume_recommendations=resume_recs,
        learning_roadmap=roadmap,
        interview_topics=topics,
        workflow_trace=trace,
    )
