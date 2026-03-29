import json
import logging
import re
import anthropic
from app.config import settings
from app.services.image_service import image_to_base64

logger = logging.getLogger(__name__)

COLOR_SYSTEM_PROMPT = """You are a certified personal color consultant specializing in Korean 퍼스널컬러 (seasonal color analysis) for hair salons.
Analyze the customer's photo to determine their seasonal color type and provide hair color recommendations.
Return ONLY valid JSON. No markdown, no explanation, no code blocks."""

COLOR_ANALYSIS_PROMPT = """Analyze this customer's skin tone, undertone, eye color, and natural hair color to determine their personal color season.

Return a JSON object with this exact structure:
{
  "season": "spring|summer|autumn|winter",
  "tone": "warm|cool",
  "skin_tone": "<brief Korean description of skin tone e.g. 밝은 복숭아빛, 쿨 핑크, 황금빛 베이지>",
  "undertone_description": "<1-2 sentences in Korean about their undertone characteristics>",
  "recommended_hair_colors": [
    {"name": "<Korean color name>", "description": "<brief Korean description>", "hex": "<#hex>"},
    {"name": "<Korean color name>", "description": "<brief Korean description>", "hex": "<#hex>"},
    {"name": "<Korean color name>", "description": "<brief Korean description>", "hex": "<#hex>"},
    {"name": "<Korean color name>", "description": "<brief Korean description>", "hex": "<#hex>"}
  ],
  "avoid_hair_colors": [
    {"name": "<Korean color name>", "hex": "<#hex>"},
    {"name": "<Korean color name>", "hex": "<#hex>"}
  ],
  "color_summary": "<2-3 natural sentences in Korean a designer can read to explain the personal color and recommended hair color direction>"
}

Season definitions:
- spring (봄 웜톤): Warm, bright, clear. Best hair: 골든 브라운, 코퍼, 허니 블론드, 카라멜
- summer (여름 쿨톤): Cool, soft, muted. Best hair: 애쉬 브라운, 쿨 다크 브라운, 소프트 블랙, 라벤더 애쉬
- autumn (가을 웜톤): Warm, deep, earthy. Best hair: 다크 초콜릿, 오번, 딥 카라멜, 테라코타
- winter (겨울 쿨톤): Cool, vivid, stark. Best hair: 블루블랙, 차콜, 플래티넘, 쿨 애쉬

All text fields must be in Korean. Hex codes must be valid CSS hex values."""


def analyze_personal_color(image_bytes: bytes) -> dict:
    """
    Analyze personal color season from photo using Claude Vision.
    Returns structured personal color dict with hair color recommendations.
    Synchronous — call via asyncio.to_thread in async contexts.
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    b64_image = image_to_base64(image_bytes)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=COLOR_SYSTEM_PROMPT,
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
                    {"type": "text", "text": COLOR_ANALYSIS_PROMPT},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    raw = _strip_markdown_fences(raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse personal color response: %s\nRaw: %s", e, raw[:500])
        raise


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from Claude responses."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text
