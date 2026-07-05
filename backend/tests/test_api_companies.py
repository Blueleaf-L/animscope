"""Tests for companies API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_companies_empty(client: AsyncClient, db_session):
    """List companies — empty database."""
    response = await client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_companies_seeded(client: AsyncClient, seed_data):
    """List companies — with seeded data."""
    response = await client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_companies_filter_by_type(client: AsyncClient, seed_data):
    """Filter companies by type."""
    response = await client.get("/api/v1/companies?type=3D")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "测试动画公司"


@pytest.mark.asyncio
async def test_list_companies_search(client: AsyncClient, seed_data):
    """Search companies by name."""
    response = await client.get("/api/v1/companies?q=另一个")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "另一个动画公司"


@pytest.mark.asyncio
async def test_get_company_detail(client: AsyncClient, seed_data):
    """Get company detail with works."""
    company_id = seed_data["companies"][0].id
    response = await client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试动画公司"
    assert data["works_count"] == 4
    assert len(data["works"]) == 4


@pytest.mark.asyncio
async def test_get_company_not_found(client: AsyncClient):
    """Get non-existent company."""
    response = await client.get("/api/v1/companies/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_company_works_filtered(client: AsyncClient, seed_data):
    """Get company works with year filter."""
    company_id = seed_data["companies"][0].id
    response = await client.get(f"/api/v1/companies/{company_id}/works?year_min=2023&year_max=2023")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2  # 测试作品A and 测试作品D
