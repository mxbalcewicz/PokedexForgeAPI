import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import UserCreate


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient, db_session: AsyncSession):
        user_data = UserCreate(email="test@example.com", password="password123")
        response = await client.post("/auth/register", json=user_data.model_dump())
        data = response.json()

        assert response.status_code == 201
        assert data["id"] == 1
        assert data["email"] == user_data.email

    @pytest.mark.asyncio
    async def test_login_user(self, client: AsyncClient, db_session: AsyncSession):
        user_data = UserCreate(email="login@example.com", password="password123")
        await client.post("/auth/register", json=user_data.model_dump())

        login_data = {"username": user_data.email, "password": user_data.password}
        response = await client.post("/auth/login", data=login_data)
        data = response.json()

        assert response.status_code == 200
        for _key in ("access_token", "refresh_token"):
            assert _key in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token(self, client: AsyncClient, db_session: AsyncSession):
        user_data = UserCreate(email="refresh@example.com", password="password123")
        await client.post("/auth/register", json=user_data.model_dump())
        login_data = {"username": user_data.email, "password": user_data.password}
        login_response = await client.post("/auth/login", data=login_data)
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        for _key in ("access_token", "refresh_token"):
            assert _key in data
        assert data["token_type"] == "bearer"
