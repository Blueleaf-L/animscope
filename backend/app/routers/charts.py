from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/api/v1/charts", tags=["charts"])

CACHE_HEADERS = {"Cache-Control": "public, max-age=3600"}

# Lazy import — chart libs may not be installed on deployment
_chart_service = None

def _get_chart_service():
    global _chart_service
    if _chart_service is None:
        try:
            from app.services.chart_service import ChartService
            _chart_service = ChartService
        except ImportError as e:
            raise HTTPException(
                status_code=501,
                detail="Chart generation not available on this server (missing: " + str(e) + "). Use local deployment for full chart support."
            )
    return _chart_service


@router.get("/rating-distribution")
async def rating_distribution(theme: str = Query("light"), db: AsyncSession = Depends(get_db)):
    svc = _get_chart_service()
    data, media_type = await svc.chart_rating_distribution(db, theme)
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/company-radar")
async def company_radar(id: int = Query(...), theme: str = Query("light"), db: AsyncSession = Depends(get_db)):
    svc = _get_chart_service()
    data, media_type = await svc.chart_company_radar(db, id, theme)
    if not data:
        raise HTTPException(status_code=404, detail="Company not found or no data")
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/heatmap")
async def heatmap(top_n: int = Query(20, ge=5, le=50), theme: str = Query("light"), db: AsyncSession = Depends(get_db)):
    svc = _get_chart_service()
    data, media_type = await svc.chart_heatmap(db, top_n, theme)
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/boxplot")
async def boxplot(type: Optional[str] = Query(None), theme: str = Query("light"), db: AsyncSession = Depends(get_db)):
    svc = _get_chart_service()
    data, media_type = await svc.chart_boxplot(db, type, theme)
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/compare-radar")
async def compare_radar(ids: str = Query(...), theme: str = Query("light"), db: AsyncSession = Depends(get_db)):
    svc = _get_chart_service()
    id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    if len(id_list) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 company IDs")
    data, media_type = await svc.chart_compare_radar(db, id_list, theme)
    return Response(content=data, media_type=media_type, headers=CACHE_HEADERS)


@router.get("/industry-dashboard")
async def industry_dashboard(db: AsyncSession = Depends(get_db)):
    svc = _get_chart_service()
    html = await svc.chart_dashboard_html(db)
    return HTMLResponse(content=html, headers=CACHE_HEADERS)


@router.get("/report")
async def report(format: str = Query("pdf"), db: AsyncSession = Depends(get_db)):
    if format != "pdf":
        raise HTTPException(status_code=400, detail="Only PDF format is supported")
    svc = _get_chart_service()
    data, media_type = await svc.chart_report_pdf(db)
    if not data:
        raise HTTPException(status_code=404, detail="No data available for report")
    return Response(
        content=data, media_type=media_type,
        headers={"Content-Disposition": "attachment; filename=animation_analysis_report.pdf", **CACHE_HEADERS},
    )
