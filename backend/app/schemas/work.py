from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WorkOut(BaseModel):
    id: int
    company_id: int
    company_name: str = ""
    name: str
    year: Optional[int] = None
    rating_raw: Optional[str] = None
    rating_label: Optional[str] = None
    rating_score: Optional[float] = None
    quantity: int = 1
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkDetail(WorkOut):
    pass


class WorkListResponse(BaseModel):
    items: list[WorkOut]
    total: int
    page: int
    size: int
    pages: int
