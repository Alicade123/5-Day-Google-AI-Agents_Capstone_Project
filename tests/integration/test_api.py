import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    from backend.config.settings import get_settings

    get_settings.cache_clear()
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(client):
    response = await client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "system" in data
    assert data["tool_count"] > 0
    assert "collected_at" in data


@pytest.mark.asyncio
async def test_logs_endpoint(client):
    response = await client.get("/logs")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "failures" in data


@pytest.mark.asyncio
async def test_analyze_endpoint(client):
    response = await client.post("/analyze")
    assert response.status_code == 200
    data = response.json()
    assert "snapshot" in data
    assert "agent_response" in data
    assert "facts" in data["agent_response"]


@pytest.mark.asyncio
async def test_agent_query_endpoint(client):
    response = await client.post(
        "/agent/query",
        json={"query": "Why is server performance degrading?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "facts" in data
    assert "possible_explanations" in data
    assert "confidence" in data
    assert "recommended_actions" in data


@pytest.mark.asyncio
async def test_incidents_endpoint_after_analyze(client):
    await client.post("/analyze")
    response = await client.get("/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_request_id_header(client):
    response = await client.get("/health", headers={"X-Request-ID": "test-123"})
    assert response.headers.get("X-Request-ID") == "test-123"
