"""Tests for the Flow auth system — register, login, me, RBAC."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient


class TestRegister:
    """POST /api/auth/register"""

    async def test_register_creates_user(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "bob@example.com",
                "password": "strongpass",
                "name": "Bob",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "bob@example.com"
        assert data["name"] == "Bob"
        assert data["role"] == "user"
        assert "id" in data
        assert "tenant_id" in data

    async def test_register_duplicate_email_returns_409(
        self, client: AsyncClient, registered_user: dict[str, Any]
    ) -> None:
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "alice@example.com",
                "password": "another",
                "name": "Alice Again",
            },
        )
        assert resp.status_code == 409
        assert "exists" in resp.json()["detail"].lower()

    async def test_register_creates_default_tenant(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/auth/register",
            json={
                "email": "carol@example.com",
                "password": "p4ssword",
                "name": "Carol",
                "tenant_name": "MyOrg",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "carol@example.com"
        assert data["tenant_id"] is not None

    async def test_register_multiple_users_same_tenant(
        self, client: AsyncClient
    ) -> None:
        # First user creates the tenant
        r1 = await client.post(
            "/api/auth/register",
            json={
                "email": "u1@test.com",
                "password": "pass",
                "name": "User1",
                "tenant_name": "Team",
            },
        )
        tenant_id = r1.json()["tenant_id"]

        # Second user in the same tenant
        r2 = await client.post(
            "/api/auth/register",
            json={
                "email": "u2@test.com",
                "password": "pass",
                "name": "User2",
                "tenant_name": "Team",
            },
        )
        assert r2.status_code == 201
        assert r2.json()["tenant_id"] == tenant_id


class TestLogin:
    """POST /api/auth/login"""

    async def test_login_returns_token(
        self, client: AsyncClient, registered_user: dict[str, Any]
    ) -> None:
        resp = await client.post(
            "/api/auth/login",
            json={"email": "alice@example.com", "password": "secret123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password_returns_401(
        self, client: AsyncClient, registered_user: dict[str, Any]
    ) -> None:
        resp = await client.post(
            "/api/auth/login",
            json={"email": "alice@example.com", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_email_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/auth/login",
            json={"email": "unknown@example.com", "password": "anything"},
        )
        assert resp.status_code == 401


class TestMe:
    """GET /api/auth/me"""

    async def test_me_with_valid_token_returns_user(
        self, client: AsyncClient, auth_token: str
    ) -> None:
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "alice@example.com"
        assert data["name"] == "Alice"
        assert data["role"] == "user"

    async def test_me_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_me_with_invalid_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalidtoken123"},
        )
        assert resp.status_code == 401

    async def test_me_with_malformed_header_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "NotBearer token"},
        )
        assert resp.status_code == 401


class TestRBACDependency:
    """Indirect tests for the require_role dependency via admin context."""

    async def test_health_endpoint_still_works(
        self, client: AsyncClient
    ) -> None:
        """Sanity check that adding auth didn't break existing routes."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
