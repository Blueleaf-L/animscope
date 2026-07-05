"""Tests for chart service — verify no exceptions."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rating_distribution_chart(client: AsyncClient, seed_data):
    """Rating distribution chart returns PNG."""
    response = await client.get("/api/v1/charts/rating-distribution")
    assert response.status_code == 200
    assert response.headers["content-type"] in ("image/png", "image/svg+xml")


@pytest.mark.asyncio
async def test_boxplot_chart(client: AsyncClient, seed_data):
    """Boxplot chart returns PNG."""
    response = await client.get("/api/v1/charts/boxplot")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_industry_dashboard(client: AsyncClient, seed_data):
    """Industry dashboard returns HTML."""
    response = await client.get("/api/v1/charts/industry-dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_report_pdf(client: AsyncClient, seed_data):
    """Report PDF returns PDF."""
    response = await client.get("/api/v1/charts/report?format=pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Health check endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
