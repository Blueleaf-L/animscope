import math
from typing import Optional

from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.company import Company
from app.models.work import Work


class CompanyService:
    """Service layer for company-related database queries."""

    @staticmethod
    async def get_companies(
        db: AsyncSession,
        *,
        type_filter: Optional[str] = None,
        sort: str = "name",
        order: str = "asc",
        search: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[dict], int]:
        """Get paginated company list with works_count and avg_score subquery."""
        # Subquery for works_count and avg_score
        works_sub = (
            select(
                Work.company_id,
                func.count(Work.id).label("works_count"),
                func.avg(Work.rating_score).label("avg_score"),
            )
            .group_by(Work.company_id)
            .subquery()
        )

        query = (
            select(
                Company,
                func.coalesce(works_sub.c.works_count, 0).label("works_count"),
                func.coalesce(works_sub.c.avg_score, 0).label("avg_score"),
            )
            .outerjoin(works_sub, Company.id == works_sub.c.company_id)
        )

        # Filters
        if type_filter:
            query = query.where(Company.type == type_filter)
        if search:
            query = query.where(Company.name.ilike(f"%{search}%"))

        # Sort
        sort_map = {
            "name": Company.name,
            "type": Company.type,
            "works_count": func.coalesce(works_sub.c.works_count, 0),
            "avg_score": func.coalesce(works_sub.c.avg_score, 0),
            "id": Company.id,
        }
        sort_col = sort_map.get(sort, Company.name)

        if order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        # Count total
        count_query = select(func.count()).select_from(Company)
        if type_filter:
            count_query = count_query.where(Company.type == type_filter)
        if search:
            count_query = count_query.where(Company.name.ilike(f"%{search}%"))
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await db.execute(query)
        rows = result.all()

        items = []
        for row in rows:
            company = row[0]
            items.append({
                "id": company.id,
                "name": company.name,
                "type": company.type,
                "works_count": row.works_count,
                "avg_score": float(row.avg_score) if row.avg_score else None,
                "created_at": company.created_at.isoformat(),
                "updated_at": company.updated_at.isoformat(),
            })

        return items, total

    @staticmethod
    async def get_company_detail(db: AsyncSession, company_id: int) -> Optional[dict]:
        """Get company detail with all works."""
        query = (
            select(Company)
            .options(selectinload(Company.works))
            .where(Company.id == company_id)
        )
        result = await db.execute(query)
        company = result.scalar_one_or_none()

        if not company:
            return None

        works = []
        for w in company.works:
            works.append({
                "id": w.id,
                "company_id": w.company_id,
                "name": w.name,
                "year": w.year,
                "rating_raw": w.rating_raw,
                "rating_label": w.rating_label,
                "rating_score": float(w.rating_score) if w.rating_score else None,
                "quantity": w.quantity,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat(),
            })

        return {
            "id": company.id,
            "name": company.name,
            "type": company.type,
            "works": works,
            "works_count": len(works),
            "avg_score": (
                sum(w.rating_score for w in company.works if w.rating_score) / max(len([w for w in company.works if w.rating_score]), 1)
                if company.works else None
            ),
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat(),
        }

    @staticmethod
    async def get_company_works(
        db: AsyncSession,
        company_id: int,
        *,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        rating: Optional[str] = None,
        sort: str = "year",
        order: str = "desc",
    ) -> list[dict]:
        """Get filtered works for a specific company."""
        query = select(Work).where(Work.company_id == company_id)

        if year_min:
            query = query.where(Work.year >= year_min)
        if year_max:
            query = query.where(Work.year <= year_max)
        if rating:
            labels = [r.strip() for r in rating.split(",")]
            query = query.where(Work.rating_label.in_(labels))

        # Sort
        sort_map = {
            "year": Work.year,
            "rating_score": Work.rating_score,
            "name": Work.name,
        }
        sort_col = sort_map.get(sort, Work.year)
        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc().nullslast())

        result = await db.execute(query)
        works = result.scalars().all()

        # Fetch company name
        company_result = await db.execute(select(Company.name).where(Company.id == company_id))
        company_name = company_result.scalar_one_or_none() or ""

        return [
            {
                "id": w.id,
                "company_id": w.company_id,
                "company_name": company_name,
                "name": w.name,
                "year": w.year,
                "rating_raw": w.rating_raw,
                "rating_label": w.rating_label,
                "rating_score": float(w.rating_score) if w.rating_score else None,
                "quantity": w.quantity,
                "created_at": w.created_at.isoformat(),
                "updated_at": w.updated_at.isoformat(),
            }
            for w in works
        ]
