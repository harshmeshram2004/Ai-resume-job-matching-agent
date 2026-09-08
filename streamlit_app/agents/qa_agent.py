"""Follow-up Q&A Agent — grounded in the FinalAnalysis object."""
from __future__ import annotations

from ..models.schemas import FinalAnalysis
from ..llm.base import LLMProvider


QA_SYSTEM = """You are a helpful career agent answering questions about a candidate's \
resume vs a job. Use ONLY the analysis JSON provided. NEVER invent skills, evidence, \
or experience. If the answer is not in the analysis, say so."""


def _context(a: FinalAnalysis) -> str:
    parts = [
        f"Candidate: {a.resume.name}",
        f"Target role: {a.job.job_title}",
        f"Overall score: {a.score.overall}/100 ({a.score.category})",
        "Score breakdown:",
        f"  Required Skills: {a.score.required_skills_score}",
        f"  Experience: {a.score.experience_score}",
        f"  Projects: {a.score.projects_score}",
        f"  Education: {a.score.education_score}",
        f"  Preferred Skills: {a.score.preferred_skills_score}",
        "",
        "Matches:",
    ]
    for m in a.matches:
        parts.append(f"  - {m.requirement} [{m.importance}] -> {m.status} (conf={m.confidence})")
    parts.append("")
    parts.append("Strongest skills:")
    for s in a.strongest_skills:
        parts.append(f"  - {s.skill} ({s.strength}): {s.reason}")
    parts.append("")
    parts.append("Skill gaps:")
    for g in a.skill_gaps:
        parts.append(f"  - {g.skill} [{g.importance}]: {g.gap_explanation}")
    return "\n".join(parts)


def _rule_based_answer(analysis: FinalAnalysis, question: str) -> str:
    q = question.lower()
    if "score" in q or "why" in q and str(int(analysis.score.overall)) in q:
        s = analysis.score
        return (
            f"Your overall score is {s.overall}/100 ({s.category}).\n"
            f"- Required Skills: {s.required_skills_score} × {int(s.weights.get('required_skills',0)*100)}%\n"
            f"- Experience: {s.experience_score} × {int(s.weights.get('experience',0)*100)}%\n"
            f"- Projects: {s.projects_score} × {int(s.weights.get('projects',0)*100)}%\n"
            f"- Education: {s.education_score} × {int(s.weights.get('education',0)*100)}%\n"
            f"- Preferred Skills: {s.preferred_skills_score} × {int(s.weights.get('preferred_skills',0)*100)}%\n"
            f"- Other Evidence: {s.other_evidence_score} × {int(s.weights.get('other_evidence',0)*100)}%\n"
            f"\n{s.breakdown_note}"
        )
    if "missing" in q or "gap" in q or "learn" in q:
        if not analysis.skill_gaps:
            return "No critical gaps were detected in the provided resume."
        top = analysis.skill_gaps[:5]
        return "Top gaps to address:\n" + "\n".join(
            f"- {g.skill} ({g.importance}): {g.gap_explanation}" for g in top
        )
    if "strong" in q or "strength" in q:
        if not analysis.strongest_skills:
            return "No strongly-matched required skills were detected."
        return "Your strongest skills for this role:\n" + "\n".join(
            f"- {s.skill} ({s.strength}): {s.reason}" for s in analysis.strongest_skills
        )
    if "ready" in q or "apply" in q:
        return (
            f"Your match is {analysis.score.overall}/100 ({analysis.score.category}). "
            f"Address the top gaps below before applying:\n" +
            "\n".join(f"- {g.skill}" for g in analysis.skill_gaps[:5])
        )
    if "interview" in q or "prepare" in q:
        return "Interview topics you should prepare:\n" + "\n".join(
            f"- [{t.category}] {t.topic}" for t in analysis.interview_topics[:8]
        )
    return (
        "Ask about your score, strengths, gaps, learning roadmap, or interview prep. "
        "All answers are grounded in the analysis of your resume and this job."
    )


def answer_followup_question(analysis: FinalAnalysis, question: str, llm: LLMProvider) -> str:
    if llm and llm.available:
        try:
            ctx = _context(analysis)
            resp = llm.complete(
                QA_SYSTEM,
                f"Analysis:\n{ctx}\n\nUser question: {question}\n\nAnswer briefly and cite evidence from the analysis only.",
            )
            return resp.strip() if isinstance(resp, str) else str(resp)
        except Exception:
            pass
    return _rule_based_answer(analysis, question)
