from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.db.client import get_db
from app.db import queries
from app.deps import get_current_user

router = APIRouter()


class CreateSessionRequest(BaseModel):
    gender: str = "female"


class UpdateNotesRequest(BaseModel):
    consultation_notes: str


class SelectStyleRequest(BaseModel):
    style_id: str


def _verify_session_ownership(session: dict | None, designer: dict) -> dict:
    """세션이 존재하고, 현재 디자이너의 salon 소속인지 확인."""
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    if session.get("salon_id") != designer.get("salon_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return session


@router.get("")
async def list_sessions(
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    designer: dict = Depends(get_current_user),
):
    """디자이너의 salon에 속한 세션 목록 조회 (최신순)."""
    db = get_db()
    query = (
        db.table("sessions")
        .select("*")
        .eq("salon_id", designer["salon_id"])
        .order("created_at", desc=True)
        .limit(limit)
    )
    if status:
        query = query.eq("status", status)
    response = query.execute()
    return {"sessions": response.data or [], "total": len(response.data or [])}


@router.post("")
async def create_session(body: CreateSessionRequest, designer: dict = Depends(get_current_user)):
    db = get_db()
    session = queries.create_session(db, designer["salon_id"], designer["id"], body.gender)
    return session


@router.get("/{session_id}")
async def get_session(session_id: str, designer: dict = Depends(get_current_user)):
    db = get_db()
    session = queries.get_session(db, session_id)
    _verify_session_ownership(session, designer)
    return session


@router.patch("/{session_id}/notes")
async def update_notes(session_id: str, body: UpdateNotesRequest, designer: dict = Depends(get_current_user)):
    db = get_db()
    session = queries.get_session(db, session_id)
    _verify_session_ownership(session, designer)
    updated = queries.update_session(
        db, session_id, {"consultation_notes": body.consultation_notes}
    )
    return updated


@router.patch("/{session_id}/style")
async def select_style(session_id: str, body: SelectStyleRequest, designer: dict = Depends(get_current_user)):
    db = get_db()
    session = queries.get_session(db, session_id)
    _verify_session_ownership(session, designer)
    updated = queries.update_session(
        db, session_id, {"selected_style_id": body.style_id, "status": "completed"}
    )
    return updated


@router.get("/{session_id}/photo-signed-url")
async def get_photo_signed_url(session_id: str, designer: dict = Depends(get_current_user)):
    db = get_db()
    session = queries.get_session(db, session_id)
    _verify_session_ownership(session, designer)
    photo_url = session.get("processed_photo_url")
    if not photo_url:
        raise HTTPException(status_code=404, detail="사진이 없습니다.")
    bucket = "session-photos"
    path = photo_url.split(f"/{bucket}/")[1] if f"/{bucket}/" in photo_url else None
    if not path:
        raise HTTPException(status_code=400, detail="잘못된 사진 URL입니다.")
    signed = db.storage.from_(bucket).create_signed_url(path, 3600)
    signed_url = signed.get("signedURL") or signed.get("signed_url") or photo_url
    return {"signed_url": signed_url}


@router.get("/{session_id}/summary")
async def get_summary(session_id: str, designer: dict = Depends(get_current_user)):
    db = get_db()
    session = queries.get_session(db, session_id)
    _verify_session_ownership(session, designer)

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
