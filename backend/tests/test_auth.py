"""
Tests for /api/v1/auth endpoints.
Covers: register, login, refresh, /me, social login.
"""

import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

from tests.conftest import MOCK_DESIGNER, MockQueryBuilder, MockSupabaseClient


# ─── POST /api/v1/auth/register ──────────────────────────────────────


class TestRegister:
    """회원가입 API 테스트."""

    @pytest.mark.anyio
    async def test_register_success(self, client: AsyncClient, mock_db):
        """정상 회원가입 — salon + designer 생성 후 토큰 반환."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@test.com",
                "password": "Test1234",
                "name": "새 디자이너",
                "salon_name": "새 살롱",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "new@test.com"
        assert data["user"]["name"] == "새 디자이너"
        assert data["user"]["role"] == "admin"
        assert "salon_id" in data["user"]
        assert data["user"]["salon_name"] == "새 살롱"

    @pytest.mark.anyio
    async def test_register_short_password(self, client: AsyncClient, mock_db):
        """비밀번호 8자 미만이면 422 에러."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@test.com",
                "password": "Ab1",
                "name": "테스트",
                "salon_name": "살롱",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_no_letter_password(self, client: AsyncClient, mock_db):
        """비밀번호에 영문자 없으면 422 에러."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "noalpha@test.com",
                "password": "12345678",
                "name": "테스트",
                "salon_name": "살롱",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_no_digit_password(self, client: AsyncClient, mock_db):
        """비밀번호에 숫자 없으면 422 에러."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "nodigit@test.com",
                "password": "Abcdefgh",
                "name": "테스트",
                "salon_name": "살롱",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_invalid_email(self, client: AsyncClient, mock_db):
        """잘못된 이메일 형식이면 422 에러."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "Test1234",
                "name": "테스트",
                "salon_name": "살롱",
            },
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_register_duplicate_email(self, client: AsyncClient, mock_db):
        """이미 등록된 이메일이면 409 에러."""
        mock_db.auth.admin.create_user = MagicMock(
            side_effect=Exception("User already registered")
        )
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@test.com",
                "password": "Test1234",
                "name": "테스트",
                "salon_name": "살롱",
            },
        )
        assert response.status_code == 409
        assert "이미 등록된" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_register_missing_fields(self, client: AsyncClient, mock_db):
        """필수 필드 누락 시 422 에러."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@test.com"},
        )
        assert response.status_code == 422


# ─── POST /api/v1/auth/login ─────────────────────────────────────────


class TestLogin:
    """로그인 API 테스트."""

    @pytest.mark.anyio
    async def test_login_success(self, client: AsyncClient, mock_db):
        """정상 로그인 — access_token + user 반환."""
        # Mock table() to return designer data on lookup
        mock_db.table = MagicMock(
            return_value=MockQueryBuilder(data=[MOCK_DESIGNER])
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "designer@test.com", "password": "Test1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == "designer@test.com"

    @pytest.mark.anyio
    async def test_login_wrong_password(self, client: AsyncClient, mock_db):
        """잘못된 비밀번호 — 401 에러."""
        mock_db.auth.sign_in_with_password = MagicMock(
            side_effect=Exception("Invalid login credentials")
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "designer@test.com", "password": "WrongPass1"},
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_login_missing_email(self, client: AsyncClient, mock_db):
        """이메일 누락 시 422 에러."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"password": "Test1234"},
        )
        assert response.status_code == 422


# ─── POST /api/v1/auth/refresh ───────────────────────────────────────


class TestRefreshToken:
    """토큰 갱신 API 테스트."""

    @pytest.mark.anyio
    async def test_refresh_success(self, client: AsyncClient, mock_db):
        """정상 토큰 갱신."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.anyio
    async def test_refresh_invalid_token(self, client: AsyncClient, mock_db):
        """유효하지 않은 refresh token — 401 에러."""
        mock_db.auth.refresh_session = MagicMock(
            side_effect=Exception("Invalid refresh token")
        )
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_refresh_missing_token(self, client: AsyncClient, mock_db):
        """refresh_token 필드 누락 시 422 에러."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={},
        )
        assert response.status_code == 422


# ─── GET /api/v1/auth/me ─────────────────────────────────────────────


class TestGetMe:
    """현재 사용자 정보 조회 API 테스트."""

    @pytest.mark.anyio
    async def test_me_success(self, client: AsyncClient, mock_auth_dependency):
        """인증된 사용자 정보 반환."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "designer@test.com"
        assert data["user"]["name"] == "테스트 디자이너"
        assert data["user"]["salon_name"] == "테스트 살롱"

    @pytest.mark.anyio
    async def test_me_no_token(self, client: AsyncClient):
        """토큰 없이 접근 시 401 에러."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


# ─── POST /api/v1/auth/social/login ──────────────────────────────────


class TestSocialLogin:
    """소셜 로그인 API 테스트."""

    @pytest.mark.anyio
    async def test_social_login_existing_user(self, client: AsyncClient, mock_db):
        """기존 사용자의 소셜 로그인 — 기존 designer 프로필 반환."""
        mock_db.table = MagicMock(
            return_value=MockQueryBuilder(data=[MOCK_DESIGNER])
        )
        response = await client.post(
            "/api/v1/auth/social/login",
            json={"access_token": "social-access-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["access_token"] == "social-access-token"

    @pytest.mark.anyio
    async def test_social_login_invalid_token(self, client: AsyncClient, mock_db):
        """유효하지 않은 소셜 토큰 — 401 에러."""
        mock_db.auth.get_user = MagicMock(
            side_effect=Exception("Invalid token")
        )
        response = await client.post(
            "/api/v1/auth/social/login",
            json={"access_token": "invalid-social-token"},
        )
        assert response.status_code == 401
