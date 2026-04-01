import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, field_validator

from app.db.client import get_db, get_auth_client
from app.db.queries import copy_default_catalog, DEMO_SALON_ID
from app.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    salon_name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("비밀번호에 영문자가 포함되어야 합니다.")
        if not re.search(r"[0-9]", v):
            raise ValueError("비밀번호에 숫자가 포함되어야 합니다.")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(body: RegisterRequest):
    """회원등록: Supabase Auth 유저 생성 + salon + designer 레코드 생성.
    실패 시 롤백: auth 유저 및 salon 삭제."""
    db = get_db()
    auth_user = None
    salon = None

    # 1. Supabase Auth로 유저 생성
    try:
        auth_res = db.auth.admin.create_user(
            {
                "email": body.email,
                "password": body.password,
                "email_confirm": True,
            }
        )
        auth_user = auth_res.user
    except Exception as e:
        error_msg = str(e)
        if "already" in error_msg.lower() or "duplicate" in error_msg.lower():
            raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")
        logger.error("Auth user creation failed: %s", e)
        raise HTTPException(status_code=400, detail="회원가입에 실패했습니다.")

    # 2. Salon 생성
    slug = body.email.split("@")[0].lower().replace(".", "-")
    try:
        salon_res = (
            db.table("salons")
            .insert({"name": body.salon_name, "slug": slug, "plan": "starter"})
            .execute()
        )
        salon = salon_res.data[0]
    except Exception:
        # slug 충돌 시 타임스탬프 추가
        import time
        slug = f"{slug}-{int(time.time())}"
        try:
            salon_res = (
                db.table("salons")
                .insert({"name": body.salon_name, "slug": slug, "plan": "starter"})
                .execute()
            )
            salon = salon_res.data[0]
        except Exception as e:
            # [P2-7] 롤백: salon 생성 실패 시 auth 유저 삭제
            logger.error("Salon creation failed: %s — rolling back auth user", e)
            _rollback_auth_user(db, auth_user.id)
            raise HTTPException(status_code=500, detail="매장 생성에 실패했습니다.")

    # 3. Designer 생성 (admin 권한)
    try:
        designer_res = (
            db.table("designers")
            .insert(
                {
                    "salon_id": salon["id"],
                    "auth_user_id": auth_user.id,
                    "email": body.email,
                    "name": body.name,
                    "role": "admin",
                }
            )
            .execute()
        )
        designer = designer_res.data[0]
    except Exception as e:
        # [P2-7] 롤백: designer 생성 실패 시 salon + auth 유저 삭제
        logger.error("Designer creation failed: %s — rolling back salon and auth user", e)
        _rollback_salon(db, salon["id"])
        _rollback_auth_user(db, auth_user.id)
        raise HTTPException(status_code=500, detail="디자이너 프로필 생성에 실패했습니다.")

    # 4. 기본 카탈로그 복사 (실패해도 회원가입 진행)
    try:
        copied = copy_default_catalog(db, DEMO_SALON_ID, salon["id"])
        logger.info("Copied %d default styles to new salon %s", copied, salon["id"])
    except Exception as e:
        logger.error("Default catalog copy failed for salon %s: %s", salon["id"], e)

    # 5. 로그인해서 토큰 발급 — 별도 클라이언트 사용 (메인 클라이언트 auth 상태 오염 방지)
    try:
        auth_client = get_auth_client()
        login_res = auth_client.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as e:
        logger.error("Auto-login after register failed: %s", e)
        raise HTTPException(status_code=500, detail="회원가입 후 자동 로그인에 실패했습니다.")

    return {
        "access_token": login_res.session.access_token,
        "refresh_token": login_res.session.refresh_token,
        "user": {
            "id": designer["id"],
            "auth_user_id": auth_user.id,
            "email": body.email,
            "name": body.name,
            "role": designer["role"],
            "salon_id": salon["id"],
            "salon_name": salon["name"],
        },
    }


def _rollback_auth_user(db, auth_user_id: str):
    """Auth 유저 삭제 (회원가입 롤백용)."""
    try:
        db.auth.admin.delete_user(auth_user_id)
        logger.info("Rolled back auth user %s", auth_user_id)
    except Exception as e:
        logger.critical("Failed to rollback auth user %s: %s", auth_user_id, e)


def _rollback_salon(db, salon_id: str):
    """Salon 삭제 (회원가입 롤백용)."""
    try:
        db.table("salons").delete().eq("id", salon_id).execute()
        logger.info("Rolled back salon %s", salon_id)
    except Exception as e:
        logger.critical("Failed to rollback salon %s: %s", salon_id, e)


