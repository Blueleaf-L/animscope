from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.company import Company
from app.models.work import Work

router = APIRouter(prefix="/api/v1/works", tags=["works"])


@router.get("")
async def list_works(
    q: Optional[str] = Query(None, description="Search by work name"),
    year: Optional[int] = Query(None, description="Filter by year"),
    rating: Optional[str] = Query(None, description="Filter by rating label"),
    type: Optional[str] = Query(None, description="Filter by company type"),
    sort: str = Query("year", description="Sort field: year, rating_score, name"),
    order: str = Query("desc", description="Sort order"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Search and list all works."""
    query = select(Work, Company.name.label("company_name")).join(
        Company, Work.company_id == Company.id
    )

    if q:
        query = query.where(Work.name.ilike(f"%{q}%"))
    if year:
        query = query.where(Work.year == year)
    if rating:
        query = query.where(Work.rating_label == rating)
    if type:
        query = query.where(Company.type == type)

    # Sort
    sort_map = {
        "year": Work.year,
        "rating_score": Work.rating_score,
        "name": Work.name,
    }
    sort_col = sort_map.get(sort, Work.year)
    if order == "asc":
        query = query.order_by(sort_col.asc().nullslast())
    else:
        query = query.order_by(sort_col.desc().nullslast())

    # Count
    count_query = select(func.count()).select_from(Work).join(Company, Work.company_id == Company.id)
    if q:
        count_query = count_query.where(Work.name.ilike(f"%{q}%"))
    if year:
        count_query = count_query.where(Work.year == year)
    if rating:
        count_query = count_query.where(Work.rating_label == rating)
    if type:
        count_query = count_query.where(Company.type == type)
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for work, comp_name in rows:
        items.append({
            "id": work.id,
            "company_id": work.company_id,
            "company_name": comp_name,
            "name": work.name,
            "year": work.year,
            "rating_raw": work.rating_raw,
            "rating_label": work.rating_label,
            "rating_score": float(work.rating_score) if work.rating_score else None,
            "quantity": work.quantity,
            "created_at": work.created_at.isoformat(),
            "updated_at": work.updated_at.isoformat(),
        })

    pages = max((total + size - 1) // size, 1)
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


@router.get("/{work_id}")
async def get_work(
    work_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get single work detail."""
    query = select(Work, Company.name.label("company_name")).join(
        Company, Work.company_id == Company.id
    ).where(Work.id == work_id)
    result = await db.execute(query)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Work not found")

    work, comp_name = row
    return {
        "id": work.id,
        "company_id": work.company_id,
        "company_name": comp_name,
        "name": work.name,
        "year": work.year,
        "rating_raw": work.rating_raw,
        "rating_label": work.rating_label,
        "rating_score": float(work.rating_score) if work.rating_score else None,
        "quantity": work.quantity,
        "created_at": work.created_at.isoformat(),
        "updated_at": work.updated_at.isoformat(),
    }
