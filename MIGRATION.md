# Migration: Streamlit → Next.js Frontend

This document describes the changes made to replace the **Streamlit** frontend with a
**Next.js** frontend, while keeping all existing Python business logic.

Date: 2026-10-16

---

## 1. Summary

| Area | Before | After |
| --- | --- | --- |
| Frontend | Streamlit (`app.py`) | Next.js 16 + React 19 + Tailwind CSS v4 (`resume-ranker-frontend/`) |
| Backend | None (logic ran inside Streamlit) | FastAPI (`main.py`) exposing the existing Python modules |
| Auth | Static HTML page → redirect to Streamlit with `?token=<idToken>` | Firebase Web SDK in Next.js → ID token sent as `Authorization: Bearer` on each API call |
| Styling | Streamlit default + injected CSS | Tailwind utilities, glassmorphism dark theme |

The Python AI/parsing logic was **not rewritten** — it is reused as-is through a thin
FastAPI layer.

---

## 2. Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────────────┐
│  Next.js frontend           │  HTTP  │  FastAPI backend (main.py)            │
│  resume-ranker-frontend/    │ ─────► │  ─ wraps existing Python modules:     │
│                             │ Bearer │    • cleaner.extract_text_from_pdf    │
│  • Firebase Auth (Web SDK)  │ token  │    • resume_paser.parse_resume_auto   │
│  • Landing / Login page     │        │    • ai_suggester.*                   │
│  • Dashboard (analyze,      │        │    • matcher.calculate_match_score    │
│    transform, feedback)     │        │    • template_filler.build_*          │
└─────────────────────────────┘        └──────────────────────────────────────┘
              │                                        │
              │ Firebase ID token                      │ verify_id_token (Admin SDK)
              ▼                                        ▼
        ┌───────────────────────────────────────────────────┐
        │              Firebase (Auth + Firestore)           │
        └───────────────────────────────────────────────────┘
                                                 │
                                                 ▼
                                          Groq API (LLM)
```

---

## 3. Files removed

- **`app.py`** — the Streamlit application (frontend + orchestration). Its auth logic
  and workflow were ported into `main.py` and the Next.js UI.
- From `requirements.txt`: `streamlit`, `streamlit-extras` (no longer used).
- Unused Next.js starter assets under `resume-ranker-frontend/public/` (`next.svg`,
  `vercel.svg`, etc.).

> The static sites in `resume-landing/` and `public/` are **retained** (still used for
> Firebase Hosting), but they are now optional since login is handled inside the
> Next.js app. See [Follow-ups](#9-recommended-follow-ups).

## 4. Files added

### Backend
- **`main.py`** — FastAPI application. Endpoints:
  - `GET  /api/health` — health + config check.
  - `POST /api/analyze` — multipart (`file`, `job_description`); parses the resume,
    scores it, and returns structured AI feedback.
  - `POST /api/transform` — JSON (`parsed_resume`, `job_description`); returns an
    ATS-optimized `.docx`.
  - `POST /api/feedback` — JSON (`rating`, `comments`); writes to Firestore.
  - Firebase ID token verification via `Authorization: Bearer <token>` dependency.
  - CORS configured from the `ALLOWED_ORIGINS` env var.

### Frontend (`resume-ranker-frontend/`)
- `src/app/layout.tsx` — root layout + `AuthProvider`, global metadata/fonts.
- `src/app/page.tsx` — landing page (hero + features + Google login).
- `src/app/dashboard/page.tsx` — dashboard route.
- `src/app/globals.css` — Tailwind v4 import, theme tokens, glass/gradient utilities.
- `src/components/AuthProvider.tsx` — Firebase auth React context.
- `src/components/Header.tsx` — nav bar with user email / logout.
- `src/components/LoginButton.tsx` — Google sign-in button.
- `src/components/Dashboard.tsx` — upload, analyze, results, transform, feedback UI.
- `src/components/ScoreRing.tsx` — SVG ATS / match score ring.
- `src/lib/firebase.ts` — Firebase Web SDK init + helpers.
- `src/lib/api.ts` — typed API client (attaches the Bearer token).
- `src/lib/types.ts` — shared TypeScript types.
- `.env.example` — template for required env vars.
- `.env.local` — local values (git-ignored).

## 5. Files modified

- **`ai_suggester.py`** — added `get_suggestions_structured()` which returns the AI
  feedback as JSON (`ats_score`, `match_score`, `strengths`, `improvements`,
  `overall`) instead of a free-text block. The original `get_suggestions()` is kept
  for backward compatibility. `optimize_resume_for_role()` is reused unchanged.
- **`requirements.txt`** — removed `streamlit`/`streamlit-extras`; added `fastapi`,
  `uvicorn[standard]`, `python-multipart`.
- **`README.md`** — replaced the Streamlit badge with Next.js and rewrote the
  setup/run instructions (FastAPI backend + Next.js frontend).
- **`.devcontainer/devcontainer.json`** — start command changed from
  `streamlit run app.py` to `uvicorn main:app`; forwarded ports updated
  (`8501` → `8000`, plus `3000`).

## 6. Auth flow change

**Before:** a static HTML page signed in with Firebase, then redirected to the
Streamlit app with the ID token in the URL query string (`?token=...`).

```js
window.location.href = "...streamlit.app/?token=" + idToken;
```

**After:** the Next.js app signs in with the Firebase Web SDK, keeps the user session
client-side, and attaches a freshly-minted ID token to every backend request.

```ts
headers: { Authorization: `Bearer ${await user.getIdToken()}` }
```

The FastAPI backend verifies the token with the Firebase Admin SDK
(`verify_id_token`) before processing any request. This avoids putting tokens in URLs
(no leaking via logs/referrers).

---

## 7. Configuration

### Backend (repo root `.env`)
| Variable | Purpose | Default |
| --- | --- | --- |
| `GROQ_API_KEY` | Groq API key for the LLM | — (required) |
| `FIREBASE_CREDENTIALS` | Path to the Firebase Admin service-account JSON | `resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json` |
| `REQUIRE_AUTH` | Enforce Bearer-token auth (`true`/`false`) | `true` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` |

