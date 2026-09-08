"""AI Resume & Job Matching Agent — Streamlit UI."""
from __future__ import annotations
import io
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Local package imports (streamlit_app is a package)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamlit_app.agents.router import run_complete_analysis, build_llm, route_intent
from streamlit_app.agents.qa_agent import answer_followup_question
from streamlit_app.tools.resume_parser import parse_resume, is_scanned_pdf
from streamlit_app.tools.job_parser import parse_job_file
from streamlit_app.tools.report import generate_final_report
from streamlit_app.tools.comparison import compare_multiple_jobs
from streamlit_app.utils.config import DEFAULT_WEIGHTS, get_llm_key
from streamlit_app.models.schemas import FinalAnalysis

SAMPLE = Path(__file__).resolve().parent / "sample_data"

# ---------- Page setup ----------
st.set_page_config(
    page_title="AI Resume & Job Matching Agent",
    page_icon="🎯",
    layout="wide",
)

# ---------- Custom styling ----------
st.markdown("""
<style>
:root {
  --bg-0: #0F1115;
  --bg-1: #171A21;
  --bg-2: #1F232C;
  --accent: #F5B14A;
  --accent-2: #4ADE80;
  --danger: #F87171;
  --warn: #FBBF24;
  --muted: #94A3B8;
  --text: #E5E7EB;
}
html, body, [class*="css"]  { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.stApp { background: var(--bg-0); color: var(--text); }
.big-title { font-size: 2.4rem; font-weight: 800; letter-spacing: -0.02em; }
.subtle { color: var(--muted); font-size: 0.95rem; }
.card {
  background: var(--bg-1); border: 1px solid #262B36; border-radius: 14px;
  padding: 1.1rem 1.2rem; margin-bottom: 0.8rem;
}
.score-hero {
  background: linear-gradient(135deg, #1a2233 0%, #10131a 100%);
  border: 1px solid #2A3242; border-radius: 18px; padding: 1.6rem;
}
.pill { display:inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; letter-spacing: .04em; }
.pill-matched { background: rgba(74,222,128,.12); color: #4ADE80; border: 1px solid rgba(74,222,128,.3); }
.pill-partial { background: rgba(251,191,36,.12); color: #FBBF24; border: 1px solid rgba(251,191,36,.3); }
.pill-related { background: rgba(96,165,250,.12); color: #60A5FA; border: 1px solid rgba(96,165,250,.3); }
.pill-missing { background: rgba(248,113,113,.12); color: #F87171; border: 1px solid rgba(248,113,113,.3); }
.pill-unknown { background: rgba(148,163,184,.12); color: #94A3B8; border: 1px solid rgba(148,163,184,.3); }
.evidence { font-size: 0.85rem; color: #B7C0CE; font-style: italic; }
.trace-step { padding: 6px 10px; border-left: 3px solid var(--accent); margin: 4px 0; background: #171A21; }
</style>
""", unsafe_allow_html=True)


def _pill(status: str) -> str:
    cls = {
        "MATCHED": "pill-matched",
        "PARTIALLY_MATCHED": "pill-partial",
        "RELATED": "pill-related",
        "MISSING": "pill-missing",
        "UNKNOWN": "pill-unknown",
    }.get(status, "pill-unknown")
    return f'<span class="pill {cls}">{status}</span>'


