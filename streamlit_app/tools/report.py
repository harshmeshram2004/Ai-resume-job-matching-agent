"""Report generation (Markdown)."""
from __future__ import annotations
from ..models.schemas import FinalAnalysis


def generate_final_report(a: FinalAnalysis) -> str:
    lines = []
    lines.append("=" * 50)
    lines.append("AI RESUME & JOB MATCH ANALYSIS")
    lines.append("")
    lines.append(f"Candidate: {a.resume.name or 'N/A'}")
    lines.append(f"Target Role: {a.job.job_title or 'N/A'}")
    lines.append(f"Overall Match: {a.score.overall}/100")
    lines.append(f"Match Level: {a.score.category}")
    lines.append("=" * 50)
    lines.append("")
    lines.append("## STRONGEST SKILLS")
    for s in a.strongest_skills:
        lines.append(f"- {s.skill} ({s.strength}) — {s.reason}")
    lines.append("")
    lines.append("## REQUIREMENT ANALYSIS")
    for m in a.matches:
        icon = {"MATCHED": "OK", "PARTIALLY_MATCHED": "~", "RELATED": "?", "MISSING": "X", "UNKNOWN": "?"}[m.status]
        lines.append(f"- [{icon}] {m.requirement} — {m.status} ({m.importance}, conf={m.confidence})")
        if m.evidence:
            lines.append(f"    Evidence: {m.evidence[:200]}")
    lines.append("")
    lines.append("## CRITICAL GAPS")
    for g in a.skill_gaps:
        if g.importance == "CRITICAL":
            lines.append(f"- {g.skill} — {g.gap_explanation}")
    lines.append("")
    lines.append("## RESUME IMPROVEMENTS")
    for r in a.resume_recommendations:
        lines.append(f"- [{r.section}] {r.suggestion}")
    lines.append("")
    lines.append("## LEARNING ROADMAP")
    for it in a.learning_roadmap:
        lines.append(f"- ({it.timeframe}) {it.skill} — {it.suggested_project}")
    lines.append("")
    lines.append("## INTERVIEW PREPARATION")
    for t in a.interview_topics:
        lines.append(f"- [{t.category}] {t.topic} — e.g. \"{t.example_question}\"")
    lines.append("")
    lines.append("## WHY THIS SCORE?")
    for k, v in [
        ("Required Skills", a.score.required_skills_score),
        ("Experience", a.score.experience_score),
        ("Projects", a.score.projects_score),
        ("Education", a.score.education_score),
        ("Preferred Skills", a.score.preferred_skills_score),
        ("Other Evidence", a.score.other_evidence_score),
    ]:
        w = a.score.weights.get(k.lower().replace(" ", "_"), 0)
        lines.append(f"- {k}: {v} × {int(w * 100)}%")
    lines.append(f"\nFinal: {a.score.overall}/100")
    lines.append("")
    lines.append(a.score.breakdown_note)
    lines.append("")
    lines.append("Note: This score estimates alignment with the provided job description.")
    lines.append("It is not a prediction of hiring outcome and should support, not replace, human judgment.")
    return "\n".join(lines)
