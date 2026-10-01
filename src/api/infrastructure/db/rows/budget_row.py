from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Identity, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class BudgetRow(Base):
    """카테고리의 한 달 예산. 기간은 사용자 타임존의 달이다("2026-09")."""

    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("limit_amount > 0", name="limit_positive"),
        CheckConstraint("period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'", name="period_format"),
        UniqueConstraint("category_id", "period"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"))
    period: Mapped[str] = mapped_column(String(7))
    limit_amount: Mapped[int] = mapped_column(BigInteger)
