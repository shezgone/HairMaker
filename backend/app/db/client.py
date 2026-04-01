import threading

from supabase import create_client, Client
from app.config import settings

_client: Client | None = None
_auth_client: Client | None = None
_lock = threading.Lock()


def get_db() -> Client:
    """메인 DB/Storage 클라이언트. 항상 service_role 권한으로 동작.
    threading.Lock으로 헤더 리셋 시 race condition 방지."""
    global _client
    with _lock:
        if _client is None:
            _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
        # postgrest auth 리셋 (사용자 토큰 오염 방지)
        _client.postgrest.auth(settings.supabase_service_role_key)
        # storage headers도 service_role 토큰으로 리셋
        service_auth = f"Bearer {settings.supabase_service_role_key}"
        _client.options.headers["Authorization"] = service_auth
        # storage 프로퍼티 접근으로 lazy init을 트리거한 뒤 헤더 설정
        try:
            storage = _client.storage  # lazy init 트리거
            if hasattr(storage, '_headers'):
                storage._headers["Authorization"] = service_auth
            if hasattr(storage, 'session') and hasattr(storage.session, 'headers'):
                storage.session.headers["Authorization"] = service_auth
        except Exception:
            pass
    return _client


def get_auth_client() -> Client:
    """인증 작업 전용 클라이언트. 매번 새로 생성하여 auth 상태 오염을 원천 차단."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
