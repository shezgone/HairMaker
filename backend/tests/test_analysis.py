"""
Tests for /api/v1/sessions/{session_id}/analysis endpoint.
Covers: SSE streaming analysis, cached analysis, error cases.
"""

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

from tests.conftest import MOCK_SESSION, MOCK_STYLE


MOCK_ANALYSIS = {
    "face_shape": "oval",
    "face_shape_confidence": 0.85,
    "facial_features": {
        "forehead_width": "medium",
        "jaw_width": "narrow",
        "cheekbone_prominence": "medium",
        "face_length": "medium",
    },
    "current_hair_estimate": "어깨 길이의 직모",
    "recommended_style_tags": ["adds-volume", "frames-face"],
    "avoid_style_tags": ["adds-width"],
    "consultation_summary": "계란형 얼굴에 잘 어울리는 레이어드 컷을 추천드립니다.",
}

MOCK_PERSONAL_COLOR = {
    "season": "spring",
    "tone": "warm",
    "skin_tone": "밝은 아이보리",
    "undertone_description": "따뜻한 톤",
    "recommended_hair_colors": [
        {"name": "골드브라운", "hex": "#A0522D"},
    ],
    "avoid_hair_colors": [
        {"name": "블루블랙", "hex": "#1C1C2E"},
    ],
    "color_summary": "봄 웜톤으로 따뜻한 컬러가 잘 어울립니다.",
}


# ─── GET /api/v1/sessions/{session_id}/analysis (Cached) ─────────────


class TestAnalysisCached:
    """캐시된 분석 결과 반환 테스트."""

    @pytest.mark.anyio
    async def test_cached_analysis_returns_json(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """이미 분석된 세션은 SSE가 아닌 JSON 직접 반환."""
        session_with_analysis = {
            **MOCK_SESSION,
            "face_analysis": MOCK_ANALYSIS,
            "personal_color": MOCK_PERSONAL_COLOR,
            "gender": "female",
        }
        with patch("app.routers.analysis.queries.get_session") as mock_get, \
             patch("app.routers.analysis.queries.get_recommended_styles") as mock_styles:
            mock_get.return_value = session_with_analysis
            mock_styles.return_value = [MOCK_STYLE]

            response = await client.get(
                "/api/v1/sessions/session-001/analysis",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["done"] is True
        assert data["analysis"]["face_shape"] == "oval"
        assert data["personal_color"]["season"] == "spring"
        assert len(data["styles"]) > 0

    @pytest.mark.anyio
    async def test_cached_analysis_no_personal_color(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """퍼스널컬러 분석 없이 얼굴형 분석만 있는 경우."""
        session = {
            **MOCK_SESSION,
            "face_analysis": MOCK_ANALYSIS,
            "personal_color": None,
        }
        with patch("app.routers.analysis.queries.get_session") as mock_get, \
             patch("app.routers.analysis.queries.get_recommended_styles") as mock_styles:
            mock_get.return_value = session
            mock_styles.return_value = []

            response = await client.get(
                "/api/v1/sessions/session-001/analysis",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["personal_color"] is None


# ─── GET /api/v1/sessions/{session_id}/analysis (Error Cases) ────────


class TestAnalysisErrors:
    """분석 에러 케이스 테스트."""

    @pytest.mark.anyio
    async def test_analysis_session_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 세션 — 404."""
        with patch("app.routers.analysis.queries.get_session") as mock_get:
            mock_get.return_value = None
            response = await client.get(
                "/api/v1/sessions/nonexistent/analysis",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_analysis_other_salon(self, client: AsyncClient, mock_db, mock_auth_dependency_b):
        """다른 salon의 세션 분석 접근 시 403."""
        with patch("app.routers.analysis.queries.get_session") as mock_get:
            mock_get.return_value = MOCK_SESSION.copy()
            response = await client.get(
                "/api/v1/sessions/session-001/analysis",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 403

    @pytest.mark.anyio
    async def test_analysis_no_photo(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """사진 미업로드 시 400."""
        session_no_photo = {**MOCK_SESSION, "processed_photo_url": None}
        with patch("app.routers.analysis.queries.get_session") as mock_get:
            mock_get.return_value = session_no_photo
            response = await client.get(
                "/api/v1/sessions/session-001/analysis",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 400
        assert "사진" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_analysis_no_auth(self, client: AsyncClient, mock_db):
        """인증 없이 분석 요청 시 401."""
        response = await client.get("/api/v1/sessions/session-001/analysis")
        assert response.status_code == 401


# ─── Health Check ────────────────────────────────────────────────────


class TestHealth:
    """헬스체크 엔드포인트 테스트."""

    @pytest.mark.anyio
    async def test_health_check(self, client: AsyncClient):
        """헬스체크 엔드포인트 응답."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
