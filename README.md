# Psychometric Assessment Platform

End-to-end psychometric assessment platform for recruitment: recruiters send a unique link, candidates complete a timed multi-module test in French, Dutch or English, scores are computed server-side and an LLM writes a structured narrative report that can be exported to PDF.

Built with compliance in mind: GDPR (consent, access and erasure endpoints, retention), Belgian CCT n°38 and the EU AI Act obligations for high-risk systems used in employment.

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI · Pydantic v2 · PyJWT · slowapi rate limiting (proxy-aware, pluggable storage) · optional Sentry |
| Data | Supabase (PostgreSQL, row-level security) |
| LLM | Anthropic Claude: a fast model for interactive calls, a larger model for the final report |
| Reports | HTML report rendered to PDF with WeasyPrint |
| Email | Resend |
| Frontend | Static HTML/CSS/JS, Sortable.js for ranking items, i18n module (FR/NL/EN) |
| Hosting | Render (Docker) for the API, Cloudflare Pages for the frontend |
| CI | GitHub Actions: unit tests, compile check, app import smoke test, i18n key parity |

## Assessment model

| Module | Construct | Format |
|---|---|---|
| M1 | Logical reasoning | Timed multiple choice |
| M2 | Personality, Big Five (IPIP-based) | Likert 1–5 |
| M3 | Leadership situational judgement | Ranking |
| M4 | Motivations and values | Ranking + Likert |

Packages (`scan`, `operational`, `commercial`, `leadership`) combine modules by role type. Items exist at two difficulty levels and in three languages.

Scoring is deterministic and lives in `backend/assessment-api/app/services/scoring.py`. Answer keys and scoring rules (section, Big Five dimension, reverse keying, SJT optimal ranking, value mapping) are stored with each item in the database, in server-only columns, so the engine contains no test content. The LLM never scores: it receives the computed profile and returns strict JSON for the narrative sections.

The production item bank is not part of this repository. `scripts/seed_demo.py` loads a small trilingual demo bank covering every item type.

## Architecture

```
frontend/ (Cloudflare Pages)
  dashboard.html     recruiter dashboard: sessions, statistics, links
  player.html        candidate test player
  report-demo.html   report viewer and PDF export
  i18n.js            FR / NL / EN strings
  js/ · css/         page scripts and styles, shared HTML escaping in js/utils.js
        │  HTTPS, JWT for recruiters, opaque token for candidates
        ▼
backend/assessment-api/ (FastAPI on Render)
  routers/   auth · sessions · test · scores · pdf · candidate_rights
  services/  scoring · report (LLM) · token · email
        │
        ▼
Supabase PostgreSQL   sessions · questions · answers · scores · audit fields
```

## API

All routes are served under `/api/v1`.

| Method | Route | Purpose |
|---|---|---|
| POST | `/auth/login` | Recruiter login |
| POST / GET | `/sessions/` | Create or list sessions |
| GET | `/sessions/stats` | Dashboard metrics |
| GET | `/sessions/{id}` | Session detail |
| GET | `/test/{token}` | Validate a candidate link |
| POST | `/test/{token}/start` | Record consent and start |
| GET | `/test/{token}/questions` | Item bank for the session language and package |
| POST | `/test/{token}/submit` | Submit answers, scoring and report run in background |
| GET / DELETE | `/test/{token}/my-data` | GDPR access and erasure for the candidate |
| GET | `/scores/{session_id}` | Scores and narrative report |
| GET | `/scores/{session_id}/pdf` | PDF export |

## Run locally

```bash
cd backend/assessment-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python scripts/setup_db.py
python scripts/seed_demo.py
pytest
uvicorn app.main:app --reload --port 8000
```

Serve `frontend/` with any static server and set `window.ASSESSMENT_API_BASE` in `frontend/config.js`.

## Deployment

- API: `backend/assessment-api/render.yaml` blueprint, secrets set in the Render dashboard; the container runs as a non-root user
- Behind a reverse proxy, set `TRUSTED_PROXY_HOPS` so rate limiting keys on the real client address; set `RATE_LIMIT_STORAGE_URI` (for example Redis) when running several instances
- Frontend: Cloudflare Pages on `frontend/`, with `_headers` (security headers) and `_redirects` (clean `/test/<token>` links)

## Compliance documentation

`docs/compliance/` contains the templates written for the platform (in French): privacy policy, candidate consent, recruiter terms, processing register, processor agreements, DPIA checklist and audit logging.

## License

Copyright (c) 2026 Wissem Ben Mariem. All rights reserved. See [LICENSE](LICENSE).
