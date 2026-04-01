import asyncio
import base64
import logging
import httpx
import replicate
from app.config import settings

logger = logging.getLogger(__name__)

# FLUX Kontext Pro — 빠름, 자연스러운 합성
FLUX_KONTEXT_PRO = "black-forest-labs/flux-kontext-pro"

# FLUX Kontext Max — Pro보다 강력, 얼굴 정체성 보존 최고 수준
FLUX_KONTEXT_MAX = "black-forest-labs/flux-kontext-max"

FLUX_KONTEXT_MODEL = FLUX_KONTEXT_PRO  # 기본값

# 텍스트 프롬프트만 사용할 때
SIMULATION_PROMPT_TEMPLATE = (
    "Change this person's hairstyle to: {style_description}. "
    "The hair change should be clearly visible and noticeable. "
    "Keep the same face, skin, expression, background, and clothing unchanged."
)


def _set_token():
    import os
    os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token



def _build_person_description(face_analysis: dict, gender: str) -> str:
    """face_analysis 데이터로 인물 묘사 문자열 생성 — identity drift 방지용."""
    gender_str = "male" if gender == "male" else "female"
    face_shape = face_analysis.get("face_shape", "")

    desc = f"Photo of an East Asian {gender_str}"
    if face_shape:
        desc += f" with a {face_shape} face"
    desc += "."

    return desc


def _bytes_to_data_uri(image_bytes: bytes, media_type: str = "image/jpeg") -> str:
    """이미지 바이트를 data URI로 변환."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{media_type};base64,{b64}"


async def _submit_flux_with_reference(
    model: str,
    person_url: str,
    style: dict,
    face_analysis: dict | None = None,
    gender: str = "female",
    reference_prompt: str | None = None,
) -> str:
    """FLUX 헤어스타일 합성.

    reference_prompt가 있으면 Claude Vision이 분석한 헤어스타일 설명을 사용,
    없으면 style의 텍스트 설명을 사용.
    """
    if face_analysis is None:
        face_analysis = {}

    person_desc = _build_person_description(face_analysis, gender)

    # 프롬프트 우선순위: reference_prompt > description > style name
    if reference_prompt:
        style_description = reference_prompt
    else:
        style_description = style.get("description") or style.get("simulation_prompt") or f"a {style['name']} hairstyle"

    prompt = person_desc + " " + SIMULATION_PROMPT_TEMPLATE.format(style_description=style_description)
    input_image = person_url

    last_error: Exception | None = None
    for attempt in range(5):
        try:
            input_params = {
                "prompt": prompt,
                "input_image": input_image,
                "output_format": "jpg",
                "output_quality": 95,
                "safety_tolerance": 2,
                "prompt_upsampling": False,
            }
            # 원본 비율 유지를 위해 aspect_ratio 미지정 (모델이 input_image 비율 따름)
            prediction = await replicate.predictions.async_create(
                model=model,
                input=input_params,
            )
            return prediction.id
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "throttled" in err_str.lower() or "rate limit" in err_str.lower():
                logger.warning("Rate limited on attempt %d, retrying in %ds", attempt + 1, 12 * (attempt + 1))
                last_error = e
                await asyncio.sleep(12 * (attempt + 1))
                continue
            raise
    raise last_error  # type: ignore


async def start_simulation(
    person_url: str,
    style: dict,
    face_analysis: dict | None = None,
    gender: str = "female",
    reference_prompt: str | None = None,
) -> str:
    """FLUX Kontext Pro — 빠름."""
    _set_token()
    return await _submit_flux_with_reference(
        FLUX_KONTEXT_PRO, person_url, style, face_analysis, gender,
        reference_prompt,
    )


async def start_simulation_max(
    person_url: str,
    style: dict,
    face_analysis: dict | None = None,
    gender: str = "female",
    reference_prompt: str | None = None,
) -> str:
    """FLUX Kontext Max — 얼굴 보존 최고 수준."""
    _set_token()
    return await _submit_flux_with_reference(
        FLUX_KONTEXT_MAX, person_url, style, face_analysis, gender,
        reference_prompt,
    )


async def get_prediction_status(prediction_id: str) -> dict:
    """
    Poll Replicate for the current status of a prediction.
    Returns dict with keys: status, output (URL when done), error
    """
    _set_token()

    prediction = await replicate.predictions.async_get(prediction_id)
    status = prediction.status  # starting | processing | succeeded | failed | canceled

    result = {
        "status": status,
        "output": None,
        "error": None,
    }

    if status == "succeeded":
        output = prediction.output
        # FLUX returns a URL or list of URLs
        if isinstance(output, list) and len(output) > 0:
            result["output"] = output[0]
        elif isinstance(output, str):
            result["output"] = output

    elif status in ("failed", "canceled"):
        raw_error = prediction.error
        # prediction.error can be a tuple-repr string from the model itself — clean it up
        if raw_error:
            error_str = str(raw_error)
            if error_str.startswith("('") or error_str.startswith('("'):
                result["error"] = "이미지 생성 중 모델 오류가 발생했습니다."
            else:
                result["error"] = error_str
        else:
            result["error"] = f"시뮬레이션이 {status} 상태로 종료되었습니다."

    return result


async def download_result_image(url: str) -> bytes:
    """Download the generated image bytes from Replicate's CDN."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        return response.content
