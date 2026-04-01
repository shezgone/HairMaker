import logging
from typing import Optional

from fastapi import Header, HTTPException, Query

from app.db.client import get_db, get_auth_client

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> dict:
    """Bearer 토큰에서 현재 로그인 사용자(designer) 정보를 추출하는 dependency.

    Authorization 헤더 또는 query parameter 'token'으로 인증 가능.
    (EventSource/SSE는 커스텀 헤더를 지원하지 않아 query param 필요)
    """
    # 1. Authorization 헤더에서 토큰 추출
    bearer_token = None
    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization.split(" ", 1)[1]

    # 2. query param fallback (SSE용)
    actual_token = bearer_token or token

    if not actual_token:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")

    # 별도 auth 전용 클라이언트로 토큰 검증 (메인 client 오염 방지)
    auth_client = get_auth_client()
    try:
        user_res = auth_client.auth.get_user(actual_token)
        auth_user_id = user_res.user.id
    except Exception as e:
        logger.error("Token verification failed: %s", e)
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    # DB 조회는 메인 클라이언트 사용 (service_role 권한)
    db = get_db()
    try:
        designer_res = (
            db.table("designers")
            .select("*, salons(id, name)")
            .eq("auth_user_id", auth_user_id)
            .single()
            .execute()
        )
        return designer_res.data
    except Exception as e:
        logger.error("Designer lookup failed: %s", e)
        raise HTTPException(status_code=404, detail="디자이너 프로필을 찾을 수 없습니다.")
