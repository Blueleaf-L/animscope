from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
):
    """Homepage overview: counts, trends, distributions, diagnostics."""
    return await AnalysisService.calc_overview(db)


@router.get("/rankings")
async def get_rankings(
    tab: str = Query("recommended", description="Ranking tab: recommended, good, trash"),
    db: AsyncSession = Depends(get_db),
):
    """Get company rankings by different criteria."""
    if tab not in ("recommended", "good", "trash"):
        raise HTTPException(status_code=400, detail="Invalid tab. Use: recommended, good, trash")
    return await AnalysisService.calc_rankings(db, tab)


@router.get("/trends")
async def get_trends(
    db: AsyncSession = Depends(get_db),
):
    """Yearly trends by type + heatmap matrix data."""
    return await AnalysisService.calc_trends(db)


@router.get("/compare")
async def compare_companies(
    ids: str = Query(..., description="Comma-separated company IDs (2-4)"),
    db: AsyncSession = Depends(get_db),
):
    """Multi-company comparison metrics."""
    id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    if len(id_list) < 2 or len(id_list) > 4:
        raise HTTPException(status_code=400, detail="Please provide 2-4 company IDs")
    return await AnalysisService.calc_compare(db, id_list)


@router.get("/compare/diff")
async def compare_diff(
    a: int = Query(..., description="Company A ID"),
    b: int = Query(..., description="Company B ID"),
    db: AsyncSession = Depends(get_db),
):
    """Cohen's d + dimension head-to-head + volatility for exactly 2 companies."""
    result = await AnalysisService.calc_diff(db, a, b)
    if not result:
        raise HTTPException(status_code=400, detail="Insufficient data for comparison")
    return result


@router.get("/insights")
async def get_insights(
    db: AsyncSession = Depends(get_db),
):
    """Z-Score ranking + risk alerts + track benchmarks."""
    return await AnalysisService.calc_insights(db)
