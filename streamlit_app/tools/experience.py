"""Experience comparison."""
from __future__ import annotations
from typing import List

from ..models.schemas import ResumeProfile, JobRequirements, ExperienceComparison


def compare_experience(resume: ResumeProfile, job: JobRequirements) -> List[ExperienceComparison]:
    out: List[ExperienceComparison] = []
    for req in job.experience_requirements or []:
        yrs = resume.years_of_experience or 0.0
        low_req = req.lower()
        candidate_evidence_parts = []
        if resume.experience:
            candidate_evidence_parts.append(f"{len(resume.experience)} professional role(s) listed.")
        if resume.internships:
            candidate_evidence_parts.append(f"{len(resume.internships)} internship(s) listed.")
        if resume.projects:
            candidate_evidence_parts.append(f"{len(resume.projects)} project(s) listed.")
        cand = "; ".join(candidate_evidence_parts) or "No experience details clearly stated."

        needed = job.min_years_experience or 0.0
        if "year" in low_req and needed > 0:
            if yrs >= needed:
                decision, reason = "MATCH", f"Candidate has ~{yrs}y (>= {needed}y required)."
            elif yrs > 0:
                decision, reason = "PARTIAL", f"Candidate has ~{yrs}y (< {needed}y required)."
            else:
                decision, reason = "UNKNOWN", "Years of experience not clearly stated."
        else:
            decision = "PARTIAL" if candidate_evidence_parts else "UNKNOWN"
            reason = "Relevant experience is present; direct professional depth not verifiable."
        out.append(ExperienceComparison(
            requirement=req,
            candidate_evidence=cand,
            decision=decision,  # type: ignore
            reason=reason,
        ))
    return out
