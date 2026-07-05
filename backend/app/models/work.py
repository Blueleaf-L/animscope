from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Work(Base):
    __tablename__ = "works"
    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_works_company_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_raw: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating_score: Mapped[float | None] = mapped_column(
        Numeric(4, 2), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    company = relationship("Company", back_populates="works")

    def __repr__(self) -> str:
        return f"<Work(id={self.id}, name='{self.name}', year={self.year})>"
