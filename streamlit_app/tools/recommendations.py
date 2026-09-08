"""Resume improvement recommendations."""
from __future__ import annotations
from typing import List

from ..models.schemas import ResumeProfile, JobRequirements, ResumeRecommendation, RequirementMatch


def analyze_resume_sections(resume: ResumeProfile, job: JobRequirements) -> List[ResumeRecommendation]:
    recs: List[ResumeRecommendation] = []

    if not resume.summary:
        recs.append(ResumeRecommendation(
            section="Professional Summary",
            issue="No summary section found.",
            suggestion=(
                f"Add a 2-3 line summary highlighting your top skills relevant to '{job.job_title or 'the target role'}'."
            ),
        ))
    elif len(resume.summary) < 60:
        recs.append(ResumeRecommendation(
            section="Professional Summary",
            issue="Summary is very short.",
            suggestion="Expand to 2-3 lines that reference the target role and your strongest evidence.",
        ))

    if not resume.projects:
        recs.append(ResumeRecommendation(
            section="Projects",
            issue="No projects listed.",
            suggestion="Add 1-2 projects showcasing skills the job requires; include technologies used.",
        ))
    else:
        for p in resume.projects:
            if not p.description or len(p.description) < 40:
                recs.append(ResumeRecommendation(
                    section=f"Project: {p.name or 'Unnamed'}",
                    issue="Project description is thin.",
                    suggestion=(
                        "Describe the problem, your approach, and outcomes. "
                        "If you have measurable results, consider adding them."
                    ),
                ))
                break

    if not resume.certifications and job.certifications:
        recs.append(ResumeRecommendation(
            section="Certifications",
            issue="Job mentions certifications; none listed on your resume.",
            suggestion="Add relevant certifications if you already hold them; otherwise plan to earn one.",
        ))

    if not resume.email:
        recs.append(ResumeRecommendation(
            section="Contact Info",
            issue="No email detected in the resume text.",
            suggestion="Ensure your email is clearly visible at the top of the resume.",
        ))

    return recs


def generate_resume_recommendations(
    resume: ResumeProfile,
    job: JobRequirements,
    matches: List[RequirementMatch],
) -> List[ResumeRecommendation]:
    recs = analyze_resume_sections(resume, job)
    # Add recommendations for missing critical skills
    for m in matches:
        if m.status == "MISSING" and m.importance == "REQUIRED":
            recs.append(ResumeRecommendation(
                section="Skills",
                issue=f"Required skill '{m.requirement}' not found in resume.",
                suggestion=(
                    f"If you have any exposure to {m.requirement}, add it clearly in your skills section "
                    "and reference where you used it in a project or experience."
                ),
            ))
    # Dedup
    seen = set()
    out = []
    for r in recs:
        key = (r.section, r.issue)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
