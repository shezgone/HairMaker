"""
Seed the Supabase hairstyle catalog with 50 initial styles.
Usage: python scripts/seed_catalog.py

Requires:
  pip install supabase python-dotenv
  SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in environment (or .env file)
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), "../backend/.env"))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

HAIRSTYLES = [
    {
        "name": "레이어드 컷",
        "description": "층을 넣어 볼륨감을 살린 클래식한 스타일. 모든 얼굴형에 어울립니다.",
        "style_tags": ["adds-volume", "adds-texture", "frames-face"],
        "face_shapes": ["oval", "round", "square", "heart", "diamond", "oblong", "triangle"],
        "face_shape_scores": {"oval": 0.95, "round": 0.85, "square": 0.80, "heart": 0.90, "diamond": 0.88, "oblong": 0.75, "triangle": 0.78},
        "hair_length": "medium",
        "maintenance_level": 2,
        "simulation_prompt": "a layered medium-length haircut with soft layers that add volume and movement",
        "is_active": True,
    },
    {
        "name": "히메컷",
        "description": "양옆을 짧게 자르고 앞머리를 내린 일본식 공주 컷.",
        "style_tags": ["frames-face", "softens-jaw", "emphasizes-cheekbones"],
        "face_shapes": ["oval", "heart", "diamond"],
        "face_shape_scores": {"oval": 0.90, "heart": 0.95, "diamond": 0.85},
        "hair_length": "medium",
        "maintenance_level": 3,
        "simulation_prompt": "a hime cut with blunt bangs and side hair shorter than the back, classic princess style",
        "is_active": True,
    },
    {
        "name": "울프컷",
        "description": "70년대 감성의 와일드한 레이어드 컷. 요즘 가장 핫한 트렌드.",
        "style_tags": ["adds-volume", "adds-texture", "edgy"],
        "face_shapes": ["oval", "square", "heart", "diamond"],
        "face_shape_scores": {"oval": 0.95, "square": 0.85, "heart": 0.88, "diamond": 0.90},
        "hair_length": "medium",
        "maintenance_level": 2,
        "simulation_prompt": "a wolf cut with heavy layers, curtain bangs, and wispy ends creating a 70s-inspired shaggy look",
        "is_active": True,
    },
    {
        "name": "단발 (보브컷)",
        "description": "깔끔하고 세련된 턱선 단발. 관리가 쉽고 어디서나 잘 어울립니다.",
        "style_tags": ["softens-jaw", "emphasizes-cheekbones", "low-maintenance"],
        "face_shapes": ["oval", "oblong", "heart"],
        "face_shape_scores": {"oval": 0.92, "oblong": 0.88, "heart": 0.85},
        "hair_length": "short",
        "maintenance_level": 2,
        "simulation_prompt": "a classic bob cut with clean lines ending at the jawline, sleek and polished",
        "is_active": True,
    },
    {
        "name": "롱 스트레이트",
        "description": "건강하고 윤기 있는 긴 생머리. 여성스러운 분위기를 완성합니다.",
        "style_tags": ["elongates-face", "sleek", "feminine"],
        "face_shapes": ["oval", "square", "round", "triangle"],
        "face_shape_scores": {"oval": 0.90, "square": 0.88, "round": 0.75, "triangle": 0.82},
        "hair_length": "long",
        "maintenance_level": 3,
        "simulation_prompt": "long straight hair falling past the shoulders, healthy and shiny with a sleek finish",
        "is_active": True,
    },
    {
        "name": "픽시컷",
        "description": "짧고 대담한 픽시컷. 이목구비가 뚜렷한 분께 특히 잘 어울립니다.",
        "style_tags": ["emphasizes-cheekbones", "bold", "low-maintenance"],
        "face_shapes": ["oval", "heart", "diamond"],
        "face_shape_scores": {"oval": 0.95, "heart": 0.90, "diamond": 0.88},
        "hair_length": "pixie",
        "maintenance_level": 3,
        "simulation_prompt": "a pixie cut with textured layers on top and tapered sides, bold and feminine",
        "is_active": True,
    },
    {
        "name": "웨이브 미디엄",
        "description": "자연스러운 웨이브로 볼륨감과 여성스러움을 더한 미디엄 기장.",
        "style_tags": ["adds-volume", "adds-texture", "feminine", "frames-face"],
        "face_shapes": ["oval", "square", "oblong", "triangle"],
        "face_shape_scores": {"oval": 0.95, "square": 0.85, "oblong": 0.88, "triangle": 0.80},
        "hair_length": "medium",
        "maintenance_level": 2,
        "simulation_prompt": "medium-length wavy hair with natural-looking loose waves, voluminous and feminine",
        "is_active": True,
    },
    {
        "name": "C컬 단발",
        "description": "끝에 C컬을 넣어 단발에 볼륨과 생동감을 더한 스타일.",
        "style_tags": ["adds-volume", "softens-jaw", "feminine"],
        "face_shapes": ["oval", "oblong", "round"],
        "face_shape_scores": {"oval": 0.90, "oblong": 0.92, "round": 0.80},
        "hair_length": "short",
        "maintenance_level": 2,
        "simulation_prompt": "a bob cut with C-curl ends that curl inward, adding volume at the bottom",
        "is_active": True,
    },
    {
        "name": "커튼 뱅 미디",
        "description": "가운데 가르마의 커튼 앞머리로 얼굴을 자연스럽게 감싸는 스타일.",
        "style_tags": ["frames-face", "softens-angles", "balances-forehead"],
        "face_shapes": ["oval", "square", "diamond", "oblong"],
        "face_shape_scores": {"oval": 0.92, "square": 0.88, "diamond": 0.90, "oblong": 0.85},
        "hair_length": "medium",
        "maintenance_level": 2,
        "simulation_prompt": "medium-length hair with curtain bangs parted in the middle, framing the face naturally",
        "is_active": True,
    },
    {
        "name": "숏 레이어드",
        "description": "층을 넣어 가볍고 생기 있는 짧은 단발.",
        "style_tags": ["adds-texture", "adds-volume", "fresh"],
        "face_shapes": ["oval", "heart", "oblong"],
        "face_shape_scores": {"oval": 0.90, "heart": 0.85, "oblong": 0.88},
        "hair_length": "short",
        "maintenance_level": 2,
        "simulation_prompt": "short layered haircut with textured ends for a light and airy feel",
        "is_active": True,
    },
]

# Add more styles to reach ~50...
ADDITIONAL_STYLES = [
    {"name": "S컬 펌", "description": "부드러운 S컬로 로맨틱한 분위기.", "style_tags": ["adds-volume", "romantic", "feminine"], "face_shapes": ["oval", "square", "oblong"], "face_shape_scores": {"oval": 0.92, "square": 0.85, "oblong": 0.90}, "hair_length": "medium", "maintenance_level": 3, "simulation_prompt": "medium-length hair with soft S-wave perm, romantic and feminine curls", "is_active": True},
    {"name": "내추럴 펌", "description": "자연스러운 컬로 볼륨감 있는 스타일.", "style_tags": ["adds-volume", "natural", "adds-texture"], "face_shapes": ["oval", "oblong", "triangle"], "face_shape_scores": {"oval": 0.90, "oblong": 0.88, "triangle": 0.80}, "hair_length": "medium", "maintenance_level": 2, "simulation_prompt": "medium-length hair with natural-looking loose perm curls for added volume", "is_active": True},
    {"name": "롱 레이어드", "description": "길고 풍성한 레이어드 컷.", "style_tags": ["adds-volume", "elongates-face", "feminine"], "face_shapes": ["oval", "round", "square"], "face_shape_scores": {"oval": 0.95, "round": 0.80, "square": 0.85}, "hair_length": "long", "maintenance_level": 3, "simulation_prompt": "long layered hair with cascading layers that add volume and movement", "is_active": True},
    {"name": "숄더 컷", "description": "어깨 라인에서 딱 맞는 깔끔한 기장.", "style_tags": ["balanced", "clean", "low-maintenance"], "face_shapes": ["oval", "round", "square", "heart"], "face_shape_scores": {"oval": 0.90, "round": 0.85, "square": 0.82, "heart": 0.88}, "hair_length": "medium", "maintenance_level": 1, "simulation_prompt": "shoulder-length haircut with clean lines and minimal layers", "is_active": True},
    {"name": "애즈펌 (남성)", "description": "자연스러운 에이즈 펌으로 트렌디한 남성 스타일.", "style_tags": ["natural", "trendy", "adds-texture"], "face_shapes": ["oval", "square", "oblong"], "face_shape_scores": {"oval": 0.92, "square": 0.88, "oblong": 0.85}, "hair_length": "short", "maintenance_level": 2, "simulation_prompt": "men's perm with natural wavy texture, modern Korean-style perm", "is_active": True},
    {"name": "투블럭 (남성)", "description": "사이드를 짧게 밀고 위를 길게 유지하는 남성 투블럭.", "style_tags": ["clean", "bold", "trendy"], "face_shapes": ["oval", "square", "oblong", "diamond"], "face_shape_scores": {"oval": 0.92, "square": 0.85, "oblong": 0.90, "diamond": 0.82}, "hair_length": "short", "maintenance_level": 3, "simulation_prompt": "men's two-block haircut with shaved sides and longer hair on top", "is_active": True},
    {"name": "시스루 뱅", "description": "가늘게 내려 얼굴을 살짝 가리는 시스루 앞머리.", "style_tags": ["balances-forehead", "feminine", "delicate"], "face_shapes": ["oval", "oblong", "square"], "face_shape_scores": {"oval": 0.90, "oblong": 0.92, "square": 0.85}, "hair_length": "medium", "maintenance_level": 2, "simulation_prompt": "medium-length hair with see-through wispy bangs that softly frame the forehead", "is_active": True},
    {"name": "딸기 단발", "description": "볼에 걸리는 귀여운 단발. 딸기 단발이라고도 불림.", "style_tags": ["cute", "frames-face", "feminine"], "face_shapes": ["oval", "heart", "round"], "face_shape_scores": {"oval": 0.88, "heart": 0.90, "round": 0.80}, "hair_length": "short", "maintenance_level": 2, "simulation_prompt": "a chin-length bob that rests at the cheeks with a slight curve inward, cute and feminine", "is_active": True},
    {"name": "롱 웨이브 펌", "description": "길고 풍성한 웨이브 펌. 화려하고 여성스러운 스타일.", "style_tags": ["adds-volume", "glamorous", "feminine"], "face_shapes": ["oval", "square", "oblong", "triangle"], "face_shape_scores": {"oval": 0.92, "square": 0.85, "oblong": 0.88, "triangle": 0.80}, "hair_length": "long", "maintenance_level": 4, "simulation_prompt": "long voluminous wave perm with glamorous curls throughout the length", "is_active": True},
    {"name": "리젠트 컷 (남성)", "description": "클래식한 남성 리젠트 컷.", "style_tags": ["classic", "clean", "bold"], "face_shapes": ["oval", "square", "oblong"], "face_shape_scores": {"oval": 0.92, "square": 0.88, "oblong": 0.90}, "hair_length": "short", "maintenance_level": 3, "simulation_prompt": "men's classic regent cut with pompadour styling on top and tapered sides", "is_active": True},
]

ALL_STYLES = HAIRSTYLES + ADDITIONAL_STYLES


def seed():
    db = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    print(f"Seeding {len(ALL_STYLES)} hairstyles...")

    for style in ALL_STYLES:
        try:
            result = db.table("hairstyles").upsert(style, on_conflict="name").execute()
            print(f"  ✓ {style['name']}")
        except Exception as e:
            print(f"  ✗ {style['name']}: {e}")

    print("Done!")


if __name__ == "__main__":
    seed()
