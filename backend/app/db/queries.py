import logging
from supabase import Client

logger = logging.getLogger(__name__)


def get_recommended_styles(
    db: Client,
    face_shape: str,
    compatible_tags: list[str],
    gender: str = "female",
    limit: int = 12,
    salon_id: str | None = None,
) -> list[dict]:
    """
    Query hairstyle catalog filtered by face_shape + gender and ranked by tag overlap
    with Claude's recommended_style_tags.
    gender: 'male' | 'female'  — 'unisex' styles always included for both genders.
    salon_id: filter styles belonging to the given salon.
    """
    try:
        query = (
            db.table("hairstyles")
            .select("*")
            .contains("face_shapes", [face_shape])
            .eq("is_active", True)
            .in_("gender", [gender, "unisex"])
        )
        if salon_id:
            query = query.eq("salon_id", salon_id)
        response = query.execute()
    except Exception as e:
        if "gender" in str(e):
            logger.info("gender column not found, falling back to unfiltered query")
            query = (
                db.table("hairstyles")
                .select("*")
                .contains("face_shapes", [face_shape])
                .eq("is_active", True)
            )
            if salon_id:
                query = query.eq("salon_id", salon_id)
            response = query.execute()
        else:
            logger.error("Failed to query recommended styles: %s", e)
            raise
    styles = response.data or []

    def score(style: dict) -> float:
        base = float((style.get("face_shape_scores") or {}).get(face_shape, 0.5))
        style_tags = set(style.get("style_tags") or [])
        overlap = len(style_tags.intersection(set(compatible_tags)))
        return base + overlap * 0.1

    styles.sort(key=score, reverse=True)
    return styles[:limit]


def get_style_by_id(db: Client, style_id: str, salon_id: str | None = None) -> dict | None:
    try:
        query = db.table("hairstyles").select("*").eq("id", style_id)
        if salon_id:
            query = query.eq("salon_id", salon_id)
        response = query.single().execute()
        return response.data
    except Exception as e:
        logger.error("Failed to get style %s: %s", style_id, e)
        return None


def get_styles_by_salon(db: Client, salon_id: str, limit: int = 50) -> list[dict]:
    """매장 소속 전체 스타일 목록 조회."""
    try:
        response = (
            db.table("hairstyles")
            .select("*")
            .eq("salon_id", salon_id)
            .eq("is_active", True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error("Failed to get styles for salon %s: %s", salon_id, e)
        return []


def create_session(db: Client, salon_id: str, designer_id: str, gender: str = "female") -> dict:
    try:
        response = (
            db.table("sessions")
            .insert({"salon_id": salon_id, "designer_id": designer_id, "gender": gender, "status": "active"})
            .execute()
        )
    except Exception as e:
        if "gender" in str(e):
            logger.info("gender column not found in sessions, falling back without gender")
            response = (
                db.table("sessions")
                .insert({"salon_id": salon_id, "designer_id": designer_id, "status": "active"})
                .execute()
            )
        else:
            raise
    return response.data[0]


def get_session(db: Client, session_id: str) -> dict | None:
    try:
        response = db.table("sessions").select("*").eq("id", session_id).single().execute()
        return response.data
    except Exception as e:
        logger.error("Failed to get session %s: %s", session_id, e)
        return None


def update_session(db: Client, session_id: str, updates: dict) -> dict | None:
    try:
        response = (
            db.table("sessions")
            .update(updates)
            .eq("id", session_id)
            .execute()
        )
        if not response.data:
            logger.warning("update_session returned no data for session %s", session_id)
            return None
        return response.data[0]
    except Exception as e:
        logger.error("Failed to update session %s: %s", session_id, e)
        return None


def create_simulation_job(
    db: Client, session_id: str, style_id: str
) -> dict:
    response = (
        db.table("simulation_jobs")
        .insert(
            {
                "session_id": session_id,
                "style_id": style_id,
                "status": "pending",
            }
        )
        .execute()
    )
    return response.data[0]


def get_simulation_job(db: Client, job_id: str) -> dict | None:
    try:
        response = (
            db.table("simulation_jobs").select("*").eq("id", job_id).single().execute()
        )
        return response.data
    except Exception as e:
        logger.error("Failed to get simulation job %s: %s", job_id, e)
        return None


def update_simulation_job(db: Client, job_id: str, updates: dict) -> dict | None:
    try:
        response = (
            db.table("simulation_jobs")
            .update(updates)
            .eq("id", job_id)
            .execute()
        )
        if not response.data:
            logger.warning("update_simulation_job returned no data for job %s", job_id)
            return None
        return response.data[0]
    except Exception as e:
        logger.error("Failed to update simulation job %s: %s", job_id, e)
        return None


# ============================================================
# Default catalog copy
# ============================================================

DEMO_SALON_ID = "00000000-0000-0000-0000-000000000001"

# Fields to copy from source hairstyle (excludes id, created_at which are auto-generated)
_HAIRSTYLE_COPY_FIELDS = [
    "name",
    "description",
    "style_tags",
    "face_shapes",
    "face_shape_scores",
    "gender",
    "gender_presentation",
    "hair_length",
    "maintenance_level",
    "reference_image_url",
    "reference_images",
    "simulation_prompt",
    "is_active",
]


def copy_default_catalog(
    db: Client,
    source_salon_id: str,
    target_salon_id: str,
) -> int:
    """데모 salon의 헤어스타일 카탈로그를 새 salon으로 복사.

    Returns:
        복사된 스타일 수. 실패 시 0.
    """
    try:
        # 1. 소스 salon의 활성 스타일 조회
        response = (
            db.table("hairstyles")
            .select("*")
            .eq("salon_id", source_salon_id)
            .eq("is_active", True)
            .execute()
        )
        source_styles = response.data or []

        if not source_styles:
            logger.warning(
                "No styles found in source salon %s to copy", source_salon_id
            )
            return 0

        # 2. 타겟 salon에 이미 존재하는 스타일 이름 조회 (중복 방지)
        existing_res = (
            db.table("hairstyles")
            .select("name")
            .eq("salon_id", target_salon_id)
            .execute()
        )
        existing_names = {s["name"] for s in (existing_res.data or [])}

        # 3. salon_id를 교체하여 새 레코드 생성 (중복 이름 제외)
        new_rows = []
        for style in source_styles:
            if style.get("name") in existing_names:
                continue
            row = {"salon_id": target_salon_id}
            for field in _HAIRSTYLE_COPY_FIELDS:
                if field in style:
                    row[field] = style[field]
            new_rows.append(row)

        if not new_rows:
            logger.info("No new styles to copy (all already exist in target salon)")
            return 0

        # 4. Bulk insert
        insert_res = db.table("hairstyles").insert(new_rows).execute()
        count = len(insert_res.data or [])
        logger.info(
            "Copied %d styles from salon %s to salon %s",
            count,
            source_salon_id,
            target_salon_id,
        )
        return count

    except Exception as e:
        logger.error(
            "Failed to copy catalog from salon %s to salon %s: %s",
            source_salon_id,
            target_salon_id,
            e,
        )
        return 0
