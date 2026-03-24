import asyncio
import httpx
import replicate
from app.config import settings

# FLUX Kontext Pro — 빠름, 자연스러운 합성
FLUX_KONTEXT_PRO = "black-forest-labs/flux-kontext-pro"

# FLUX Kontext Max — Pro보다 강력, 얼굴 정체성 보존 최고 수준
FLUX_KONTEXT_MAX = "black-forest-labs/flux-kontext-max"

FLUX_KONTEXT_MODEL = FLUX_KONTEXT_PRO  # 기본값

# 텍스트 프롬프트만 사용할 때
SIMULATION_PROMPT_TEMPLATE = (
    "Replace ONLY the hair with: {style_description}. "
    "This is the SAME person — do NOT change their identity in any way. "
    "Face shape, face structure, bone structure, skin tone, skin texture, pores, wrinkles, age, eyes, eyebrows, nose, lips, ears, and jawline MUST remain pixel-perfect identical to the input photo. "
    "Do NOT beautify, retouch, slim, or alter the face in any way. "
    "Background, lighting direction, clothing, shoulders, and body MUST stay exactly the same. "
    "Only the hair region changes. The result must look like the same photo with a different hairstyle applied by a hairdresser."
)

# 참고 이미지 합성 방식 (좌: 손님, 우: 참고 헤어) 프롬프트
REFERENCE_PROMPT_TEMPLATE = (
    "This image shows TWO photos side by side separated by a dark divider. "
    "LEFT photo: the person whose hairstyle needs to change. "
    "RIGHT photo: the reference hairstyle to apply. "
    "Task: Apply EXACTLY the hairstyle shown in the RIGHT photo to the person in the LEFT photo. "
    "Copy the hair shape, length, volume, layers, and texture from the RIGHT photo precisely. "
    "The LEFT person's face, skin, age, facial features, background, clothing, and body MUST remain completely unchanged — pixel-perfect identical. "
    "Output only the LEFT person with the new hairstyle. Do NOT show two photos in the output."
)


def _set_token():
    import os
    os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token



def _build_person_description(face_analysis: dict, gender: str) -> str:
    """face_analysis 데이터로 인물 묘사 문자열 생성 — identity drift 방지용."""
    gender_str = "male" if gender == "male" else "female"

    face_shape = face_analysis.get("face_shape", "")
    features = face_analysis.get("facial_features") or {}
    jaw = features.get("jaw_width", "")
    forehead = features.get("forehead_width", "")

    desc = f"The person in this photo is an East Asian {gender_str}"
    if face_shape:
        desc += f" with a {face_shape} face shape"
    if jaw:
        desc += f", {jaw} jaw width"
    if forehead:
        desc += f", {forehead} forehead"
    desc += ". Preserve all East Asian facial features exactly — monolid eyes, flat nose bridge, and skin tone MUST remain unchanged."

    return desc


async def _submit_flux_with_reference(model: str, person_url: str, style: dict, face_analysis: dict = {}, gender: str = "female") -> str:
    """FLUX 텍스트 프롬프트 방식으로 헤어스타일 합성."""
    style_description = style.get("simulation_prompt") or f"a {style['name']} hairstyle"
    person_desc = _build_person_description(face_analysis, gender)
    prompt = person_desc + " " + SIMULATION_PROMPT_TEMPLATE.format(style_description=style_description)

    last_error: Exception | None = None
    for attempt in range(5):
        try:
            prediction = replicate.predictions.create(
                model=model,
                input={
                    "prompt": prompt,
                    "input_image": person_url,
                    "output_format": "jpg",
                    "output_quality": 95,
                    "safety_tolerance": 2,
                    "prompt_upsampling": False,
                },
            )
            return prediction.id
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "throttled" in err_str.lower() or "rate limit" in err_str.lower():
                last_error = e
                await asyncio.sleep(12 * (attempt + 1))
                continue
            raise
    raise last_error  # type: ignore


async def start_simulation(person_url: str, style: dict, face_analysis: dict = {}, gender: str = "female") -> str:
    """FLUX Kontext Pro — 빠름."""
    _set_token()
    return await _submit_flux_with_reference(FLUX_KONTEXT_PRO, person_url, style, face_analysis, gender)


async def start_simulation_max(person_url: str, style: dict, face_analysis: dict = {}, gender: str = "female") -> str:
    """FLUX Kontext Max — 얼굴 보존 최고 수준."""
    _set_token()
    return await _submit_flux_with_reference(FLUX_KONTEXT_MAX, person_url, style, face_analysis, gender)


async def get_prediction_status(prediction_id: str) -> dict:
    """
    Poll Replicate for the current status of a prediction.
    Returns dict with keys: status, output (URL when done), error
    """
    _set_token()

    prediction = replicate.predictions.get(prediction_id)
    result = {
        "status": prediction.status,  # starting | processing | succeeded | failed | canceled
        "output": None,
        "error": None,
    }

    if prediction.status == "succeeded":
        output = prediction.output
        # FLUX returns a URL or list of URLs
        if isinstance(output, list) and len(output) > 0:
            result["output"] = output[0]
        elif isinstance(output, str):
            result["output"] = output

    if prediction.status == "failed":
        result["error"] = str(prediction.error)

    return result


async def download_result_image(url: str) -> bytes:
    """Download the generated image bytes from Replicate's CDN."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30)
        response.raise_for_status()
        return response.content
