import uuid
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from app.db.client import get_db
from app.db import queries

router = APIRouter()


class UpdateStyleRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    simulation_prompt: str | None = None
    is_active: bool | None = None


@router.get("")
async def list_styles(
    face_shape: str | None = Query(None),
    tags: str | None = Query(None),
    limit: int = Query(12, ge=1, le=50),
):
    """
    List styles from catalog, optionally filtered by face_shape and tags.
    Tags should be comma-separated.
    """
    db = get_db()
    compatible_tags = [t.strip() for t in tags.split(",")] if tags else []

    if face_shape:
        styles = queries.get_recommended_styles(db, face_shape, compatible_tags, limit)
    else:
        response = (
            db.table("hairstyles")
            .select("*")
            .eq("is_active", True)
            .limit(limit)
            .execute()
        )
        styles = response.data or []

    return {"styles": styles, "total": len(styles)}


@router.get("/{style_id}")
async def get_style(style_id: str):
    db = get_db()
    style = queries.get_style_by_id(db, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    return style


@router.patch("/{style_id}")
async def update_style(style_id: str, body: UpdateStyleRequest):
    db = get_db()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = db.table("hairstyles").update(updates).eq("id", style_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Style not found")
    return result.data[0]


@router.post("/{style_id}/image")
async def upload_style_image(
    style_id: str,
    file: UploadFile = File(...),
    angle: str = Query("front", pattern="^(front|side)$"),
):
    """원장이 헤어스타일 참고 이미지를 직접 업로드. angle=front|side. style-catalog 버킷에 저장."""
    db = get_db()

    style = queries.get_style_by_id(db, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")

    content_type = file.content_type or "image/jpeg"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "jpg"
    path = f"{style_id}/{angle}.{ext}"
    image_bytes = await file.read()

    bucket = "style-catalog"
    db.storage.from_(bucket).upload(
        path,
        image_bytes,
        file_options={"content-type": content_type, "upsert": "true"},
    )

    result = db.storage.from_(bucket).get_public_url(path)
    public_url = result if isinstance(result, str) else result.get("publicUrl", "")

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
        }).eq("id", style_id).execute()
    else:  # side
        if len(current_images) == 0:
            current_images.append("")  # front placeholder
        if len(current_images) == 1:
            current_images.append(public_url)
        else:
            current_images[1] = public_url
        db.table("hairstyles").update({
            "reference_images": current_images,
        }).eq("id", style_id).execute()

    return {"angle": angle, "url": public_url}
