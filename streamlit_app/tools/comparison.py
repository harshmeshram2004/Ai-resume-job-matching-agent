"""Multi-job comparison helper."""
from __future__ import annotations
from typing import Dict, List

from ..models.schemas import FinalAnalysis


def compare_multiple_jobs(analyses: Dict[str, FinalAnalysis]) -> Dict[str, dict]:
    """Given a mapping of {job_label: FinalAnalysis}, return a summary dict."""
    summary: Dict[str, dict] = {}
    all_gaps_counter: Dict[str, int] = {}
    for label, a in analyses.items():
        summary[label] = {
            "score": a.score.overall,
            "category": a.score.category,
            "matched": sum(1 for m in a.matches if m.status == "MATCHED"),
            "missing": sum(1 for m in a.matches if m.status == "MISSING"),
            "top_gaps": [g.skill for g in a.skill_gaps[:3]],
            "strongest": [s.skill for s in a.strongest_skills[:3]],
        }
        for g in a.skill_gaps:
            all_gaps_counter[g.skill] = all_gaps_counter.get(g.skill, 0) + 1
    cross_gaps = [k for k, v in sorted(all_gaps_counter.items(), key=lambda x: -x[1]) if v > 1]
    return {"per_job": summary, "cross_cutting_gaps": cross_gaps}
