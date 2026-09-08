"""Unit tests for parsing & rule-based extraction."""
from streamlit_app.tools.resume_parser import parse_txt
from streamlit_app.tools.extraction import rule_based_resume, rule_based_job


def test_parse_txt_basic():
    text = "Hello world"
    assert parse_txt(text.encode("utf-8")) == "Hello world"


def test_rule_based_resume_detects_python():
    r = rule_based_resume("I know Python and SQL. Worked with TensorFlow.")
    assert "python" in r["skills"]
    assert "sql" in r["skills"]
    assert "tensorflow" in r["frameworks"]


def test_rule_based_job_detects_required():
    j = rule_based_job("Requires Python and Docker. 3 years of experience.")
    assert "python" in j["required_skills"]
    assert j["min_years_experience"] == 3.0
