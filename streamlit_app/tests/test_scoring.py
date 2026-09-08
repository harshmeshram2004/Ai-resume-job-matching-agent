"""Tests for deterministic scoring."""
from streamlit_app.models.schemas import RequirementMatch, ResumeProfile, JobRequirements
from streamlit_app.tools.scoring import calculate_match_score


def _mk(status, importance="REQUIRED", conf=0.9):
    return RequirementMatch(
        requirement="skill", importance=importance, status=status,
        confidence=conf, evidence_type="EXPLICIT", evidence="ev", explanation="",
    )


def test_scoring_deterministic():
    matches = [_mk("MATCHED"), _mk("MATCHED"), _mk("MISSING")]
    resume = ResumeProfile(years_of_experience=2, projects=[], skills=["python"])
    job = JobRequirements(min_years_experience=2, required_skills=["python"])
    s1 = calculate_match_score(matches, resume, job)
    s2 = calculate_match_score(matches, resume, job)
    assert s1.overall == s2.overall
    assert 0 <= s1.overall <= 100


def test_score_missing_lowers_score():
    all_matched = [_mk("MATCHED") for _ in range(3)]
    all_missing = [_mk("MISSING") for _ in range(3)]
    resume = ResumeProfile(years_of_experience=2)
    job = JobRequirements(min_years_experience=2, required_skills=["a", "b", "c"])
    s_m = calculate_match_score(all_matched, resume, job).overall
    s_x = calculate_match_score(all_missing, resume, job).overall
    assert s_m > s_x
