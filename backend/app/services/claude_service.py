import json
import logging
import re
import anthropic
from app.config import settings
from app.services.image_service import image_to_base64

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 얼굴형 분석과 헤어스타일 추천에 깊은 전문성을 가진 프로페셔널 헤어 디자인 컨설턴트입니다.
고객의 얼굴 사진을 분석하고, 헤어 디자이너가 상담에 활용할 수 있는 구조화된 JSON 추천을 반환합니다.
반드시 유효한 JSON만 반환하세요. 마크다운, 설명, 코드 블록은 포함하지 마세요."""

ANALYSIS_PROMPT = """이 고객 사진을 주의 깊게 분석하고 다음 구조의 JSON 객체를 반환하세요:

{
  "face_shape": "oval|round|square|heart|diamond|oblong|triangle",
  "face_shape_confidence": <float 0.0-1.0>,
  "facial_features": {
    "forehead_width": "narrow|medium|wide",
    "jaw_width": "narrow|medium|wide",
    "cheekbone_prominence": "low|medium|high",
    "face_length": "short|medium|long"
  },
  "current_hair_estimate": "<현재 헤어스타일에 대한 간단한 한국어 설명>",
  "recommended_style_tags": ["<태그1>", "<태그2>", ...],
  "avoid_style_tags": ["<태그1>", "<태그2>", ...],
  "consultation_summary": "<디자이너가 고객에게 읽어줄 수 있는 자연스러운 2-3문장. 얼굴형 특징과 어울리는 스타일을 친근한 전문가 톤으로 한국어로 설명>"
}

스타일 태그 예시: "볼륨감", "턱라인 보완", "얼굴 길어보이게", "얼굴 감싸기", "관리 편함",
"넓이감", "이마 밸런스", "각진부분 완화", "질감 살리기", "광대뼈 강조"

정확하되 따뜻한 톤을 유지하세요. consultation_summary는 임상적 분석이 아니라 친근한 전문가의 조언처럼 느껴져야 합니다.
모든 텍스트 값은 반드시 한국어로 작성하세요. JSON key 이름과 face_shape 값(oval, round 등)은 영문으로 유지하세요."""


async def analyze_face(image_bytes: bytes) -> dict:
    """
    Send face photo to Claude claude-sonnet-4-6 for analysis.
    Returns structured face analysis dict.
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    b64_image = image_to_base64(image_bytes)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": ANALYSIS_PROMPT,
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    raw = _strip_markdown_fences(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Claude face analysis response: %s\nRaw: %s", e, raw[:500])
        raise


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```) from Claude responses."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


HAIRSTYLE_ANALYSIS_PROMPT = """Describe this hairstyle for an AI image editor that will apply it to a different person's photo.

Focus ONLY on the hair. Be specific about what makes this style unique.

Describe:
1. Hair length for top, sides, and back (use cm)
2. Texture (straight, wavy, curly, permed)
3. Volume level (flat, medium, voluminous)
4. Bangs/fringe style and length
5. Side styling (undercut, tapered, two-block, natural)
6. Parting position
7. Hair color if not black
8. Key distinguishing feature of this style

Write ONE clear English paragraph as an image generation prompt. Be specific and descriptive, but realistic — avoid extreme words like "dramatic", "bold", "surging", "crashing". Describe the hairstyle accurately as a hairdresser would explain it to a colleague. Start with "Hairstyle:" """


async def analyze_hairstyle_reference(front_image_bytes: bytes, side_image_bytes: bytes | None = None) -> str:
    """레퍼런스 이미지를 Claude Vision으로 분석하여 상세 헤어스타일 설명을 생성."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    content = []

    # 정면 이미지
    b64_front = image_to_base64(front_image_bytes)
    content.append({
        "type": "image",
        "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_front},
    })

    if side_image_bytes:
        content.append({"type": "text", "text": "Above: front view. Below: side view of the same hairstyle."})
        b64_side = image_to_base64(side_image_bytes)
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": b64_side},
        })

    content.append({"type": "text", "text": HAIRSTYLE_ANALYSIS_PROMPT})

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": content}],
    )

    return message.content[0].text.strip()


async def analyze_face_stream(image_bytes: bytes):
    """
    Streaming version — yields text chunks as Claude generates them.
    The final chunk will be complete JSON.
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    b64_image = image_to_base64(image_bytes)

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64_image,
                        },
                    },
                    {"type": "text", "text": ANALYSIS_PROMPT},
                ],
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            yield text
