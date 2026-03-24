import json
import anthropic
from app.config import settings
from app.services.image_service import image_to_base64

SYSTEM_PROMPT = """You are a professional hair design consultant with deep expertise in face shape analysis and hairstyle recommendations.
Analyze customer face photos and return structured JSON recommendations that a hair designer can use to guide their consultation.
Return ONLY valid JSON. No markdown, no explanation, no code blocks."""

ANALYSIS_PROMPT = """Analyze this customer photo carefully and return a JSON object with the following structure:

{
  "face_shape": "oval|round|square|heart|diamond|oblong|triangle",
  "face_shape_confidence": <float 0.0-1.0>,
  "facial_features": {
    "forehead_width": "narrow|medium|wide",
    "jaw_width": "narrow|medium|wide",
    "cheekbone_prominence": "low|medium|high",
    "face_length": "short|medium|long"
  },
  "current_hair_estimate": "<brief description of current hair>",
  "recommended_style_tags": ["<tag1>", "<tag2>", ...],
  "avoid_style_tags": ["<tag1>", "<tag2>", ...],
  "consultation_summary": "<2-3 natural sentences a designer can read to the customer explaining their face shape and what styles will suit them best>"
}

Style tag examples: "adds-volume", "softens-jaw", "elongates-face", "frames-face", "low-maintenance",
"adds-width", "balances-forehead", "softens-angles", "adds-texture", "emphasizes-cheekbones"

Be precise but warm. The consultation_summary should feel like advice from a friendly expert, not a clinical analysis."""


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
    # Strip any accidental markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


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
