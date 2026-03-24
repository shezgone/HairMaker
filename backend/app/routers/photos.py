from fastapi import APIRouter, UploadFile, File, HTTPException
from app.db.client import get_db
from app.db import queries
from app.services import image_service, storage_service

router = APIRouter()


@router.post("/{session_id}/photo")
async def upload_photo(session_id: str, file: UploadFile = File(...)):
    """
    Accept raw photo upload, preprocess it, save to Supabase Storage,
    and update the session record with the photo URL.
    """
    db = get_db()

    session = queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Unsupported image format")

    raw_bytes = await file.read()

    try:
        processed_bytes = image_service.preprocess_photo(raw_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Image processing failed: {str(e)}")

    photo_url = storage_service.upload_session_photo(db, session_id, processed_bytes)

    queries.update_session(db, session_id, {"processed_photo_url": photo_url})

    return {"photo_url": photo_url, "session_id": session_id}
