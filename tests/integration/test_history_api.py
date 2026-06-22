import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setenv("API_KEY", "test-secret-key")
    from backend.config.settings import get_settings

    get_settings.cache_clear()
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    headers = {"X-API-Key": "test-secret-key"}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as ac:
        yield ac


@pytest.mark.asyncio
async def test_api_key_required_without_header(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/metrics")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_public_without_api_key(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_history_endpoint(client):
    await client.get("/metrics")
    response = await client.get("/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "records" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_trends_endpoint(client):
    for _ in range(3):
        await client.get("/metrics")
    response = await client.get("/history/trends?window_minutes=60")
    assert response.status_code == 200
    data = response.json()
    assert "summaries" in data
    assert "moving_averages" in data


@pytest.mark.asyncio
async def test_correlation_endpoint(client):
    await client.post("/analyze")
    response = await client.get("/correlation?window_hours=1")
    assert response.status_code == 200
    assert "patterns" in response.json()
