"""Pydantic schemas for the AI Resume & Job Matching Agent."""
from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ---------- Evidence ----------
EvidenceType = Literal["EXPLICIT", "INFERRED", "WEAK", "NOT_FOUND"]


class Evidence(BaseModel):
    skill: str
    evidence: str = ""
    evidence_type: EvidenceType = "NOT_FOUND"
    confidence: float = 0.0
    source: str = "Resume"


# ---------- Resume ----------
class EducationEntry(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""
    details: str = ""


class ExperienceEntry(BaseModel):
    role: str = ""
    company: str = ""
    duration: str = ""
    description: str = ""
    is_internship: bool = False


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)


class ResumeProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    summary: str = ""
    education: List[EducationEntry] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    libraries: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud: List[str] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    internships: List[ExperienceEntry] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    years_of_experience: float = 0.0
    raw_text: str = ""


# ---------- Job ----------
Importance = Literal["REQUIRED", "PREFERRED", "OPTIONAL"]


class JobRequirement(BaseModel):
    text: str
    importance: Importance = "REQUIRED"
    category: str = "skill"  # skill | experience | education | certification | soft_skill | responsibility


class JobRequirements(BaseModel):
    job_title: str = ""
    company: str = ""
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    optional_skills: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    libraries: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud: List[str] = Field(default_factory=list)
    education_requirements: List[str] = Field(default_factory=list)
    experience_requirements: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    domain_knowledge: List[str] = Field(default_factory=list)
    min_years_experience: float = 0.0
    raw_text: str = ""


# ---------- Match Result ----------
MatchStatus = Literal["MATCHED", "PARTIALLY_MATCHED", "RELATED", "MISSING", "UNKNOWN"]


class RequirementMatch(BaseModel):
    requirement: str
    importance: Importance
    status: MatchStatus
    confidence: float = 0.0
    evidence_type: EvidenceType = "NOT_FOUND"
    evidence: str = ""
    explanation: str = ""


class MatchScore(BaseModel):
    overall: float = 0.0
    category: str = ""
    required_skills_score: float = 0.0
    experience_score: float = 0.0
    projects_score: float = 0.0
    education_score: float = 0.0
    preferred_skills_score: float = 0.0
    other_evidence_score: float = 0.0
    weights: dict = Field(default_factory=dict)
    breakdown_note: str = ""


# ---------- Recommendations ----------
class SkillGap(BaseModel):
    skill: str
    importance: Literal["CRITICAL", "IMPORTANT", "NICE_TO_HAVE"]
    job_requirement: str = ""
    current_evidence: str = "Not found in the provided resume."
    gap_explanation: str = ""
    learning_recommendation: str = ""
    priority: int = 1


class StrongestSkill(BaseModel):
    skill: str
    evidence: str
    job_relevance: str
    strength: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    reason: str = ""


class ResumeRecommendation(BaseModel):
    section: str
    issue: str
    suggestion: str


class LearningItem(BaseModel):
    skill: str
    why_learn: str
    job_relevance: str
    current_level: str
    suggested_project: str
    priority: int
    timeframe: Literal["IMMEDIATE", "1-2 WEEKS", "1 MONTH", "2-3 MONTHS"]


class InterviewTopic(BaseModel):
    category: str
    topic: str
    why_it_matters: str
    preparation_guidance: str
    example_question: str


class ExperienceComparison(BaseModel):
    requirement: str
    candidate_evidence: str
    decision: Literal["MATCH", "PARTIAL", "MISS", "UNKNOWN"]
    reason: str


# ---------- Final report ----------
class FinalAnalysis(BaseModel):
    resume: ResumeProfile
    job: JobRequirements
    matches: List[RequirementMatch]
    score: MatchScore
    strongest_skills: List[StrongestSkill]
    skill_gaps: List[SkillGap]
    experience_comparisons: List[ExperienceComparison]
    resume_recommendations: List[ResumeRecommendation]
    learning_roadmap: List[LearningItem]
    interview_topics: List[InterviewTopic]
    workflow_trace: List[str] = Field(default_factory=list)
