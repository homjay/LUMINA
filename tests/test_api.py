"""API tests for License Server."""
import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from app.models.schemas import LicenseCreate


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.asyncio
async def test_ping():
    """Test ping endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/ping")
        assert response.status_code == 200
        data = response.json()
        assert data["ping"] == "pong"


@pytest.mark.asyncio
async def test_verify_license_invalid():
    """Test license verification with invalid key."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/license/verify",
            json={
                "license_key": "INVALID-KEY-123",
                "machine_code": "TEST-MACHINE-001",
                "ip": "192.168.1.1"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False


@pytest.mark.asyncio
async def test_admin_login():
    """Test admin login."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_admin_login_invalid():
    """Test admin login with invalid credentials."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/login",
            json={
                "username": "admin",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_license():
    """Test creating a license."""
    # First login to get token
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login_response = await client.post(
            "/api/v1/admin/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        token = login_response.json()["access_token"]

        # Create license
        response = await client.post(
            "/api/v1/admin/license",
            json={
                "product": "TestApp",
                "version": "1.0.0",
                "customer": "Test Customer",
                "email": "test@example.com",
                "max_activations": 1,
                "machine_binding": True,
                "status": "active"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "key" in data
        assert data["product"] == "TestApp"
        assert data["customer"] == "Test Customer"


@pytest.mark.asyncio
async def test_create_license_unauthorized():
    """Test creating a license without authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/license",
            json={
                "product": "TestApp",
                "customer": "Test Customer"
            }
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"
