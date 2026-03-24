from supabase import Client


def get_recommended_styles(
    db: Client,
    face_shape: str,
    compatible_tags: list[str],
    gender: str = "female",
    limit: int = 12,
) -> list[dict]:
    """
    Query hairstyle catalog filtered by face_shape + gender and ranked by tag overlap
    with Claude's recommended_style_tags.
    gender: 'male' | 'female'  — 'unisex' styles always included for both genders.
    """
    # Include exact gender match + unisex (gender 컬럼 없으면 전체 조회)
    try:
        response = (
            db.table("hairstyles")
            .select("*")
            .contains("face_shapes", [face_shape])
            .eq("is_active", True)
            .in_("gender", [gender, "unisex"])
            .execute()
        )
    except Exception as e:
        if "gender" in str(e):
            response = (
                db.table("hairstyles")
                .select("*")
                .contains("face_shapes", [face_shape])
                .eq("is_active", True)
                .execute()
            )
        else:
            raise
    styles = response.data or []

    def score(style: dict) -> float:
        base = float((style.get("face_shape_scores") or {}).get(face_shape, 0.5))
        style_tags = set(style.get("style_tags") or [])
        overlap = len(style_tags.intersection(set(compatible_tags)))
        return base + overlap * 0.1

    styles.sort(key=score, reverse=True)
    return styles[:limit]


def get_style_by_id(db: Client, style_id: str) -> dict | None:
    response = db.table("hairstyles").select("*").eq("id", style_id).single().execute()
    return response.data


def create_session(db: Client, salon_id: str, designer_id: str, gender: str = "female") -> dict:
    try:
        response = (
            db.table("sessions")
            .insert({"salon_id": salon_id, "designer_id": designer_id, "gender": gender, "status": "active"})
            .execute()
        )
    except Exception as e:
        if "gender" in str(e):
            # gender 컬럼이 아직 없는 경우 fallback
            response = (
                db.table("sessions")
                .insert({"salon_id": salon_id, "designer_id": designer_id, "status": "active"})
                .execute()
            )
        else:
            raise
    return response.data[0]


def get_session(db: Client, session_id: str) -> dict | None:
    response = db.table("sessions").select("*").eq("id", session_id).single().execute()
    return response.data


def update_session(db: Client, session_id: str, updates: dict) -> dict:
    response = (
        db.table("sessions")
        .update(updates)
        .eq("id", session_id)
        .execute()
    )
    return response.data[0]


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
    response = (
        db.table("simulation_jobs").select("*").eq("id", job_id).single().execute()
    )
    return response.data


def update_simulation_job(db: Client, job_id: str, updates: dict) -> dict:
    response = (
        db.table("simulation_jobs")
        .update(updates)
        .eq("id", job_id)
        .execute()
    )
    return response.data[0]