# ---------- Session state ----------
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "multi_analyses" not in st.session_state:
    st.session_state.multi_analyses = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### AI Resume & Job Agent")
    st.markdown('<span class="subtle">Understand → Extract → Compare → Decide → Recommend</span>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**1. Upload Resume**")
    resume_file = st.file_uploader(
        "Resume file (PDF / DOCX / TXT)",
        type=["pdf", "docx", "txt"],
        key="resume_up",
    )

    st.markdown("**2. Job Description**")
    jd_source = st.radio("Provide JD as", ["Paste text", "Upload file"], horizontal=True, key="jd_src")
    jd_text_input = ""
    jd_file = None
    if jd_source == "Paste text":
        jd_text_input = st.text_area("Paste the job description", height=180, key="jd_paste")
    else:
        jd_file = st.file_uploader("JD file (TXT / PDF)", type=["txt", "pdf"], key="jd_up")

    st.divider()
    st.markdown("**LLM Provider**")
    llm_key = get_llm_key()
    provider_mode = st.radio(
        "Mode",
        ["Cloud (Emergent LLM Key)", "Local / Rule-based"],
        index=0 if llm_key else 1,
        key="llm_mode",
    )
    show_trace = st.checkbox("Show agent workflow trace", value=True, key="show_trace")

    with st.expander("Score weights (advanced)"):
        w_req = st.slider("Required skills", 0.0, 1.0, DEFAULT_WEIGHTS["required_skills"], 0.05)
        w_exp = st.slider("Experience", 0.0, 1.0, DEFAULT_WEIGHTS["experience"], 0.05)
        w_proj = st.slider("Projects", 0.0, 1.0, DEFAULT_WEIGHTS["projects"], 0.05)
        w_edu = st.slider("Education", 0.0, 1.0, DEFAULT_WEIGHTS["education"], 0.05)
        w_pref = st.slider("Preferred skills", 0.0, 1.0, DEFAULT_WEIGHTS["preferred_skills"], 0.05)
        w_oth = st.slider("Other evidence", 0.0, 1.0, DEFAULT_WEIGHTS["other_evidence"], 0.05)

    weights = {
        "required_skills": w_req, "experience": w_exp, "projects": w_proj,
        "education": w_edu, "preferred_skills": w_pref, "other_evidence": w_oth,
    }
    weight_total = sum(weights.values())
    if weight_total > 0:
        weights = {k: v / weight_total for k, v in weights.items()}

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        analyze_btn = st.button("Analyze", type="primary", use_container_width=True, key="analyze_btn")
    with col_b:
        demo_btn = st.button("Run Demo", use_container_width=True, key="demo_btn")

    if st.button("Reset", use_container_width=True, key="reset_btn"):
        st.session_state.analysis = None
        st.session_state.chat_history = []
        st.session_state.multi_analyses = {}
        st.rerun()

    st.divider()
    st.caption(
        "Privacy: resumes are processed in memory for the duration of your session. "
        "Nothing is written to disk by default."
    )


# ---------- Header ----------
st.markdown('<div class="big-title">AI Resume & Job Matching Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtle">Understand → Extract → Compare → Decide → Recommend</div>', unsafe_allow_html=True)
st.write("")


def _load_texts(demo: bool = False) -> tuple[str, str]:
    if demo:
        return (SAMPLE / "sample_resume.txt").read_text(), (SAMPLE / "job_ai_engineer.txt").read_text()

    # Resume
    if not resume_file:
        st.error("Please upload a resume.")
        st.stop()
    data = resume_file.read()
    if is_scanned_pdf(resume_file.name, data):
        st.error(
            "This appears to be a scanned/image-based PDF. Text extraction was unsuccessful. "
            "Please upload a text-based PDF, DOCX, or TXT."
        )
        st.stop()
    resume_text = parse_resume(resume_file.name, data)
    if not resume_text or len(resume_text.strip()) < 30:
        st.error("Could not extract text from the resume. Please try a different format.")
        st.stop()

    # JD
    if jd_source == "Paste text":
        jd_text = (jd_text_input or "").strip()
    else:
        if not jd_file:
            st.error("Please upload a job description file.")
            st.stop()
        jd_text = parse_job_file(jd_file.name, jd_file.read())
    if not jd_text or len(jd_text.strip()) < 30:
        st.error("Job description is empty or too short.")
        st.stop()
    return resume_text, jd_text


def _run(resume_text: str, jd_text: str) -> FinalAnalysis:
    mode = "local" if provider_mode.startswith("Local") else "cloud"
    llm = build_llm(mode)
    with st.status("Running agent workflow...", expanded=True) as status:
        status.write("Extracting resume information...")
        analysis = run_complete_analysis(resume_text, jd_text, llm=llm, weights=weights)
        status.write(f"Score: {analysis.score.overall}/100 ({analysis.score.category})")
        status.update(label="Analysis complete", state="complete")
    return analysis


if analyze_btn:
    r, j = _load_texts(demo=False)
    st.session_state.analysis = _run(r, j)
    st.session_state.chat_history = []

if demo_btn:
    r, j = _load_texts(demo=True)
    st.session_state.analysis = _run(r, j)
    st.session_state.chat_history = []


analysis: FinalAnalysis | None = st.session_state.analysis

if analysis is None:
    st.info(
        "Upload a resume and a job description in the sidebar, then click **Analyze**. "
        "Or click **Run Demo** to see the full pipeline on sample data."
    )
    st.stop()


# ---------- Dashboard ----------
col1, col2, col3 = st.columns([1.4, 1, 1])

with col1:
    st.markdown('<div class="score-hero">', unsafe_allow_html=True)
    st.markdown(f"**Candidate:** {analysis.resume.name or 'N/A'}")
    st.markdown(f"**Target Role:** {analysis.job.job_title or 'N/A'}")
    st.markdown(
        f"<div style='font-size:3.6rem; font-weight:800; color:var(--accent);'>{analysis.score.overall}/100</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**Match level:** {analysis.score.category}")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=analysis.score.overall,
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#F5B14A"},
            "steps": [
                {"range": [0, 40], "color": "#3F2020"},
                {"range": [40, 70], "color": "#3F3720"},
                {"range": [70, 100], "color": "#1F3F2A"},
            ],
        },
    ))
    gauge.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=220,
                        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E5E7EB"))
    st.plotly_chart(gauge, use_container_width=True)

