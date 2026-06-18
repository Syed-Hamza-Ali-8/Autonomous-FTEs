import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_all_candidates_empty(client):
    response = await client.get("/api/candidates/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_candidate_not_found(client):
    response = await client.get("/api/candidates/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_candidates_by_status(client):
    response = await client.get("/api/candidates/by-status/queued")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
