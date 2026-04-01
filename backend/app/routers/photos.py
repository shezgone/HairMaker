import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.db.client import get_db
from app.db import queries
from app.deps import get_current_user
from app.services import image_service, storage_service

logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

router = APIRouter()


@router.post("/{session_id}/photo")
async def upload_photo(session_id: str, file: UploadFile = File(...), designer: dict = Depends(get_current_user)):
    """
    Accept raw photo upload, preprocess it, save to Supabase Storage,
    and update the session record with the photo URL.
    """
    db = get_db()

    session = queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    if session.get("salon_id") != designer.get("salon_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    raw_bytes = await file.read()
    if len(raw_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기가 10MB를 초과합니다.")

    try:
        processed_bytes = image_service.preprocess_photo(raw_bytes)
    except Exception as e:
        logger.error("Image preprocessing failed for session %s: %s", session_id, e)
        raise HTTPException(status_code=422, detail="이미지 처리에 실패했습니다. 다른 사진으로 시도해주세요.")

    try:
        photo_url = storage_service.upload_session_photo(db, session_id, processed_bytes)
    except RuntimeError as e:
        logger.error("Storage upload failed for session %s: %s", session_id, e)
        raise HTTPException(status_code=502, detail=str(e))

    queries.update_session(db, session_id, {"processed_photo_url": photo_url})

    return {"photo_url": photo_url, "session_id": session_id}
