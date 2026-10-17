"""FastAPI backend for Resume Ranker.

Replaces the Streamlit frontend (app.py). Reuses the existing Python modules:
  - cleaner.extract_text_from_pdf
  - resume_paser.parse_resume_auto
  - ai_suggester.get_suggestions_structured / optimize_resume_for_role
  - matcher.calculate_match_score
  - template_filler.build_template_resume

Run:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from ai_suggester import get_suggestions_structured, optimize_resume_for_role
from cleaner import extract_text_from_pdf
from resume_paser import parse_resume_auto
from template_filler import build_template_resume

load_dotenv()

# ----------------------------- CONFIG ----------------------------- #
GATEWAY_JSON = os.getenv(
    "FIREBASE_CREDENTIALS",
    "resume-ranker-auth-firebase-adminsdk-fbsvc-16ac3f1d73.json",
)
# Set REQUIRE_AUTH=false for local development without Firebase creds.
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "true").lower() in {"1", "true", "yes"}
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

# ---------------------------- FIREBASE ---------------------------- #
firebase_ready = False
db = None

try:
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps and os.path.exists(GATEWAY_JSON):
        cred = credentials.Certificate(GATEWAY_JSON)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        firebase_ready = True
except Exception:
    firebase_ready = False


def verify_token(authorization: Optional[str]) -> Dict[str, Any]:
    """Verify a Firebase ID token sent as `Authorization: Bearer <token>`."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    if not firebase_ready:
        raise HTTPException(
            status_code=503,
            detail="Firebase Admin is not configured (missing credentials file).",
        )

    from firebase_admin import auth as admin_auth

    try:
        return admin_auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def current_user(authorization: Optional[str]) -> Dict[str, Any]:
    if not REQUIRE_AUTH:
        return {"uid": "dev", "email": "dev@local"}
    return verify_token(authorization)


# ----------------------------- APP ----------------------------- #
app = FastAPI(title="Resume Ranker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "firebase": firebase_ready,
        "auth_required": REQUIRE_AUTH,
    }


# --------------------------- MODELS --------------------------- #
class AnalyzeResponse(BaseModel):
    ats_score: int | str
    match_score: int | float | str
    strengths: list[str]
    improvements: list[str]
    overall: str
    resume_text: str
    parsed_resume: Dict[str, Any]


class TransformRequest(BaseModel):
    parsed_resume: Dict[str, Any]
    job_description: str


class FeedbackRequest(BaseModel):
    rating: str
    comments: str = ""


# --------------------------- ENDPOINTS --------------------------- #
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    authorization: Optional[str] = Header(None),
    user: Dict[str, Any] = Depends(current_user),
) -> AnalyzeResponse:
    """Parse an uploaded resume, score it against a JD, return AI feedback."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not job_description or not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required")

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        resume_text = extract_text_from_pdf(raw_bytes)
    except Exception:
        resume_text = ""

    try:
        parsed_resume = parse_resume_auto(raw_bytes, file.filename)
    except Exception:
        parsed_resume = {}

    if not resume_text and not parsed_resume:
        raise HTTPException(status_code=422, detail="Could not read resume")

    feedback = get_suggestions_structured(resume_text or "", job_description)

    return AnalyzeResponse(
        ats_score=feedback.get("ats_score", 0),
        match_score=feedback.get("match_score", 0),
        strengths=feedback.get("strengths", []),
        improvements=feedback.get("improvements", []),
        overall=feedback.get("overall", ""),
        resume_text=resume_text,
        parsed_resume=parsed_resume or {},
    )


@app.post("/api/transform")
async def transform(
    body: TransformRequest,
    authorization: Optional[str] = Header(None),
    user: Dict[str, Any] = Depends(current_user),
) -> Response:
    """Optimize the resume for the JD and return an ATS-friendly .docx."""
    if not body.parsed_resume:
        raise HTTPException(status_code=400, detail="parsed_resume is required")
    if not body.job_description or not body.job_description.strip():
        raise HTTPException(status_code=400, detail="job_description is required")

    try:
        optimized = optimize_resume_for_role(
            body.parsed_resume, body.job_description
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Optimization failed: {exc}")

    try:
        buffer = build_template_resume(optimized)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DOCX build failed: {exc}")

    if not buffer:
        raise HTTPException(status_code=500, detail="Empty document produced")

    data = buffer.getvalue()
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="updated_resume.docx"'},
    )


@app.post("/api/feedback")
async def feedback(
    body: FeedbackRequest,
    authorization: Optional[str] = Header(None),
    user: Dict[str, Any] = Depends(current_user),
) -> Dict[str, str]:
    """Persist user feedback to Firestore (no-op if Firebase is unavailable)."""
    if db is not None:
        try:
            db.collection("feedback").add(
                {
                    "user": user.get("email") or user.get("uid", "unknown"),
                    "rating": body.rating,
                    "comments": body.comments,
                }
            )
        except Exception:
            pass
    return {"status": "saved"}
