import logging

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from app.db.client import get_db
from app.db import queries
from app.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateStyleRequest(BaseModel):
    name: str
    description: str | None = None
    style_tags: list[str] = []
    face_shapes: list[str] = []
    face_shape_scores: dict = {}
    gender: str = "female"
    hair_length: str | None = None
    maintenance_level: int = 2
    simulation_prompt: str | None = None


class UpdateStyleRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    gender: str | None = None
    hair_length: str | None = None
    simulation_prompt: str | None = None
    is_active: bool | None = None


@router.get("")
async def list_styles(
    face_shape: str | None = Query(None),
    tags: str | None = Query(None),
    gender: str | None = Query(None),
    limit: int = Query(12, ge=1, le=50),
    designer: dict = Depends(get_current_user),
):
    """
    List styles from the salon's catalog, optionally filtered by face_shape, tags, and gender.
    Tags should be comma-separated. Requires auth — salon_id derived from token.
    """
    db = get_db()
    salon_id = designer["salon_id"]
    compatible_tags = [t.strip() for t in tags.split(",")] if tags else []

    if face_shape:
        styles = queries.get_recommended_styles(
            db, face_shape, compatible_tags, gender or "female", limit, salon_id=salon_id
        )
    else:
        query = (
            db.table("hairstyles")
            .select("*")
            .eq("is_active", True)
            .eq("salon_id", salon_id)
        )
        if gender:
            query = query.in_("gender", [gender, "unisex"])
        response = query.limit(limit).execute()
        styles = response.data or []

    return {"styles": styles, "total": len(styles)}


@router.get("/{style_id}")
async def get_style(style_id: str, designer: dict = Depends(get_current_user)):
    """Get a single style — must belong to the designer's salon."""
    db = get_db()
    salon_id = designer["salon_id"]
    style = queries.get_style_by_id(db, style_id, salon_id=salon_id)
    if not style:
        raise HTTPException(status_code=404, detail="스타일을 찾을 수 없습니다.")
    return style


@router.post("")
async def create_style(body: CreateStyleRequest, designer: dict = Depends(get_current_user)):
    """새 헤어스타일 생성 — 현재 매장의 카탈로그에 추가. 인증 필요."""
    db = get_db()
    salon_id = designer["salon_id"]

    data = {
        "salon_id": salon_id,
        "name": body.name,
        "description": body.description,
        "style_tags": body.style_tags,
        "face_shapes": body.face_shapes,
        "face_shape_scores": body.face_shape_scores,
        "gender": body.gender,
        "hair_length": body.hair_length,
        "maintenance_level": body.maintenance_level,
        "simulation_prompt": body.simulation_prompt,
        "is_active": True,
    }
    try:
        result = db.table("hairstyles").insert(data).execute()
    except Exception as e:
        if "hairstyles_salon_name_unique" in str(e):
            raise HTTPException(status_code=409, detail="같은 이름의 스타일이 이미 존재합니다.")
        raise
    return result.data[0]


@router.patch("/{style_id}")
async def update_style(style_id: str, body: UpdateStyleRequest, designer: dict = Depends(get_current_user)):
    """스타일 수정 — 자기 매장 소속 스타일만 수정 가능. 인증 필요."""
    db = get_db()
    salon_id = designer["salon_id"]

    # Verify ownership
    style = queries.get_style_by_id(db, style_id, salon_id=salon_id)
    if not style:
        raise HTTPException(status_code=404, detail="스타일을 찾을 수 없습니다.")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다.")
    result = db.table("hairstyles").update(updates).eq("id", style_id).eq("salon_id", salon_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="스타일을 찾을 수 없습니다.")
    return result.data[0]


@router.delete("/{style_id}")
async def delete_style(style_id: str, designer: dict = Depends(get_current_user)):
    """스타일 삭제 (soft delete) — 자기 매장 소속만. 인증 필요."""
    db = get_db()
    salon_id = designer["salon_id"]

    style = queries.get_style_by_id(db, style_id, salon_id=salon_id)
    if not style:
        raise HTTPException(status_code=404, detail="스타일을 찾을 수 없습니다.")

    db.table("hairstyles").update({"is_active": False}).eq("id", style_id).eq("salon_id", salon_id).execute()
    return {"detail": "삭제되었습니다."}


@router.post("/{style_id}/image")
async def upload_style_image(
    style_id: str,
    file: UploadFile = File(...),
    angle: str = Query("front", pattern="^(front|side)$"),
    designer: dict = Depends(get_current_user),
):
    """원장이 헤어스타일 참고 이미지를 직접 업로드. angle=front|side. style-catalog 버킷에 저장. 인증 필요."""
    db = get_db()
    salon_id = designer["salon_id"]

    style = queries.get_style_by_id(db, style_id, salon_id=salon_id)
    if not style:
        raise HTTPException(status_code=404, detail="스타일을 찾을 수 없습니다.")

    content_type = file.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "jpg"
    path = f"{salon_id}/{style_id}/{angle}.{ext}"
    image_bytes = await file.read()

    bucket = "style-catalog"
    try:
        db.storage.from_(bucket).upload(
            path,
            image_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
    except Exception as e:
        logger.error("Storage upload failed for style %s: %s", style_id, e)
        raise HTTPException(status_code=500, detail=f"이미지 저장에 실패했습니다: {str(e)}")

    try:
        result = db.storage.from_(bucket).get_public_url(path)
        public_url = result if isinstance(result, str) else result.get("publicUrl", "")
    except Exception as e:
        logger.error("Failed to get public URL for style %s: %s", style_id, e)
        raise HTTPException(status_code=500, detail=f"이미지 URL 생성에 실패했습니다: {str(e)}")

    # reference_images 배열: index 0 = front, index 1 = side
    current_images: list = list(style.get("reference_images") or [])
    if angle == "front":
        if len(current_images) == 0:
            current_images.append(public_url)
        else:
            current_images[0] = public_url
        db.table("hairstyles").update({
            "reference_image_url": public_url,
            "reference_images": current_images,
            "simulation_prompt": None,  # 캐시 초기화 — 다음 시뮬레이션 시 재분석
        }).eq("id", style_id).eq("salon_id", salon_id).execute()
    else:  # side
        if len(current_images) == 0:
            current_images.append("")  # front placeholder
        if len(current_images) == 1:
            current_images.append(public_url)
        else:
            current_images[1] = public_url
        db.table("hairstyles").update({
            "reference_images": current_images,
            "simulation_prompt": None,  # 캐시 초기화
        }).eq("id", style_id).eq("salon_id", salon_id).execute()

    return {"angle": angle, "url": public_url}
