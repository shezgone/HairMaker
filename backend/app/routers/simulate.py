import asyncio
import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.db.client import get_db
from app.db import queries
from app.services import replicate_service, storage_service

router = APIRouter()


class StartSimulationRequest(BaseModel):
    session_id: str
    style_id: str
    model: str = "flux"  # "flux" | "hairfastgan"


@router.post("")
async def start_simulation(body: StartSimulationRequest, background_tasks: BackgroundTasks):
    """
    Queue an AI hair simulation job.
    Returns immediately with a job_id; client polls for status.
    """
    db = get_db()

    session = queries.get_session(db, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    photo_url = session.get("processed_photo_url")
    if not photo_url:
        raise HTTPException(status_code=400, detail="No photo uploaded for this session")

    style = queries.get_style_by_id(db, body.style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")

    # Generate signed URL so Replicate can access the private bucket photo (1 hour)
    bucket = "session-photos"
    path = photo_url.split(f"/{bucket}/")[1] if f"/{bucket}/" in photo_url else None
    if not path:
        raise HTTPException(status_code=400, detail="Invalid photo URL")
    signed = db.storage.from_(bucket).create_signed_url(path, 3600)
    signed_url = signed.get("signedURL") or signed.get("signed_url") or photo_url

    # Create job record
    job = queries.create_simulation_job(db, body.session_id, body.style_id)
    job_id = job["id"]

    # face_analysis에서 인물 묘사 추출 (identity drift 방지)
    face_analysis = session.get("face_analysis") or {}
    gender = session.get("gender", "female")

    # Start background task to submit to Replicate and poll for completion
    background_tasks.add_task(
        _run_simulation_job, job_id, signed_url, style, body.model, face_analysis, gender
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/{job_id}")
async def get_simulation_status(job_id: str):
    db = get_db()
    job = queries.get_simulation_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "status": job["status"],
        "result_url": job.get("result_url"),
        "error": job.get("error_message"),
    }


async def _run_simulation_job(job_id: str, photo_url: str, style: dict, model: str = "flux", face_analysis: dict = {}, gender: str = "female"):
    """
    Background task:
    1. Submit to Replicate (FLUX or HairFastGAN)
    2. Poll until done
    3. Download result and save to Supabase Storage
    4. Update job record
    """
    db = get_db()

    try:
        # Submit prediction
        if model == "flux-max":
            prediction_id = await replicate_service.start_simulation_max(photo_url, style, face_analysis, gender)
            model_name = "flux-kontext-max"
        else:
            prediction_id = await replicate_service.start_simulation(photo_url, style, face_analysis, gender)
            model_name = "flux-kontext-pro"

        queries.update_simulation_job(
            db,
            job_id,
            {"status": "processing", "job_id": prediction_id, "model_used": model_name},
        )

        # Poll for completion (max 3 minutes)
        for _ in range(60):
            await asyncio.sleep(3)
            result = await replicate_service.get_prediction_status(prediction_id)

            if result["status"] == "succeeded":
                image_bytes = await replicate_service.download_result_image(result["output"])
                result_url = storage_service.upload_simulation_result(db, job_id, image_bytes)
                queries.update_simulation_job(
                    db, job_id, {"status": "done", "result_url": result_url}
                )
                return

            if result["status"] in ("failed", "canceled"):
                queries.update_simulation_job(
                    db,
                    job_id,
                    {"status": "error", "error_message": result.get("error", "Unknown error")},
                )
                return

    except Exception as e:
        queries.update_simulation_job(
            db, job_id, {"status": "error", "error_message": str(e)}
        )
