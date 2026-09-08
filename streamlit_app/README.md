# AI Resume & Job Matching Agent

**Understand → Extract → Compare → Decide → Recommend**

An agentic Streamlit application that goes far beyond keyword matching. It extracts
structured evidence from a candidate's resume and a job description, semantically
compares them, validates every claim against the resume text, computes a
deterministic, explainable match score, identifies skill gaps, and generates
personalized learning + interview prep — all with strict hallucination prevention.

---

## Features

- Resume upload (PDF / DOCX / TXT) — parsed in memory (privacy-first)
- Job description via paste or file upload
- Structured extraction into typed Pydantic schemas
- Evidence-based matching (`MATCHED`, `PARTIALLY_MATCHED`, `RELATED`, `MISSING`, `UNKNOWN`)
- Deterministic weighted score (0–100) with a full "Why this score?" breakdown
- Skill-gap analysis (CRITICAL / IMPORTANT / NICE_TO_HAVE)
- Resume improvement suggestions, learning roadmap, interview prep
- Multi-job comparison — see which JD you fit best
- Follow-up Q&A chat, grounded in the analysis
- Downloadable Markdown report
- Configurable LLM (Cloud via Emergent Universal LLM Key, or rule-based local fallback)
- Agent workflow trace visible to judges

---

## Architecture

```
Streamlit UI  →  Agent Router
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Resume Agent    Job Agent      Q&A Agent
             │              │
             ▼              ▼
      Resume Parser   JD Parser
             │              │
             └──────┬───────┘
                    ▼
             Matching Engine (evidence-validated)
                    ▼
             Deterministic Score Engine
                    ▼
             Recommendation Agent → Learning + Interview
                    ▼
             Final Validation → Report
```

---

## Tech Stack

- Python 3.11+, Streamlit
- Pydantic v2 for schemas
- pypdf, python-docx for document parsing
- Plotly for charts
- `emergentintegrations` for cloud LLM (OpenAI GPT-5.4 via Emergent Universal Key)

---

## Install

```bash
pip install -r streamlit_app/requirements.txt
```

## Configure LLM

Add to `/app/backend/.env` (already provisioned):

```
EMERGENT_LLM_KEY=sk-emergent-xxxxxxxxxxxx
```

The app automatically picks it up. Switch to "Local / Rule-based" in the
sidebar to run fully offline without any LLM.

## Run

```bash
streamlit run streamlit_app/app.py --server.port 3000 --server.address 0.0.0.0
```

On this platform it is already wired to port 3000 through the frontend
supervisor entry.

## Demo mode

Click **"Run Demo"** in the sidebar to run the full pipeline on the sample
resume + sample AI Engineer JD in `streamlit_app/sample_data/`.

## Tests

```bash
pytest streamlit_app/tests -q
```

Includes:
- Parser tests
- Deterministic scoring tests
- Hallucination-prevention test (AWS/Docker not on resume must NOT be marked MATCHED)
- End-to-end agent test using rule-based provider

## Scoring methodology

Default weights (configurable in the sidebar):

- Required Skills: 40%
- Experience:      25%
- Projects:        15%
- Education:       10%
- Preferred Skills: 5%
- Other Evidence:   5%

Each requirement is scored by status:
`MATCHED=1.0, PARTIALLY_MATCHED=0.6, RELATED=0.3, UNKNOWN=0.15, MISSING=0.0`.

Buckets are averaged, then combined via the configured weights. The LLM is
**never** asked to pick the number — the score is 100% deterministic.

## Hallucination prevention

- Every requirement match is checked against the raw resume text.
- If no direct snippet is found, the status is downgraded (never `MATCHED`).
- The LLM extraction is always merged with a rule-based fallback, and any
  fields absent from the resume are left empty.
- The Q&A agent is grounded on the analysis object only.

## Privacy

- Files are read into memory; nothing is written to disk by default.
- No API keys are logged.
- A privacy notice is displayed in the sidebar.

## For competition judges

1. Open the app.
2. Click **Run Demo** in the sidebar.
3. Enable **Show agent workflow trace**.
4. Explore each tab: Requirements → Skill Gaps → Score Breakdown → Learning → Interview.
5. Ask the agent a follow-up like *"Why did I get this score?"* or *"Which skills should I learn first?"*.
6. Try **Multi-Job Compare** with a second JD.

## Limitations

- Scanned/image PDFs are not OCR'd by default.
- Semantic matching relies on a curated related-skill map rather than a heavy
  embedding model (kept lightweight on purpose).
- Extraction quality is best when using the cloud LLM; local rule-based mode
  is a safety net, not a peer.

## Ethical note

This system evaluates alignment with the provided job requirements. It does
not use any protected characteristics for scoring and should support, not
replace, human judgment.
