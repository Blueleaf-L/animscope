from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, HTMLResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.database import get_db
from app.services.chart_service import ChartService

router = APIRouter(prefix="/api/v1/charts", tags=["charts"])

# Cache headers for chart responses
CACHE_HEADERS = {"Cache-Control": "public, max-age=3600"}


@router.get("/rating-distribution")
async def rating_distribution(
    theme: str = Query("light", description="Theme: light or dark"),
    db: AsyncSession = Depends(get_db),
):
    """Rating distribution bar chart (PNG)."""
    data, media_type = await ChartService.chart_rating_distribution(db, theme)
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/company-radar")
async def company_radar(
    id: int = Query(..., description="Company ID"),
    theme: str = Query("light", description="Theme: light or dark"),
    db: AsyncSession = Depends(get_db),
):
    """Company radar chart (SVG)."""
    data, media_type = await ChartService.chart_company_radar(db, id, theme)
    if not data:
        raise HTTPException(status_code=404, detail="Company not found or no data")
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/heatmap")
async def heatmap(
    top_n: int = Query(20, ge=5, le=50, description="Number of top companies"),
    theme: str = Query("light", description="Theme: light or dark"),
    db: AsyncSession = Depends(get_db),
):
    """Company × Year heatmap (PNG)."""
    data, media_type = await ChartService.chart_heatmap(db, top_n, theme)
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/boxplot")
async def boxplot(
    type: Optional[str] = Query(None, description="Filter by company type: 2D, 3D, 三渲二"),
    theme: str = Query("light", description="Theme: light or dark"),
    db: AsyncSession = Depends(get_db),
):
    """Box plot of rating distributions (PNG)."""
    data, media_type = await ChartService.chart_boxplot(db, type, theme)
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/compare-radar")
async def compare_radar(
    ids: str = Query(..., description="Comma-separated company IDs"),
    theme: str = Query("light", description="Theme: light or dark"),
    db: AsyncSession = Depends(get_db),
):
    """Multi-company comparison radar chart (SVG)."""
    id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    if len(id_list) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 company IDs")
    data, media_type = await ChartService.chart_compare_radar(db, id_list, theme)
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/industry-dashboard")
async def industry_dashboard(
    db: AsyncSession = Depends(get_db),
):
    """Interactive Plotly dashboard (HTML snippet)."""
    html = await ChartService.chart_dashboard_html(db)
    return HTMLResponse(content=html, headers=CACHE_HEADERS)


@router.get("/report")
async def report(
    format: str = Query("pdf", description="Output format: pdf"),
    db: AsyncSession = Depends(get_db),
):
    """Download multi-page PDF report."""
    if format != "pdf":
        raise HTTPException(status_code=400, detail="Only PDF format is supported")

    data, media_type = await ChartService.chart_report_pdf(db)
    if not data:
        raise HTTPException(status_code=404, detail="No data available for report")

    return Response(
        content=data,
        media_type=media_type,
        headers={
            "Content-Disposition": "attachment; filename=animation_analysis_report.pdf",
            **CACHE_HEADERS,
        },
    )
