"""
Tests for /api/v1/styles endpoints.
Covers: list, detail, create, update, delete, image upload, salon_id isolation.
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

from tests.conftest import MOCK_STYLE, MockQueryBuilder


# ─── GET /api/v1/styles ──────────────────────────────────────────────


class TestListStyles:
    """스타일 목록 조회 API 테스트."""

    @pytest.mark.anyio
    async def test_list_styles_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """salon 소속 스타일 목록 조회."""
        mock_db.table = MagicMock(
            return_value=MockQueryBuilder(data=[MOCK_STYLE])
        )
        response = await client.get(
            "/api/v1/styles",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data
        assert "total" in data
        assert data["total"] >= 0

    @pytest.mark.anyio
    async def test_list_styles_with_face_shape_filter(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """face_shape 필터 적용 시 get_recommended_styles 호출."""
        with patch("app.db.queries.get_recommended_styles") as mock_rec:
            mock_rec.return_value = [MOCK_STYLE]
            response = await client.get(
                "/api/v1/styles?face_shape=oval&tags=adds-volume",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        mock_rec.assert_called_once()
        # salon_id가 전달되었는지 확인
        call_kwargs = mock_rec.call_args
        assert call_kwargs[1].get("salon_id") == "salon-001" or call_kwargs[0][-1] == "salon-001"

    @pytest.mark.anyio
    async def test_list_styles_no_auth(self, client: AsyncClient, mock_db):
        """인증 없이 접근 시 401."""
        response = await client.get("/api/v1/styles")
        assert response.status_code == 401


# ─── GET /api/v1/styles/{style_id} ───────────────────────────────────


class TestGetStyle:
    """스타일 상세 조회 API 테스트."""

    @pytest.mark.anyio
    async def test_get_style_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """salon 소속 스타일 상세 조회."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = MOCK_STYLE.copy()
            response = await client.get(
                "/api/v1/styles/style-001",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        assert response.json()["id"] == "style-001"

    @pytest.mark.anyio
    async def test_get_style_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 스타일 — 404."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = None
            response = await client.get(
                "/api/v1/styles/nonexistent",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_get_style_other_salon(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """다른 salon의 스타일은 salon_id 필터링으로 찾을 수 없음."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            # get_style_by_id가 salon_id로 필터링하므로 None 반환
            mock_get.return_value = None
            response = await client.get(
                "/api/v1/styles/style-from-other-salon",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404


# ─── POST /api/v1/styles ─────────────────────────────────────────────


class TestCreateStyle:
    """스타일 생성 API 테스트."""

    @pytest.mark.anyio
    async def test_create_style_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """정상 스타일 생성."""
        mock_db.table = MagicMock(
            return_value=MockQueryBuilder(data=[{
                **MOCK_STYLE,
                "name": "새로운 컷",
            }])
        )
        response = await client.post(
            "/api/v1/styles",
            json={
                "name": "새로운 컷",
                "description": "깔끔한 단발",
                "gender": "female",
                "style_tags": ["low-maintenance"],
                "face_shapes": ["oval"],
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "새로운 컷"

    @pytest.mark.anyio
    async def test_create_style_missing_name(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """name 누락 시 422."""
        response = await client.post(
            "/api/v1/styles",
            json={"description": "설명만"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_create_style_duplicate_name(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """같은 이름의 스타일 중복 생성 시 409."""
        mock_builder = MockQueryBuilder()
        mock_builder.execute = MagicMock(
            side_effect=Exception("hairstyles_salon_name_unique")
        )
        mock_db.table = MagicMock(return_value=mock_builder)
        response = await client.post(
            "/api/v1/styles",
            json={"name": "중복 이름"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 409


# ─── PATCH /api/v1/styles/{style_id} ─────────────────────────────────


class TestUpdateStyle:
    """스타일 수정 API 테스트."""

    @pytest.mark.anyio
    async def test_update_style_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """정상 스타일 수정."""
        updated_style = {**MOCK_STYLE, "name": "수정된 이름"}
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = MOCK_STYLE.copy()
            mock_db.table = MagicMock(
                return_value=MockQueryBuilder(data=[updated_style])
            )
            response = await client.patch(
                "/api/v1/styles/style-001",
                json={"name": "수정된 이름"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_update_style_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 스타일 수정 시 404."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = None
            response = await client.patch(
                "/api/v1/styles/nonexistent",
                json={"name": "수정"},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_update_style_empty_body(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """수정할 필드 없을 때 400."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = MOCK_STYLE.copy()
            response = await client.patch(
                "/api/v1/styles/style-001",
                json={},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 400


# ─── DELETE /api/v1/styles/{style_id} ────────────────────────────────


class TestDeleteStyle:
    """스타일 삭제 API 테스트."""

    @pytest.mark.anyio
    async def test_delete_style_success(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """정상 스타일 soft delete."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = MOCK_STYLE.copy()
            mock_db.table = MagicMock(
                return_value=MockQueryBuilder(data=[{**MOCK_STYLE, "is_active": False}])
            )
            response = await client.delete(
                "/api/v1/styles/style-001",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        assert "삭제" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_delete_style_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 스타일 삭제 시 404."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = None
            response = await client.delete(
                "/api/v1/styles/nonexistent",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404

    @pytest.mark.anyio
    async def test_delete_style_other_salon(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """다른 salon의 스타일 삭제 시 salon_id 필터링으로 404."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = None  # salon_id 필터로 매칭 안됨
            response = await client.delete(
                "/api/v1/styles/other-salon-style",
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404


# ─── POST /api/v1/styles/{style_id}/image ────────────────────────────


class TestUploadStyleImage:
    """스타일 이미지 업로드 API 테스트."""

    @pytest.mark.anyio
    async def test_upload_front_image(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """정면 참고 이미지 업로드."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = MOCK_STYLE.copy()
            mock_db.table = MagicMock(
                return_value=MockQueryBuilder(data=[MOCK_STYLE])
            )
            # Create a fake JPEG file
            file_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
            response = await client.post(
                "/api/v1/styles/style-001/image?angle=front",
                files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["angle"] == "front"
        assert "url" in data

    @pytest.mark.anyio
    async def test_upload_side_image(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """측면 참고 이미지 업로드."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = MOCK_STYLE.copy()
            mock_db.table = MagicMock(
                return_value=MockQueryBuilder(data=[MOCK_STYLE])
            )
            file_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
            response = await client.post(
                "/api/v1/styles/style-001/image?angle=side",
                files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        assert response.json()["angle"] == "side"

    @pytest.mark.anyio
    async def test_upload_invalid_angle(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """잘못된 angle 파라미터 — 422."""
        file_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        response = await client.post(
            "/api/v1/styles/style-001/image?angle=back",
            files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_upload_non_image_file(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """이미지가 아닌 파일 업로드 시 400."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = MOCK_STYLE.copy()
            response = await client.post(
                "/api/v1/styles/style-001/image?angle=front",
                files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 400

    @pytest.mark.anyio
    async def test_upload_image_style_not_found(self, client: AsyncClient, mock_db, mock_auth_dependency):
        """존재하지 않는 스타일에 이미지 업로드 시 404."""
        with patch("app.db.queries.get_style_by_id") as mock_get:
            mock_get.return_value = None
            file_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
            response = await client.post(
                "/api/v1/styles/nonexistent/image?angle=front",
                files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 404
