import io
import base64
from PIL import Image
import cv2
import numpy as np


def preprocess_photo(image_bytes: bytes, max_size: int = 1000) -> bytes:
    """
    Preprocess customer photo:
    1. Detect and crop to face region with padding
    2. Resize to max_size px on longest dimension
    3. Return as JPEG bytes
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Cannot decode image")

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

    if len(faces) > 0:
        x, y, w, h = faces[0]
        # 헤어스타일 시뮬레이션용 — 머리 위/옆 공간과 어깨까지 넉넉하게 포함
        pad_x = int(w * 1.2)   # 좌우 여백 (얼굴 너비의 120%)
        pad_top = int(h * 1.5) # 위 여백 (헤어스타일 공간 확보)
        pad_bot = int(h * 1.5) # 아래 여백 (어깨까지 포함)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_top)
        x2 = min(img.shape[1], x + w + pad_x)
        y2 = min(img.shape[0], y + h + pad_bot)
        img = img[y1:y2, x1:x2]

    # Resize to max_size while maintaining aspect ratio
    h, w = img.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Convert to PIL for JPEG encoding
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def image_to_base64(image_bytes: bytes) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def compose_side_by_side(person_bytes: bytes, reference_bytes: bytes, target_height: int = 800) -> bytes:
    """
    손님 사진과 헤어 참고 이미지를 좌우로 합성.
    두 이미지 높이를 target_height에 맞추고 가로로 이어붙임.
    FLUX에 전달해 "오른쪽 헤어를 왼쪽 사람에게 적용" 프롬프트와 함께 사용.
    """
    def load_and_resize(data: bytes) -> Image.Image:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        ratio = target_height / img.height
        new_w = int(img.width * ratio)
        return img.resize((new_w, target_height), Image.LANCZOS)

    left = load_and_resize(person_bytes)
    right = load_and_resize(reference_bytes)

    # 구분선 4px 추가
    divider = Image.new("RGB", (4, target_height), (60, 60, 60))

    total_w = left.width + 4 + right.width
    canvas = Image.new("RGB", (total_w, target_height), (30, 30, 30))
    canvas.paste(left, (0, 0))
    canvas.paste(divider, (left.width, 0))
    canvas.paste(right, (left.width + 4, 0))

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
