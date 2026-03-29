import asyncio
import json
import logging
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.db.client import get_db
from app.db import queries
from app.services import claude_service, color_service, storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{session_id}/analysis")
async def stream_analysis(session_id: str):
    """
    SSE endpoint: streams Claude's face analysis as it's generated,
    then saves the final JSON to the session record.
    """
    db = get_db()
    session = queries.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    photo_url = session.get("processed_photo_url")
    if not photo_url:
        raise HTTPException(status_code=400, detail="No photo uploaded for this session")

    # Download the preprocessed photo from Supabase Storage (authenticated)
    # Extract path from URL: .../session-photos/{path}
    bucket = "session-photos"
    path = photo_url.split(f"/{bucket}/")[1] if f"/{bucket}/" in photo_url else None
    if not path:
        raise HTTPException(status_code=400, detail="Invalid photo URL")
    image_bytes = db.storage.from_(bucket).download(path)

    async def event_generator():
        collected = []
        async for chunk in claude_service.analyze_face_stream(image_bytes):
            collected.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        full_text = "".join(collected)
        # Strip markdown fences if present
        full_text = full_text.strip()
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", full_text, re.DOTALL)
        if fence_match:
            full_text = fence_match.group(1).strip()

        try:
            analysis = json.loads(full_text.strip())
        except json.JSONDecodeError:
            logger.error("Failed to parse SSE analysis JSON: %s", full_text[:500])
            yield f"data: {json.dumps({'error': 'AI 응답을 파싱할 수 없습니다. 다시 시도해주세요.'})}\n\n"
            return

        # Run face analysis save + personal color analysis in parallel
        recommended_tags = analysis.get("recommended_style_tags", [])
        face_shape = analysis.get("face_shape", "oval")
        gender = session.get("gender", "female")

        personal_color_task = asyncio.to_thread(color_service.analyze_personal_color, image_bytes)
        styles_task = asyncio.to_thread(
            queries.get_recommended_styles, db, face_shape, recommended_tags, gender
        )

        results = await asyncio.gather(personal_color_task, styles_task, return_exceptions=True)
        personal_color = results[0] if not isinstance(results[0], Exception) else None
        if isinstance(results[0], Exception):
            logger.warning("Personal color analysis failed: %s", results[0])
        styles = results[1] if not isinstance(results[1], Exception) else []
        if isinstance(results[1], Exception):
            logger.warning("Style recommendation query failed: %s", results[1])

        # Save both analysis results to session
        queries.update_session(
            db,
            session_id,
            {"face_analysis": analysis, "personal_color": personal_color},
        )

        yield f"data: {json.dumps({'analysis': analysis, 'personal_color': personal_color, 'styles': styles, 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
