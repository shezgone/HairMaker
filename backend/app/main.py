import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, sessions, photos, analysis, styles, simulate

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if settings.environment == "production" else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
# Quieten noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="HairMaker API",
    description="Hair style recommendation and simulation backend for hair salons",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(photos.router, prefix="/api/v1/sessions", tags=["photos"])
app.include_router(analysis.router, prefix="/api/v1/sessions", tags=["analysis"])
app.include_router(styles.router, prefix="/api/v1/styles", tags=["styles"])
app.include_router(simulate.router, prefix="/api/v1/simulate", tags=["simulate"])


@app.on_event("startup")
async def ensure_storage_buckets():
    """앱 시작 시 필수 storage 버킷이 존재하는지 확인하고, 없으면 생성한다."""
    from app.db.client import get_db
    db = get_db()
    required_buckets = {
        "session-photos": False,
        "simulation-results": False,
        "style-catalog": True,  # public bucket
    }
    try:
        existing = {b.name for b in db.storage.list_buckets()}
        for bucket_name, is_public in required_buckets.items():
            if bucket_name not in existing:
                db.storage.create_bucket(
                    bucket_name,
                    options={"public": is_public},
                )
                logger.info("Created storage bucket: %s (public=%s)", bucket_name, is_public)
    except Exception as e:
        logger.warning("Failed to ensure storage buckets: %s", e)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


logger.info("HairMaker API started (env=%s)", settings.environment)


@app.get("/debug/env-check")
async def debug_env():
    """임시 디버그 — 배포 후 삭제할 것"""
    from app.config import settings
    from supabase import create_client
    key = settings.supabase_service_role_key
    # 직접 Supabase admin API 테스트
    test_result = "untested"
    try:
        client = create_client(settings.supabase_url, key)
        res = client.auth.admin.create_user({
            "email": "railwaytest@debug.com",
            "password": "Test1234",
            "email_confirm": True,
        })
        client.auth.admin.delete_user(res.user.id)
        test_result = "SUCCESS"
    except Exception as e:
        test_result = f"FAIL: {str(e)[:200]}"
    return {
        "key_prefix": key[:15] if key else "MISSING",
        "key_length": len(key) if key else 0,
        "admin_create_user": test_result,
    }
