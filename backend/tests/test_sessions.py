"""
Tests for /api/v1/sessions endpoints.
Covers: session CRUD, ownership verification (multi-tenant isolation),
notes update, style selection, summary.
"""

import pytest
from unittest.mock import patch, MagicMock, ANY
from httpx import AsyncClient

from tests.conftest import MOCK_SESSION, MOCK_STYLE, MockQueryBuilder


# ─── POST /api/v1/sessions ───────────────────────────────────────────


class TestCreateSession:
    """세션 생성 API 테스트."""

    @pytest.mark.anyio
    async def test_create_session_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """정상 세션 생성 — salon_id와 designer_id가 현재 사용자 기준."""
        with patch("app.routers.sessions.queries.create_session") as mock_create:
            mock_create.return_value = MOCK_SESSION.copy()
            response = await client.post(
                "/api/v1/sessions",
                json={"gender": "female"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["salon_id"] == "salon-001"
        assert data["gender"] == "female"
        # Verify it was called with correct salon/designer IDs
        mock_create.assert_called_once_with(ANY, "salon-001", "designer-001", "female")

    @pytest.mark.anyio
    async def test_create_session_male(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """남성 고객 세션 생성."""
        with patch("app.routers.sessions.queries.create_session") as mock_create:
            male_session = {**MOCK_SESSION, "gender": "male"}
            mock_create.return_value = male_session
            response = await client.post(
                "/api/v1/sessions",
                json={"gender": "male"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        assert response.json()["gender"] == "male"

    @pytest.mark.anyio
    async def test_create_session_default_gender(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """gender 생략 시 기본값 female."""
        with patch("app.routers.sessions.queries.create_session") as mock_create:
            mock_create.return_value = MOCK_SESSION.copy()
            response = await client.post(
                "/api/v1/sessions",
                json={},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        mock_create.assert_called_once_with(ANY, "salon-001", "designer-001", "female")

    @pytest.mark.anyio
    async def test_create_session_no_auth(self, client: AsyncClient, mock_db):
        """인증 없이 세션 생성 시 401."""
        response = await client.post(
            "/api/v1/sessions",
            json={"gender": "female"},
        )
        assert response.status_code == 401


# ─── GET /api/v1/sessions ────────────────────────────────────────────


class TestListSessions:
    """세션 목록 조회 API 테스트."""

    @pytest.mark.anyio
    async def test_list_sessions_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """현재 디자이너의 salon에 속한 세션 목록 반환."""
        mock_db._tables["sessions"] = [MOCK_SESSION]
        response = await client.get(
            "/api/v1/sessions",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data

    @pytest.mark.anyio
    async def test_list_sessions_empty(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """세션 없을 때 빈 목록 반환."""
        mock_db._tables["sessions"] = []
        response = await client.get(
            "/api/v1/sessions",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["sessions"] == []


# ─── GET /api/v1/sessions/{session_id} ───────────────────────────────


class TestGetSession:
    """세션 상세 조회 API 테스트."""

    @pytest.mark.anyio
    async def test_get_session_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """자기 salon의 세션 조회 성공."""
        with patch("app.routers.sessions.queries.get_session") as mock_get:
            mock_get.return_value = MOCK_SESSION.copy()
            response = await client.get(
                "/api/v1/sessions/session-001",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        assert response.json()["id"] == "session-001"

    @pytest.mark.anyio
    async def test_get_session_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 세션 — 404."""
        with patch("app.routers.sessions.queries.get_session") as mock_get:
            mock_get.return_value = None
            response = await client.get(
                "/api/v1/sessions/nonexistent",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_session_other_salon(self, client: AsyncClient, mock_db, mock_auth_dependency_b):
        """다른 salon의 세션 접근 시 403 (멀티테넌트 격리)."""
        with patch("app.routers.sessions.queries.get_session") as mock_get:
            # session belongs to salon-001, but current user is salon-002
            mock_get.return_value = MOCK_SESSION.copy()
            response = await client.get(
                "/api/v1/sessions/session-001",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 403
        assert "접근 권한" in response.json()["detail"]


# ─── PATCH /api/v1/sessions/{session_id}/notes ───────────────────────


class TestUpdateNotes:
    """상담 메모 업데이트 API 테스트."""

    @pytest.mark.anyio
    async def test_update_notes_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """정상적으로 메모 업데이트."""
        with patch("app.routers.sessions.queries.get_session") as mock_get, \
             patch("app.routers.sessions.queries.update_session") as mock_update:
            mock_get.return_value = MOCK_SESSION.copy()
            updated = {**MOCK_SESSION, "consultation_notes": "새로운 메모"}
            mock_update.return_value = updated
            response = await client.patch(
                "/api/v1/sessions/session-001/notes",
                json={"consultation_notes": "새로운 메모"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        mock_update.assert_called_once_with(
            ANY, "session-001", {"consultation_notes": "새로운 메모"}
        )

    @pytest.mark.anyio
    async def test_update_notes_other_salon(self, client: AsyncClient, mock_db, mock_auth_dependency_b):
        """다른 salon의 세션 메모 수정 시 403."""
        with patch("app.routers.sessions.queries.get_session") as mock_get:
            mock_get.return_value = MOCK_SESSION.copy()
            response = await client.patch(
                "/api/v1/sessions/session-001/notes",
                json={"consultation_notes": "해킹 시도"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 403


# ─── PATCH /api/v1/sessions/{session_id}/style ───────────────────────


class TestSelectStyle:
    """스타일 선택 API 테스트."""

    @pytest.mark.anyio
    async def test_select_style_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """스타일 선택 시 세션 상태 completed로 변경."""
        with patch("app.routers.sessions.queries.get_session") as mock_get, \
             patch("app.routers.sessions.queries.update_session") as mock_update:
            mock_get.return_value = MOCK_SESSION.copy()
            mock_update.return_value = {
                **MOCK_SESSION,
                "selected_style_id": "style-001",
                "status": "completed",
            }
            response = await client.patch(
                "/api/v1/sessions/session-001/style",
                json={"style_id": "style-001"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        mock_update.assert_called_once_with(
            ANY, "session-001", {"selected_style_id": "style-001", "status": "completed"}
        )


# ─── GET /api/v1/sessions/{session_id}/summary ──────────────────────


class TestGetSummary:
    """세션 요약 API 테스트."""

    @pytest.mark.anyio
    async def test_summary_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """정상 세션 요약 조회."""
        session_with_style = {**MOCK_SESSION, "selected_style_id": "style-001"}
        with patch("app.routers.sessions.queries.get_session") as mock_get, \
             patch("app.routers.sessions.queries.get_style_by_id") as mock_style:
            mock_get.return_value = session_with_style
            mock_style.return_value = MOCK_STYLE.copy()
            # Mock the simulation_jobs query
            mock_db._tables["simulation_jobs"] = []
            response = await client.get(
                "/api/v1/sessions/session-001/summary",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "session" in data
        assert "selected_style" in data
        assert "simulation_results" in data

    @pytest.mark.anyio
    async def test_summary_no_style_selected(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """스타일 미선택 시 selected_style은 null."""
        with patch("app.routers.sessions.queries.get_session") as mock_get:
            mock_get.return_value = MOCK_SESSION.copy()
            mock_db._tables["simulation_jobs"] = []
            response = await client.get(
                "/api/v1/sessions/session-001/summary",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        assert response.json()["selected_style"] is None
