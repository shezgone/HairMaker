import uuid
from supabase import Client


BUCKET_SESSION_PHOTOS = "session-photos"
BUCKET_SIMULATION_RESULTS = "simulation-results"
BUCKET_STYLE_CATALOG = "style-catalog"


def upload_session_photo(db: Client, session_id: str, image_bytes: bytes) -> str:
    """Upload preprocessed session photo and return public URL."""
    filename = f"{session_id}/photo_{uuid.uuid4().hex}.jpg"
    db.storage.from_(BUCKET_SESSION_PHOTOS).upload(
        filename,
        image_bytes,
        file_options={"content-type": "image/jpeg"},
    )
    return db.storage.from_(BUCKET_SESSION_PHOTOS).get_public_url(filename)


def upload_simulation_result(db: Client, job_id: str, image_bytes: bytes) -> str:
    """Upload simulation result image and return public URL."""
    filename = f"{job_id}/result_{uuid.uuid4().hex}.jpg"
    db.storage.from_(BUCKET_SIMULATION_RESULTS).upload(
        filename,
        image_bytes,
        file_options={"content-type": "image/jpeg"},
    )
    return db.storage.from_(BUCKET_SIMULATION_RESULTS).get_public_url(filename)


def download_image(db: Client, bucket: str, path: str) -> bytes:
    """Download a file from Supabase Storage."""
    return db.storage.from_(bucket).download(path)
