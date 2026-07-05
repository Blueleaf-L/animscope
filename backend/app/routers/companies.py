from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.company_service import CompanyService

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


@router.get("")
async def list_companies(
    type: Optional[str] = Query(None, description="Filter by company type (2D, 3D, 三渲二)"),
    sort: str = Query("name", description="Sort field: name, type, works_count, avg_score"),
    order: str = Query("asc", description="Sort order: asc or desc"),
    q: Optional[str] = Query(None, description="Search by company name"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated company list with works_count and avg_score."""
    items, total = await CompanyService.get_companies(
        db,
        type_filter=type,
        sort=sort,
        order=order,
        search=q,
        page=page,
        size=size,
    )
    pages = max((total + size - 1) // size, 1)
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


@router.get("/{company_id}")
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get company detail with works list."""
    detail = await CompanyService.get_company_detail(db, company_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Company not found")
    return detail


@router.get("/{company_id}/works")
async def get_company_works(
    company_id: int,
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    rating: Optional[str] = Query(None, description="Comma-separated rating labels"),
    sort: str = Query("year", description="Sort field: year, rating_score, name"),
    order: str = Query("desc", description="Sort order"),
    db: AsyncSession = Depends(get_db),
):
    """Get filtered works for a specific company."""
    # Verify company exists
    detail = await CompanyService.get_company_detail(db, company_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Company not found")

    works = await CompanyService.get_company_works(
        db, company_id,
        year_min=year_min, year_max=year_max,
        rating=rating, sort=sort, order=order,
    )
    return {"items": works, "total": len(works)}
