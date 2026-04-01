import asyncio
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, field_validator
from app.db.client import get_db
from app.db import queries
from app.deps import get_current_user
from app.services import replicate_service, storage_service, image_service, claude_service

logger = logging.getLogger(__name__)

router = APIRouter()


class StartSimulationRequest(BaseModel):
    session_id: str
    style_id: str
    model: str = "flux"

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if v not in ("flux", "flux-max"):
            raise ValueError("model must be 'flux' or 'flux-max'")
        return v


@router.post("")
async def start_simulation(body: StartSimulationRequest, background_tasks: BackgroundTasks, designer: dict = Depends(get_current_user)):
    """
    Queue an AI hair simulation job.
    Returns immediately with a job_id; client polls for status.
    """
    db = get_db()

    session = queries.get_session(db, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    if session.get("salon_id") != designer.get("salon_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    photo_url = session.get("processed_photo_url")
    if not photo_url:
        raise HTTPException(status_code=400, detail="사진이 아직 업로드되지 않았습니다.")

    salon_id = designer["salon_id"]
    style = queries.get_style_by_id(db, body.style_id, salon_id=salon_id)
    if not style:
        raise HTTPException(status_code=404, detail="스타일을 찾을 수 없습니다.")

    # Generate signed URL so Replicate can access the private bucket photo (1 hour)
    bucket = "session-photos"
    path = photo_url.split(f"/{bucket}/")[1] if f"/{bucket}/" in photo_url else None
    if not path:
        raise HTTPException(status_code=400, detail="잘못된 사진 URL입니다.")
    signed = db.storage.from_(bucket).create_signed_url(path, 3600)
    signed_url = signed.get("signedURL") or signed.get("signed_url") or photo_url

    # Create job record
    job = queries.create_simulation_job(db, body.session_id, body.style_id)
    job_id = job["id"]

    face_analysis = session.get("face_analysis") or {}
    gender = session.get("gender", "female")

    # 레퍼런스 이미지 정보 추출
    reference_image_url = style.get("reference_image_url")
    reference_images = style.get("reference_images") or []
    side_image_url = reference_images[1] if len(reference_images) > 1 and reference_images[1] else None

    logger.info(
        "Starting simulation job %s (model=%s, style=%s, has_reference=%s, has_side=%s)",
        job_id, body.model, body.style_id, bool(reference_image_url), bool(side_image_url),
    )

    background_tasks.add_task(
        _run_simulation_job, job_id, signed_url, style, body.model,
        face_analysis, gender, reference_image_url, side_image_url,
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/{job_id}")
async def get_simulation_status(job_id: str, designer: dict = Depends(get_current_user)):
    db = get_db()
    job = queries.get_simulation_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    # 시뮬레이션 작업의 세션 소유권 확인
    session = queries.get_session(db, job["session_id"])
    if session and session.get("salon_id") != designer.get("salon_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    return {
        "job_id": job_id,
        "status": job["status"],
        "result_url": job.get("result_url"),
        "error": job.get("error_message"),
    }


def _safe_update_job(db, job_id: str, updates: dict):
    """Update simulation job with error fallback to prevent silent failures."""
    try:
        queries.update_simulation_job(db, job_id, updates)
    except Exception as e:
        logger.critical("FAILED to update simulation job %s in DB: %s (updates=%s)", job_id, e, updates)


async def _download_image_bytes(url: str) -> bytes:
    """URL에서 이미지를 다운로드하여 bytes로 반환."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        return response.content


async def _run_simulation_job(
    job_id: str,
    photo_url: str,
    style: dict,
    model: str = "flux",
    face_analysis: dict | None = None,
    gender: str = "female",
    reference_image_url: str | None = None,
    side_image_url: str | None = None,
):
    """
    Background task:
    1. (Optional) Analyze reference image with Claude Vision to generate hairstyle prompt
    2. Submit to Replicate (FLUX Kontext Pro or Max) with customer photo + text prompt
    3. Poll until done — retry once on intermittent model errors
    4. Download result and save to Supabase Storage
    5. Update job record
    """
    if face_analysis is None:
        face_analysis = {}

    db = get_db()
    max_attempts = 2

    # 레퍼런스 프롬프트: 캐시(simulation_prompt) 우선, 없으면 Claude Vision 분석 후 캐싱
    reference_prompt: str | None = style.get("simulation_prompt")

    if not reference_prompt and reference_image_url:
        try:
            front_bytes = await _download_image_bytes(reference_image_url)
            side_bytes = None
            if side_image_url:
                side_bytes = await _download_image_bytes(side_image_url)
            reference_prompt = await claude_service.analyze_hairstyle_reference(front_bytes, side_bytes)
            logger.info("Job %s: generated reference prompt: %s", job_id, reference_prompt[:100])

            # DB에 캐싱 — 다음 시뮬레이션부터 Claude 호출 생략
            try:
                db.table("hairstyles").update({"simulation_prompt": reference_prompt}).eq("id", style["id"]).execute()
                logger.info("Cached simulation_prompt for style %s", style["id"])
            except Exception as cache_err:
                logger.warning("Failed to cache simulation_prompt: %s", cache_err)
        except Exception as e:
            logger.warning("Job %s: reference analysis failed, using text description: %s", job_id, e)
            reference_prompt = None

    for attempt in range(max_attempts):
        try:
            # Submit prediction
            if model == "flux-max":
                prediction_id = await replicate_service.start_simulation_max(
                    photo_url, style, face_analysis, gender, reference_prompt,
                )
                model_name = "flux-kontext-max"
            else:
                prediction_id = await replicate_service.start_simulation(
                    photo_url, style, face_analysis, gender, reference_prompt,
                )
                model_name = "flux-kontext-pro"

            logger.info("Job %s: submitted prediction %s (model=%s, attempt=%d)", job_id, prediction_id, model_name, attempt + 1)

            _safe_update_job(
                db, job_id,
                {"status": "processing", "job_id": prediction_id, "model_used": model_name},
            )

            # Poll for completion (max 3 minutes — 60 * 3s)
            for poll_count in range(60):
                await asyncio.sleep(3)
                result = await replicate_service.get_prediction_status(prediction_id)
                status = result["status"]

                if status == "succeeded":
                    logger.info("Job %s: prediction succeeded after %ds", job_id, (poll_count + 1) * 3)
                    image_bytes = await replicate_service.download_result_image(result["output"])
                    result_url = storage_service.upload_simulation_result(db, job_id, image_bytes)
                    _safe_update_job(db, job_id, {"status": "done", "result_url": result_url})
                    return

                if status in ("failed", "canceled"):
                    error_msg = result.get("error") or ""
                    logger.warning("Job %s: prediction %s (error=%s, attempt=%d)", job_id, status, error_msg, attempt + 1)
                    is_transient = "Error generating image" in error_msg or not error_msg
                    if is_transient and attempt < max_attempts - 1:
                        await asyncio.sleep(5)
                        break  # Break inner poll loop -> retry outer loop
                    _safe_update_job(
                        db, job_id,
                        {"status": "error", "error_message": error_msg or f"시뮬레이션이 {status} 상태로 종료되었습니다."},
                    )
                    return
            else:
                # Timed out
                logger.warning("Job %s: timed out after 3 minutes (attempt=%d)", job_id, attempt + 1)
                if attempt < max_attempts - 1:
                    await asyncio.sleep(5)
                    continue
                _safe_update_job(
                    db, job_id, {"status": "error", "error_message": "시뮬레이션 시간이 초과되었습니다 (3분)."}
                )
                return

        except Exception as e:
            logger.exception("Job %s: unexpected error (attempt=%d): %s", job_id, attempt + 1, e)
            err_str = str(e)
            if err_str.startswith("('") or err_str.startswith('("'):
                human_error = "이미지 생성 중 오류가 발생했습니다. 다시 시도해주세요."
            else:
                human_error = err_str
            if attempt < max_attempts - 1:
                await asyncio.sleep(5)
                continue
            _safe_update_job(db, job_id, {"status": "error", "error_message": human_error})
            return
