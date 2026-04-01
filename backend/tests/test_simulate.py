"""
Tests for /api/v1/simulate endpoints.
Covers: start simulation, status polling, ownership validation.
"""

import pytest
from unittest.mock import patch, MagicMock, ANY
from httpx import AsyncClient

from tests.conftest import MOCK_SESSION, MOCK_STYLE, MOCK_SIM_JOB


# ─── POST /api/v1/simulate ───────────────────────────────────────────


class TestStartSimulation:
    """시뮬레이션 시작 API 테스트."""

    @pytest.mark.anyio
    async def test_start_simulation_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """정상 시뮬레이션 시작 — job_id 반환."""
        session = {
            **MOCK_SESSION,
            "processed_photo_url": "https://test.supabase.co/storage/v1/object/public/session-photos/session-001/photo.jpg",
        }
        with patch("app.routers.simulate.queries.get_session") as mock_get_session, \
             patch("app.routers.simulate.queries.get_style_by_id") as mock_get_style, \
             patch("app.routers.simulate.queries.create_simulation_job") as mock_create_job:
            mock_get_session.return_value = session
            mock_get_style.return_value = MOCK_STYLE.copy()
            mock_create_job.return_value = MOCK_SIM_JOB.copy()

            response = await client.post(
                "/api/v1/simulate",
                json={
                    "session_id": "session-001",
                    "style_id": "style-001",
                    "model": "flux",
                },
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

    @pytest.mark.anyio
    async def test_start_simulation_no_photo(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """사진 미업로드 시 400."""
        session_no_photo = {**MOCK_SESSION, "processed_photo_url": None}
        with patch("app.routers.simulate.queries.get_session") as mock_get_session:
            mock_get_session.return_value = session_no_photo
            response = await client.post(
                "/api/v1/simulate",
                json={"session_id": "session-001", "style_id": "style-001"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 400
        assert "사진" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_start_simulation_session_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 세션 — 404."""
        with patch("app.routers.simulate.queries.get_session") as mock_get_session:
            mock_get_session.return_value = None
            response = await client.post(
                "/api/v1/simulate",
                json={"session_id": "nonexistent", "style_id": "style-001"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_start_simulation_other_salon(self, client: AsyncClient, mock_db, mock_auth_dependency_b):
        """다른 salon의 세션으로 시뮬레이션 시도 시 403."""
        with patch("app.routers.simulate.queries.get_session") as mock_get_session:
            mock_get_session.return_value = MOCK_SESSION.copy()  # salon-001
            response = await client.post(
                "/api/v1/simulate",
                json={"session_id": "session-001", "style_id": "style-001"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_start_simulation_style_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 스타일 — 404."""
        session = {
            **MOCK_SESSION,
            "processed_photo_url": "https://test.supabase.co/storage/v1/object/public/session-photos/session-001/photo.jpg",
        }
        with patch("app.routers.simulate.queries.get_session") as mock_get_session, \
             patch("app.routers.simulate.queries.get_style_by_id") as mock_get_style:
            mock_get_session.return_value = session
            mock_get_style.return_value = None
            response = await client.post(
                "/api/v1/simulate",
                json={"session_id": "session-001", "style_id": "nonexistent"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_start_simulation_invalid_model(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """지원하지 않는 model 값 — 422."""
        response = await client.post(
            "/api/v1/simulate",
            json={
                "session_id": "session-001",
                "style_id": "style-001",
                "model": "invalid-model",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_start_simulation_flux_max(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """flux-max 모델 선택."""
        session = {
            **MOCK_SESSION,
            "processed_photo_url": "https://test.supabase.co/storage/v1/object/public/session-photos/session-001/photo.jpg",
        }
        with patch("app.routers.simulate.queries.get_session") as mock_get_session, \
             patch("app.routers.simulate.queries.get_style_by_id") as mock_get_style, \
             patch("app.routers.simulate.queries.create_simulation_job") as mock_create_job:
            mock_get_session.return_value = session
            mock_get_style.return_value = MOCK_STYLE.copy()
            mock_create_job.return_value = MOCK_SIM_JOB.copy()

            response = await client.post(
                "/api/v1/simulate",
                json={
                    "session_id": "session-001",
                    "style_id": "style-001",
                    "model": "flux-max",
                },
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200


# ─── GET /api/v1/simulate/{job_id} ───────────────────────────────────


class TestGetSimulationStatus:
    """시뮬레이션 상태 조회 API 테스트."""

    @pytest.mark.anyio
    async def test_get_status_pending(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """pending 상태 조회."""
        with patch("app.routers.simulate.queries.get_simulation_job") as mock_get_job, \
             patch("app.routers.simulate.queries.get_session") as mock_get_session:
            mock_get_job.return_value = MOCK_SIM_JOB.copy()
            mock_get_session.return_value = MOCK_SESSION.copy()
            response = await client.get(
                "/api/v1/simulate/job-001",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["result_url"] is None

    @pytest.mark.anyio
    async def test_get_status_done(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """완료된 시뮬레이션 — result_url 포함."""
        done_job = {
            **MOCK_SIM_JOB,
            "status": "done",
            "result_url": "https://test.supabase.co/result.jpg",
        }
        with patch("app.routers.simulate.queries.get_simulation_job") as mock_get_job, \
             patch("app.routers.simulate.queries.get_session") as mock_get_session:
            mock_get_job.return_value = done_job
            mock_get_session.return_value = MOCK_SESSION.copy()
            response = await client.get(
                "/api/v1/simulate/job-001",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["result_url"] == "https://test.supabase.co/result.jpg"

    @pytest.mark.anyio
    async def test_get_status_error(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """에러 상태 시뮬레이션 — error 메시지 포함."""
        error_job = {
            **MOCK_SIM_JOB,
            "status": "error",
            "error_message": "시뮬레이션 실패",
        }
        with patch("app.routers.simulate.queries.get_simulation_job") as mock_get_job, \
             patch("app.routers.simulate.queries.get_session") as mock_get_session:
            mock_get_job.return_value = error_job
            mock_get_session.return_value = MOCK_SESSION.copy()
            response = await client.get(
                "/api/v1/simulate/job-001",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["error"] == "시뮬레이션 실패"

    @pytest.mark.anyio
    async def test_get_status_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 job — 404."""
        with patch("app.routers.simulate.queries.get_simulation_job") as mock_get_job:
            mock_get_job.return_value = None
            response = await client.get(
                "/api/v1/simulate/nonexistent",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_status_other_salon(self, client: AsyncClient, mock_db, mock_auth_dependency_b):
        """다른 salon의 시뮬레이션 작업 조회 시 403."""
        with patch("app.routers.simulate.queries.get_simulation_job") as mock_get_job, \
             patch("app.routers.simulate.queries.get_session") as mock_get_session:
            mock_get_job.return_value = MOCK_SIM_JOB.copy()
            mock_get_session.return_value = MOCK_SESSION.copy()  # salon-001
            response = await client.get(
                "/api/v1/simulate/job-001",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_start_simulation_no_auth(self, client: AsyncClient, mock_db):
        """인증 없이 시뮬레이션 시작 시 401."""
        response = await client.post(
            "/api/v1/simulate",
            json={"session_id": "session-001", "style_id": "style-001"},
        )
        assert response.status_code == 401
