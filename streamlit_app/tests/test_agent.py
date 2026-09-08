"""End-to-end agent test using the local (rule-based) provider only."""
from pathlib import Path

from streamlit_app.agents.router import run_complete_analysis
from streamlit_app.llm.local import LocalLLMProvider


SAMPLE = Path(__file__).resolve().parent.parent / "sample_data"


def test_end_to_end_demo():
    resume = (SAMPLE / "sample_resume.txt").read_text()
    job = (SAMPLE / "job_ai_engineer.txt").read_text()
    a = run_complete_analysis(resume, job, llm=LocalLLMProvider())
    # Sanity assertions
    assert 0 <= a.score.overall <= 100
    assert len(a.matches) > 0
    # Python should be matched
    py = [m for m in a.matches if m.requirement.lower() == "python"]
    assert py, "python requirement not extracted"
    assert py[0].status == "MATCHED"
    # Docker (not on resume) should not be MATCHED
    dk = [m for m in a.matches if m.requirement.lower() == "docker"]
    if dk:
        assert dk[0].status != "MATCHED"
    # Workflow trace present
    assert any("EXTRACT RESUME" in s for s in a.workflow_trace)