@router.post("/login")
async def login(body: LoginRequest):
    """로그인: Supabase Auth로 인증 후 designer 정보 반환"""
    db = get_db()

    # 1. Supabase Auth 로그인 — 별도 클라이언트 사용 (메인 클라이언트 오염 방지)
    try:
        auth_client = get_auth_client()
        login_res = auth_client.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception as e:
        logger.error("Login failed: %s", e)
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    auth_user_id = login_res.user.id

    # 2. Designer 프로필 조회
    try:
        designer_res = (
            db.table("designers")
            .select("*, salons(id, name)")
            .eq("auth_user_id", auth_user_id)
            .single()
            .execute()
        )
        designer = designer_res.data
    except Exception as e:
        logger.error("Designer lookup failed for auth_user %s: %s", auth_user_id, e)
        raise HTTPException(status_code=404, detail="디자이너 프로필을 찾을 수 없습니다.")

    salon = designer.get("salons") or {}

    return {
        "access_token": login_res.session.access_token,
        "refresh_token": login_res.session.refresh_token,
        "user": {
            "id": designer["id"],
            "auth_user_id": auth_user_id,
            "email": designer["email"],
            "name": designer["name"],
            "role": designer["role"],
            "salon_id": designer["salon_id"],
            "salon_name": salon.get("name", ""),
        },
    }


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    """Refresh token으로 새 access token 발급."""

    try:
        auth_client = get_auth_client()
        refresh_res = auth_client.auth.refresh_session(body.refresh_token)
        session = refresh_res.session
    except Exception as e:
        logger.error("Token refresh failed: %s", e)
        raise HTTPException(status_code=401, detail="토큰 갱신에 실패했습니다. 다시 로그인해주세요.")

    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    }


class SocialLoginRequest(BaseModel):
    access_token: str
    refresh_token: str | None = None


@router.post("/social/login")
async def social_login(body: SocialLoginRequest):
    """
    소셜 로그인 콜백 처리
    - 프론트에서 Supabase OAuth 완료 후 access_token 전달
    - 토큰으로 유저 조회 -> designers 없으면 자동 생성 (salon 포함)
    """
    db = get_db()

    # 1. access_token으로 Supabase 유저 정보 조회 — 별도 클라이언트 사용
    try:
        auth_client = get_auth_client()
        user_res = auth_client.auth.get_user(body.access_token)
        auth_user = user_res.user
    except Exception as e:
        logger.error("Social login token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="유효하지 않은 소셜 로그인 토큰입니다.")

    auth_user_id = auth_user.id
    email = auth_user.email or ""
    metadata = auth_user.user_metadata or {}

    # 2. 기존 designer 조회
    try:
        designer_res = (
            db.table("designers")
            .select("*, salons(id, name)")
            .eq("auth_user_id", auth_user_id)
            .single()
            .execute()
        )
        designer = designer_res.data
        salon = designer.get("salons")
        # salons join이 null일 때 별도 조회
        if salon is None and designer.get("salon_id"):
            try:
                salon_res = (
                    db.table("salons")
                    .select("id, name")
                    .eq("id", designer["salon_id"])
                    .single()
                    .execute()
                )
                salon = salon_res.data
            except Exception:
                salon = {}
        salon = salon or {}
    except Exception:
        designer = None
        salon = None

    # 3. designer가 없으면 salon + designer 자동 생성
    if designer is None:
        # name: user_metadata에서 full_name -> name -> email 앞부분 순서로 사용
        display_name = (
            metadata.get("full_name")
            or metadata.get("name")
            or (email.split("@")[0] if email else "사용자")
        )

        # salon 생성
        slug = (email.split("@")[0] if email else auth_user_id[:8]).lower().replace(".", "-")
        try:
            salon_res = (
                db.table("salons")
                .insert({"name": "내 매장", "slug": slug, "plan": "starter"})
                .execute()
            )
            salon = salon_res.data[0]
        except Exception:
            import time
            slug = f"{slug}-{int(time.time())}"
            salon_res = (
                db.table("salons")
                .insert({"name": "내 매장", "slug": slug, "plan": "starter"})
                .execute()
            )
            salon = salon_res.data[0]

        # designer 생성
        try:
            designer_res = (
                db.table("designers")
                .insert(
                    {
                        "salon_id": salon["id"],
                        "auth_user_id": auth_user_id,
                        "email": email,
                        "name": display_name,
                        "role": "admin",
                    }
                )
                .execute()
            )
            designer = designer_res.data[0]
        except Exception as e:
            logger.error("Designer creation failed for social login %s: %s", auth_user_id, e)
            raise HTTPException(status_code=500, detail="디자이너 프로필 생성에 실패했습니다.")

        # 기본 카탈로그 복사 (실패해도 회원가입 진행)
        try:
            copied = copy_default_catalog(db, DEMO_SALON_ID, salon["id"])
            logger.info("Copied %d default styles to new salon %s (social)", copied, salon["id"])
        except Exception as e:
            logger.error("Default catalog copy failed for salon %s (social): %s", salon["id"], e)

    return {
        "access_token": body.access_token,
        "refresh_token": body.refresh_token,
        "user": {
            "id": designer["id"],
            "auth_user_id": auth_user_id,
            "email": designer["email"],
            "name": designer["name"],
            "role": designer["role"],
            "salon_id": designer["salon_id"],
            "salon_name": (salon or {}).get("name", ""),
        },
    }


@router.get("/me")
async def get_me(designer: dict = Depends(get_current_user)):
    """현재 로그인 사용자 정보 조회 (Bearer token)"""
    salon = designer.get("salons") or {}
    return {
        "user": {
            "id": designer["id"],
            "auth_user_id": designer["auth_user_id"],
            "email": designer["email"],
            "name": designer["name"],
            "role": designer["role"],
            "salon_id": designer["salon_id"],
            "salon_name": salon.get("name", ""),
        },
    }
