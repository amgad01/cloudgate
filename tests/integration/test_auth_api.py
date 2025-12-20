import pytest
from httpx import AsyncClient


class TestAuthAPI:

    @pytest.mark.asyncio
    async def test_health_check(self, auth_client: AsyncClient) -> None:
        response = await auth_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "auth"
        assert data["status"] in ["healthy", "degraded"]

    @pytest.mark.asyncio
    async def test_register_user(self, auth_client: AsyncClient) -> None:
        response = await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "Test"
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_client: AsyncClient) -> None:
        await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        response = await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_login_success(self, auth_client: AsyncClient) -> None:
        await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "SecurePass123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_client: AsyncClient) -> None:
        response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "WrongPass123!"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, auth_client: AsyncClient) -> None:
        await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": "me@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        login_response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "me@example.com", "password": "SecurePass123!"},
        )
        token = login_response.json()["access_token"]
        response = await auth_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, auth_client: AsyncClient) -> None:
        response = await auth_client.get("/api/v1/auth/me")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_refresh_token(self, auth_client: AsyncClient) -> None:
        await auth_client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        login_response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@example.com", "password": "SecurePass123!"},
        )
        refresh_token = login_response.json()["refresh_token"]
        response = await auth_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
