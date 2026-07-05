from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.work import WorkOut


class CompanyOut(BaseModel):
    id: int
    name: str
    type: str
    works_count: int = 0
    avg_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyDetail(CompanyOut):
    works: list[WorkOut] = []


class CompanyListResponse(BaseModel):
    items: list[CompanyOut]
    total: int
    page: int
    size: int
    pages: int
