"""Tests for analysis API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_overview_empty(client: AsyncClient, db_session):
    """Overview with no data."""
    response = await client.get("/api/v1/analysis/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["total_companies"] == 0
    assert data["stats"]["total_works"] == 0


@pytest.mark.asyncio
async def test_overview_seeded(client: AsyncClient, seed_data):
    """Overview with seeded data."""
    response = await client.get("/api/v1/analysis/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["total_companies"] == 2
    assert data["stats"]["total_works"] == 6
    assert data["stats"]["recommended_count"] == 2
    assert data["stats"]["trash_count"] == 1


@pytest.mark.asyncio
async def test_rankings(client: AsyncClient, seed_data):
    """Rankings endpoint."""
    response = await client.get("/api/v1/analysis/rankings?tab=recommended")
    assert response.status_code == 200
    data = response.json()
    assert data["tab"] == "recommended"
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_rankings_invalid_tab(client: AsyncClient):
    """Rankings with invalid tab."""
    response = await client.get("/api/v1/analysis/rankings?tab=invalid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_trends(client: AsyncClient, seed_data):
    """Trends endpoint."""
    response = await client.get("/api/v1/analysis/trends")
    assert response.status_code == 200
    data = response.json()
    assert "by_type" in data
    assert "heatmap_data" in data


@pytest.mark.asyncio
async def test_compare(client: AsyncClient, seed_data):
    """Compare companies."""
    ids = f"{seed_data['companies'][0].id},{seed_data['companies'][1].id}"
    response = await client.get(f"/api/v1/analysis/compare?ids={ids}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["companies"]) == 2


@pytest.mark.asyncio
async def test_compare_invalid(client: AsyncClient):
    """Compare with only 1 company."""
    response = await client.get("/api/v1/analysis/compare?ids=1")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_diff(client: AsyncClient, seed_data):
    """Diff analysis between two companies."""
    a = seed_data["companies"][0].id
    b = seed_data["companies"][1].id
    response = await client.get(f"/api/v1/analysis/compare/diff?a={a}&b={b}")
    assert response.status_code == 200
    data = response.json()
    assert "cohens_d" in data
    assert "dimensions" in data


@pytest.mark.asyncio
async def test_insights(client: AsyncClient, seed_data):
    """Insights endpoint."""
    response = await client.get("/api/v1/analysis/insights")
    assert response.status_code == 200
    data = response.json()
    assert "top_companies" in data
    assert "risk_alerts" in data
    assert "track_benchmarks" in data
