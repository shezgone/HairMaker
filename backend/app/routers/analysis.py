import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.db.client import get_db
from app.db import queries
from app.services import claude_service, storage_service

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
        if "```" in full_text:
            parts = full_text.split("```")
            full_text = parts[1] if len(parts) > 1 else full_text
            if full_text.startswith("json"):
                full_text = full_text[4:]

        try:
            analysis = json.loads(full_text.strip())
        except json.JSONDecodeError:
            yield f"data: {json.dumps({'error': 'Failed to parse analysis'})}\n\n"
            return

        # Save analysis to session
        queries.update_session(db, session_id, {"face_analysis": analysis})

        # Fetch recommendations
        recommended_tags = analysis.get("recommended_style_tags", [])
        face_shape = analysis.get("face_shape", "oval")
        gender = session.get("gender", "female")
        styles = queries.get_recommended_styles(db, face_shape, recommended_tags, gender)

        yield f"data: {json.dumps({'analysis': analysis, 'styles': styles, 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
