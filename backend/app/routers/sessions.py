from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from app.db.client import get_db
from app.db import queries

router = APIRouter()


class CreateSessionRequest(BaseModel):
    salon_id: str
    designer_id: str
    gender: str = "female"


class UpdateNotesRequest(BaseModel):
    consultation_notes: str


class SelectStyleRequest(BaseModel):
    style_id: str


@router.post("")
async def create_session(body: CreateSessionRequest):
    db = get_db()
    session = queries.create_session(db, body.salon_id, body.designer_id, body.gender)
    return session


@router.get("/{session_id}")
async def get_session(session_id: str):
    db = get_db()
    session = queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}/notes")
async def update_notes(session_id: str, body: UpdateNotesRequest):
    db = get_db()
    updated = queries.update_session(
        db, session_id, {"consultation_notes": body.consultation_notes}
    )
    return updated


@router.patch("/{session_id}/style")
async def select_style(session_id: str, body: SelectStyleRequest):
    db = get_db()
    updated = queries.update_session(
        db, session_id, {"selected_style_id": body.style_id, "status": "completed"}
    )
    return updated


@router.get("/{session_id}/photo-signed-url")
async def get_photo_signed_url(session_id: str):
    db = get_db()
    session = queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    photo_url = session.get("processed_photo_url")
    if not photo_url:
        raise HTTPException(status_code=404, detail="No photo for this session")
    bucket = "session-photos"
    path = photo_url.split(f"/{bucket}/")[1] if f"/{bucket}/" in photo_url else None
    if not path:
        raise HTTPException(status_code=400, detail="Invalid photo URL")
    signed = db.storage.from_(bucket).create_signed_url(path, 3600)
    signed_url = signed.get("signedURL") or signed.get("signed_url") or photo_url
    return {"signed_url": signed_url}


@router.get("/{session_id}/summary")
async def get_summary(session_id: str):
    db = get_db()
    session = queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Fetch selected style details if available
    selected_style = None
    if session.get("selected_style_id"):
        selected_style = queries.get_style_by_id(db, session["selected_style_id"])

    # Fetch simulation jobs for this session
    sim_jobs = (
        db.table("simulation_jobs")
        .select("*")
        .eq("session_id", session_id)
        .eq("status", "done")
        .execute()
    )

    return {
        "session": session,
        "selected_style": selected_style,
        "simulation_results": sim_jobs.data or [],
    }
