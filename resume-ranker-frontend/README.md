# Resume Ranker — Frontend

Next.js (App Router) frontend for **Resume Ranker**. Handles Google authentication
(Firebase Web SDK) and the upload → analyze → transform workflow, talking to the
FastAPI backend at `NEXT_PUBLIC_API_URL`.

## Requirements

- Node.js 20+
- The backend running (see the repo root `README.md` / `MIGRATION.md`)

## Setup

```bash
npm install
# Create .env.local and set your REAL Firebase project values.
# Do NOT keep the placeholder values from .env.example, or login will fail
# with "auth/api-key-not-valid".
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

> `NEXT_PUBLIC_*` variables are inlined when the dev/build server starts, so always
> **restart** `npm run dev` after editing `.env.local`.

## Environment variables

| Variable | Description |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI backend (e.g. `http://localhost:8000`) |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID` | Firebase Web config |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Firebase Web config |

> Firebase Web config values are public (they ship to the browser). Never put the
> Firebase **Admin** service-account JSON here.

## Scripts

```bash
npm run dev     # start dev server
npm run build   # production build
npm run start   # run the production build
npm run lint    # eslint
```

## Structure

```
src/
  app/
    layout.tsx            # root layout + AuthProvider
    page.tsx              # landing / login
    dashboard/page.tsx    # analysis dashboard
    globals.css           # Tailwind v4 + theme
  components/
    AuthProvider.tsx      # Firebase auth context
    Header.tsx
    LoginButton.tsx
    Dashboard.tsx
    ScoreRing.tsx
  lib/
    firebase.ts           # Firebase Web SDK init
    api.ts                # backend client (attaches Bearer token)
    types.ts
```

## Authentication

Users sign in with Google via the Firebase Web SDK. Each backend request includes a
fresh ID token as `Authorization: Bearer <token>`, which the FastAPI backend verifies
with the Firebase Admin SDK.

## Troubleshooting login

### `Firebase: Error (auth/api-key-not-valid...)`

`.env.local` still has the placeholder values from `.env.example`. Put your **real**
Firebase Web config in `.env.local` and **restart** `npm run dev` (`NEXT_PUBLIC_*`
vars are inlined at startup).

### `Firebase: Error (auth/unauthorized-domain)`

The origin you're browsing from isn't in the project's authorized domains. For
projects created after **April 28, 2025**, `localhost` is **not** added by default.

1. Firebase Console → **Authentication** → **Settings** → **Authorized domains**
2. Click **Add domain** and add `localhost` (and `127.0.0.1` if you use that host)
3. Add your deployed domain too (e.g. `your-app.vercel.app`)

> Add only the host — no protocol and no port (`localhost`, **not**
> `http://localhost:3000`). Then retry login; no code changes required.