### Frontend (`resume-ranker-frontend/.env.local`)
| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | FastAPI base URL (e.g. `http://localhost:8000`) |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase Web config |

> Firebase **Web** config values are public by design (they ship in client bundles).
> The **Admin** service-account JSON is secret — keep it out of source control.

---

## 8. How to run

### Backend
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# health check: http://localhost:8000/api/health
# API docs:     http://localhost:8000/docs
```

### Frontend
```bash
cd resume-ranker-frontend
npm install
# create .env.local from .env.example and fill in the values
npm run dev        # http://localhost:3000
npm run build      # production build
```

Start the backend first (or set `NEXT_PUBLIC_API_URL` to wherever it runs).

---

## 9. Recommended follow-ups

1. **Rotate & secure secrets.** The Firebase Admin service-account JSON currently
   lives in the repo root and `firebase_config.py` hardcodes API keys. Rotate those
   credentials and load them from environment variables / secret storage.
2. **Fix `.gitignore` secret pattern.** The entry
   `resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json:1` is malformed and
   does not reliably ignore the JSON. Use `*.json` scoped correctly or remove the file
   from tracking.
3. **Delete legacy modules** if unused: `firebase_config.py`, `formatter.py`,
   `jd_parser.py` (superseded by `jd_analyzer.py`), `gap_analysis.py`, `template.py`.
4. **Remove/redirect legacy landing folders** (`resume-landing/`, `public/`) once the
   Next.js app is deployed, or point Firebase Hosting at the Next.js build.
5. **Token expiry / refresh UX.** The client fetches a fresh token per request; add a
   global 401 handler that re-authenticates if the session expires mid-use.
6. **Backend CORS for production.** Set `ALLOWED_ORIGINS` to the deployed frontend
   origin(s) before going live.

---

## 10. Verification performed

- `python -c "import main"` — backend imports cleanly; all 4 API routes registered.
- FastAPI smoke test — `/api/health` returns `200`; OpenAPI lists all endpoints.
- `npm run build` — Next.js production build succeeds (`/`, `/dashboard` prerendered).
- `npm run lint` — ESLint passes with no errors.
