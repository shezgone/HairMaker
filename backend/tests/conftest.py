"""
Shared test fixtures for HairMaker backend tests.

All external services (Supabase DB, Auth, Storage, Claude API, Replicate API) are mocked.
A real FastAPI TestClient is created via httpx.AsyncClient.
"""

import uuid
from unittest.mock import MagicMock, patch
from typing import Generator

import pytest
from httpx import AsyncClient, ASGITransport

# --- Patch settings BEFORE importing app ---
import os

_ENV = {
    "ANTHROPIC_API_KEY": "test-anthropic-key",
    "REPLICATE_API_TOKEN": "test-replicate-token",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
    "REDIS_URL": "redis://localhost:6379",
    "CORS_ORIGINS": "http://localhost:3000",
    "ENVIRONMENT": "test",
}

for k, v in _ENV.items():
    os.environ[k] = v


# ─── Mock Supabase Helpers ────────────────────────────────────────────

class MockExecuteResult:
    """Simulates a Supabase .execute() result."""
    def __init__(self, data):
        self.data = data


class MockQueryBuilder:
    """Chainable mock that simulates Supabase PostgREST query builder."""

    def __init__(self, data=None):
        self._data = data if data is not None else []
        self._single = False

    def select(self, *args, **kwargs):
        return self

    def insert(self, data, **kwargs):
        if isinstance(data, dict):
            record = {"id": str(uuid.uuid4()), **data}
            self._data = [record]
        return self

    def update(self, data, **kwargs):
        if self._data:
            updated = []
            for rec in (self._data if isinstance(self._data, list) else [self._data]):
                updated.append({**rec, **data})
            self._data = updated
        return self

    def delete(self):
        return self

    def eq(self, *args, **kwargs):
        return self

    def in_(self, *args, **kwargs):
        return self

    def contains(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._single and isinstance(self._data, list) and self._data:
            return MockExecuteResult(self._data[0])
        return MockExecuteResult(self._data if self._data else [])


class MockStorageBucket:
    """Mock Supabase Storage bucket."""

    def upload(self, path, data, **kwargs):
        return {"Key": path}

    def download(self, path):
        return b"\xff\xd8\xff\xe0fake-jpeg-bytes"

    def get_public_url(self, path):
        return f"https://test.supabase.co/storage/v1/object/public/bucket/{path}"

    def create_signed_url(self, path, expires_in):
        return {"signedURL": f"https://test.supabase.co/signed/{path}?expires={expires_in}"}


class MockStorage:
    """Mock Supabase Storage client."""

    def from_(self, bucket_name):
        return MockStorageBucket()


class MockAuthAdmin:
    """Mock Supabase Auth admin."""

    def create_user(self, data):
        result = MagicMock()
        result.user = MagicMock()
        result.user.id = str(uuid.uuid4())
        result.user.email = data.get("email", "test@test.com")
        return result

    def delete_user(self, user_id):
        pass


class MockAuth:
    """Mock Supabase Auth."""

    def __init__(self):
        self.admin = MockAuthAdmin()

    def sign_in_with_password(self, data):
        result = MagicMock()
        result.user = MagicMock()
        result.user.id = "auth-user-id-123"
        result.session = MagicMock()
        result.session.access_token = "test-access-token"
        result.session.refresh_token = "test-refresh-token"
        return result

    def refresh_session(self, refresh_token):
        result = MagicMock()
        result.session = MagicMock()
        result.session.access_token = "new-access-token"
        result.session.refresh_token = "new-refresh-token"
        return result

    def get_user(self, token):
        result = MagicMock()
        result.user = MagicMock()
        result.user.id = "auth-user-id-123"
        result.user.email = "test@test.com"
        result.user.user_metadata = {"full_name": "Test User"}
        return result


class MockSupabaseClient:
    """Complete mock Supabase Client that matches real Supabase client interface."""

    def __init__(self):
        self.auth = MockAuth()
        self.storage = MockStorage()
        self._storage = None
        self._tables: dict[str, list[dict]] = {}
        self.postgrest = MagicMock()
        self.options = MagicMock()
        self.options.headers = {}

    def table(self, name):
        return MockQueryBuilder(data=self._tables.get(name, []))


# ─── Test Data Constants ──────────────────────────────────────────────

MOCK_DESIGNER = {
    "id": "designer-001",
    "auth_user_id": "auth-user-id-123",
    "email": "designer@test.com",
    "name": "테스트 디자이너",
    "role": "admin",
    "salon_id": "salon-001",
    "salons": {"id": "salon-001", "name": "테스트 살롱"},
}

MOCK_DESIGNER_B = {
    "id": "designer-002",
    "auth_user_id": "auth-user-id-456",
    "email": "other@test.com",
    "name": "다른 디자이너",
    "role": "admin",
    "salon_id": "salon-002",
    "salons": {"id": "salon-002", "name": "다른 살롱"},
}

MOCK_SESSION = {
    "id": "session-001",
    "salon_id": "salon-001",
    "designer_id": "designer-001",
    "gender": "female",
    "status": "active",
    "processed_photo_url": "https://test.supabase.co/storage/v1/object/public/session-photos/session-001/photo.jpg",
    "face_analysis": None,
    "personal_color": None,
    "selected_style_id": None,
    "consultation_notes": "",
    "created_at": "2026-03-31T00:00:00Z",
}

MOCK_STYLE = {
    "id": "style-001",
    "salon_id": "salon-001",
    "name": "내추럴 레이어드 컷",
    "description": "자연스러운 레이어드 컷",
    "style_tags": ["adds-volume", "frames-face"],
    "face_shapes": ["oval", "round"],
    "face_shape_scores": {"oval": 0.9, "round": 0.7},
    "hair_length": "medium",
    "maintenance_level": 2,
    "reference_image_url": "https://test.supabase.co/style.jpg",
    "reference_images": ["https://test.supabase.co/front.jpg", "https://test.supabase.co/side.jpg"],
    "simulation_prompt": "a natural layered cut with soft movement",
    "is_active": True,
    "gender": "female",
}

MOCK_SIM_JOB = {
    "id": "job-001",
    "session_id": "session-001",
    "style_id": "style-001",
    "status": "pending",
    "result_url": None,
    "error_message": None,
}


# ─── Fixtures ─────────────────────────────────────────────────────────

# All modules that import get_db need to be patched
_GET_DB_PATHS = [
    "app.db.client.get_db",
    "app.db.client.get_auth_client",
    "app.routers.auth.get_db",
    "app.routers.sessions.get_db",
    "app.routers.styles.get_db",
    "app.routers.simulate.get_db",
    "app.routers.photos.get_db",
    "app.routers.analysis.get_db",
]


@pytest.fixture
def mock_db():
    """Provide a MockSupabaseClient and patch get_db everywhere it's imported."""
    client = MockSupabaseClient()
    patches = [patch(path, return_value=client) for path in _GET_DB_PATHS]
    for p in patches:
        p.start()
    yield client
    for p in patches:
        p.stop()


@pytest.fixture
def mock_auth_dependency():
    """Override get_current_user dependency to return MOCK_DESIGNER."""
    from app.deps import get_current_user
    from app.main import app

    async def override():
        return MOCK_DESIGNER.copy()

    app.dependency_overrides[get_current_user] = override
    yield MOCK_DESIGNER
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_auth_dependency_b():
    """Override get_current_user to return MOCK_DESIGNER_B (different salon)."""
    from app.deps import get_current_user
    from app.main import app

    async def override():
        return MOCK_DESIGNER_B.copy()

    app.dependency_overrides[get_current_user] = override
    yield MOCK_DESIGNER_B
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def client():
    """Async HTTP client for testing FastAPI app."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