with col3:
    counts = {"MATCHED": 0, "PARTIALLY_MATCHED": 0, "RELATED": 0, "MISSING": 0, "UNKNOWN": 0}
    for m in analysis.matches:
        counts[m.status] += 1
    for k, v in counts.items():
        st.markdown(f"{_pill(k)} &nbsp; **{v}**", unsafe_allow_html=True)

st.caption(
    "This score estimates alignment with the provided job description. "
    "It is not a prediction of hiring outcome."
)

# ---------- Workflow trace ----------
if show_trace:
    with st.expander("🧠 Agent workflow trace", expanded=False):
        for step in analysis.workflow_trace:
            st.markdown(f'<div class="trace-step">✓ {step}</div>', unsafe_allow_html=True)


# ---------- Tabs ----------
tabs = st.tabs([
    "Requirements", "Strongest Skills", "Skill Gaps", "Score Breakdown",
    "Experience", "Resume Improvements", "Learning Roadmap", "Interview Prep",
    "Multi-Job Compare", "Ask the Agent",
])

with tabs[0]:
    st.subheader("Requirement match table")
    filt = st.multiselect(
        "Filter by status",
        ["MATCHED", "PARTIALLY_MATCHED", "RELATED", "MISSING", "UNKNOWN"],
        default=["MATCHED", "PARTIALLY_MATCHED", "RELATED", "MISSING"],
    )
    rows = [{
        "Requirement": m.requirement,
        "Importance": m.importance,
        "Status": m.status,
        "Confidence": m.confidence,
        "Evidence": (m.evidence[:180] + "…") if m.evidence and len(m.evidence) > 180 else (m.evidence or "—"),
    } for m in analysis.matches if m.status in filt]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("No requirements match the filter.")

with tabs[1]:
    st.subheader("Your strongest skills for this role")
    if not analysis.strongest_skills:
        st.info("No strongly-matched required skills detected.")
    for s in analysis.strongest_skills:
        st.markdown(
            f"<div class='card'><b>{s.skill}</b> &nbsp; "
            f"<span class='pill pill-matched'>{s.strength}</span> &nbsp; "
            f"<span class='subtle'>{s.job_relevance}</span><br>"
            f"<span class='evidence'>“{s.evidence[:220]}”</span><br>"
            f"<span class='subtle'>{s.reason}</span></div>",
            unsafe_allow_html=True,
        )

with tabs[2]:
    st.subheader("Skill gap analysis")
    for level, label in [("CRITICAL", "Critical"), ("IMPORTANT", "Important"), ("NICE_TO_HAVE", "Nice to have")]:
        gaps = [g for g in analysis.skill_gaps if g.importance == level]
        if not gaps:
            continue
        st.markdown(f"### {label} ({len(gaps)})")
        for g in gaps:
            st.markdown(
                f"<div class='card'><b>{g.skill}</b><br>"
                f"<span class='subtle'>{g.gap_explanation}</span><br>"
                f"<span class='evidence'>Current evidence: {g.current_evidence}</span><br>"
                f"<b>Recommendation:</b> {g.learning_recommendation}</div>",
                unsafe_allow_html=True,
            )

with tabs[3]:
    st.subheader("Why this score?")
    breakdown = pd.DataFrame([
        {"Bucket": "Required Skills", "Score": analysis.score.required_skills_score, "Weight": analysis.score.weights.get("required_skills", 0)},
        {"Bucket": "Experience", "Score": analysis.score.experience_score, "Weight": analysis.score.weights.get("experience", 0)},
        {"Bucket": "Projects", "Score": analysis.score.projects_score, "Weight": analysis.score.weights.get("projects", 0)},
        {"Bucket": "Education", "Score": analysis.score.education_score, "Weight": analysis.score.weights.get("education", 0)},
        {"Bucket": "Preferred Skills", "Score": analysis.score.preferred_skills_score, "Weight": analysis.score.weights.get("preferred_skills", 0)},
        {"Bucket": "Other Evidence", "Score": analysis.score.other_evidence_score, "Weight": analysis.score.weights.get("other_evidence", 0)},
    ])
    breakdown["Weighted"] = (breakdown["Score"] * breakdown["Weight"]).round(2)
    breakdown["Weight %"] = (breakdown["Weight"] * 100).round(1)
    st.dataframe(breakdown[["Bucket", "Score", "Weight %", "Weighted"]], hide_index=True, use_container_width=True)
    st.markdown(f"**Final: {analysis.score.overall}/100 → {analysis.score.category}**")
    st.caption(analysis.score.breakdown_note)

    bar = go.Figure(go.Bar(x=breakdown["Bucket"], y=breakdown["Score"], marker_color="#F5B14A"))
    bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#E5E7EB"), height=300, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(bar, use_container_width=True)

