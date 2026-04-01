import logging
import uuid

from supabase import Client

logger = logging.getLogger(__name__)

BUCKET_SESSION_PHOTOS = "session-photos"
BUCKET_SIMULATION_RESULTS = "simulation-results"
BUCKET_STYLE_CATALOG = "style-catalog"


def upload_session_photo(db: Client, session_id: str, image_bytes: bytes) -> str:
    """Upload preprocessed session photo and return public URL.

    Raises:
        RuntimeError: storage upload 실패 시
    """
    filename = f"{session_id}/photo_{uuid.uuid4().hex}.jpg"
    try:
        result = db.storage.from_(BUCKET_SESSION_PHOTOS).upload(
            filename,
            image_bytes,
            file_options={"content-type": "image/jpeg"},
        )
    except Exception as e:
        logger.error(
            "Storage upload failed for session %s: %s", session_id, e
        )
        raise RuntimeError(f"사진 업로드에 실패했습니다: {e}") from e

    # upload 결과 검증
    if result is None:
        logger.error(
            "Storage upload returned None for session %s, file %s",
            session_id,
            filename,
        )
        raise RuntimeError("사진 업로드에 실패했습니다: 빈 응답")

    public_url = db.storage.from_(BUCKET_SESSION_PHOTOS).get_public_url(filename)
    logger.info("Photo uploaded for session %s: %s", session_id, public_url)
    return public_url


def upload_simulation_result(db: Client, job_id: str, image_bytes: bytes) -> str:
    """Upload simulation result image and return public URL.

    Raises:
        RuntimeError: storage upload 실패 시
    """
    filename = f"{job_id}/result_{uuid.uuid4().hex}.jpg"
    try:
        result = db.storage.from_(BUCKET_SIMULATION_RESULTS).upload(
            filename,
            image_bytes,
            file_options={"content-type": "image/jpeg"},
        )
    except Exception as e:
        logger.error(
            "Storage upload failed for job %s: %s", job_id, e
        )
        raise RuntimeError(f"시뮬레이션 결과 업로드에 실패했습니다: {e}") from e

    if result is None:
        logger.error(
            "Storage upload returned None for job %s, file %s",
            job_id,
            filename,
        )
        raise RuntimeError("시뮬레이션 결과 업로드에 실패했습니다: 빈 응답")

    public_url = db.storage.from_(BUCKET_SIMULATION_RESULTS).get_public_url(filename)
    logger.info("Simulation result uploaded for job %s: %s", job_id, public_url)
    return public_url


def download_image(db: Client, bucket: str, path: str) -> bytes:
    """Download a file from Supabase Storage."""
    return db.storage.from_(bucket).download(path)
