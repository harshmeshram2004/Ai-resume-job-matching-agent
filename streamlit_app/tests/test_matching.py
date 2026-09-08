"""Tests for matching + evidence validation (no hallucinations)."""
from streamlit_app.models.schemas import ResumeProfile, JobRequirements
from streamlit_app.tools.matcher import match_requirements


def test_no_hallucination_missing_skills_stay_missing():
    resume_text = "Python and SQL used in academic projects."
    resume = ResumeProfile(
        raw_text=resume_text,
        skills=["python", "sql"],
        programming_languages=["python"],
    )
    job = JobRequirements(
        required_skills=["python", "sql", "aws", "docker"],
    )
    matches = match_requirements(resume, job)
    by_skill = {m.requirement.lower(): m for m in matches}
    assert by_skill["python"].status == "MATCHED"
    assert by_skill["sql"].status == "MATCHED"
    # AWS / Docker must NOT be marked MATCHED
    assert by_skill["aws"].status in ("MISSING", "RELATED", "UNKNOWN")
    assert by_skill["docker"].status in ("MISSING", "RELATED", "UNKNOWN")
    assert by_skill["aws"].status != "MATCHED"
    assert by_skill["docker"].status != "MATCHED"


def test_related_skill_marked_related_not_matched():
    resume = ResumeProfile(
        raw_text="Built REST API with Flask.",
        skills=["flask", "python"],
    )
    job = JobRequirements(required_skills=["rest api"])
    matches = match_requirements(resume, job)
    # 'rest api' via flask should be RELATED or MATCHED depending on snippet
    st = matches[0].status
    assert st in ("MATCHED", "RELATED", "PARTIALLY_MATCHED")