with tabs[4]:
    st.subheader("Experience comparison")
    if not analysis.experience_comparisons:
        st.info("No experience requirements to compare.")
    for c in analysis.experience_comparisons:
        st.markdown(
            f"<div class='card'><b>Job:</b> {c.requirement}<br>"
            f"<b>Resume evidence:</b> {c.candidate_evidence}<br>"
            f"<b>Decision:</b> {c.decision} — <span class='subtle'>{c.reason}</span></div>",
            unsafe_allow_html=True,
        )

with tabs[5]:
    st.subheader("Resume improvement suggestions")
    if not analysis.resume_recommendations:
        st.info("No major resume issues detected.")
    for r in analysis.resume_recommendations:
        st.markdown(
            f"<div class='card'><b>{r.section}</b><br>"
            f"<span class='subtle'>{r.issue}</span><br>"
            f"→ {r.suggestion}</div>",
            unsafe_allow_html=True,
        )

with tabs[6]:
    st.subheader("Learning roadmap")
    for tf in ["IMMEDIATE", "1-2 WEEKS", "1 MONTH", "2-3 MONTHS"]:
        items = [it for it in analysis.learning_roadmap if it.timeframe == tf]
        if not items:
            continue
        st.markdown(f"### {tf}")
        for it in items:
            st.markdown(
                f"<div class='card'><b>{it.skill}</b> "
                f"<span class='pill pill-related'>{it.job_relevance}</span><br>"
                f"<span class='subtle'>{it.why_learn}</span><br>"
                f"<b>Suggested project:</b> {it.suggested_project}</div>",
                unsafe_allow_html=True,
            )

with tabs[7]:
    st.subheader("Interview preparation topics")
    for cat in sorted({t.category for t in analysis.interview_topics}):
        st.markdown(f"### {cat}")
        for t in analysis.interview_topics:
            if t.category != cat:
                continue
            st.markdown(
                f"<div class='card'><b>{t.topic}</b><br>"
                f"<span class='subtle'>{t.why_it_matters}</span><br>"
                f"<b>Prep:</b> {t.preparation_guidance}<br>"
                f"<i>Example:</i> {t.example_question}</div>",
                unsafe_allow_html=True,
            )

with tabs[8]:
    st.subheader("Compare this resume against multiple jobs")
    st.caption("Analyze the same resume against additional JDs to rank fit.")
    extra_jd = st.text_area("Paste another job description", height=140, key="extra_jd_text")
    label = st.text_input("Label for this job", value="Job B", key="extra_jd_label")
    if st.button("Add & compare", key="add_compare"):
        if extra_jd.strip():
            new_a = run_complete_analysis(
                analysis.resume.raw_text, extra_jd,
                llm=build_llm("local" if provider_mode.startswith("Local") else "cloud"),
                weights=weights,
            )
            st.session_state.multi_analyses[label] = new_a
        else:
            st.warning("Please paste a job description.")

    all_map = {"Current job": analysis, **st.session_state.multi_analyses}
    if len(all_map) > 1:
        summary = compare_multiple_jobs(all_map)
        st.markdown("### Ranking")
        rows = []
        for lbl, s in summary["per_job"].items():
            rows.append({"Job": lbl, "Score": s["score"], "Category": s["category"],
                         "Matched": s["matched"], "Missing": s["missing"],
                         "Top gaps": ", ".join(s["top_gaps"])})
        rows.sort(key=lambda r: -r["Score"])
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        if summary["cross_cutting_gaps"]:
            st.info("**Skills that would improve you across multiple jobs:** " +
                    ", ".join(summary["cross_cutting_gaps"][:6]))

with tabs[9]:
    st.subheader("Ask the Resume Agent")
    st.caption("Answers are grounded in the analysis of your resume and this job. The agent will not invent evidence.")

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_q = st.chat_input("e.g., Why did I get this score? Which skills should I learn first?")
    if user_q:
        st.session_state.chat_history.append(("user", user_q))
        with st.chat_message("user"):
            st.markdown(user_q)
        intent = route_intent(user_q)
        llm = build_llm("local" if provider_mode.startswith("Local") else "cloud")
        answer = answer_followup_question(analysis, user_q, llm)
        answer = f"**Router intent:** `{intent}`\n\n{answer}"
        st.session_state.chat_history.append(("assistant", answer))
        with st.chat_message("assistant"):
            st.markdown(answer)


# ---------- Download report ----------
st.divider()
report_md = generate_final_report(analysis)
st.download_button(
    "📥 Download full analysis (Markdown)",
    data=report_md.encode("utf-8"),
    file_name="resume_match_report.md",
    mime="text/markdown",
    use_container_width=True,
)
