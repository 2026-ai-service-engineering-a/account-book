from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class CategoryRuleRow(Base):
    """카테고리 고르기 0단계의 규칙 표 — 색인 텍스트에 이 패턴이 들면 이 카테고리.

    규칙은 사용자의 것이다. 자동으로 늘지 않고 사용자가 승격한다(category-suggestion-rag 8.2).
    """

    __tablename__ = "category_rules"
    __table_args__ = (CheckConstraint("source IN ('seed', 'user')", name="source"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    merchant_pattern: Mapped[str] = mapped_column(String(100), unique=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"))
    source: Mapped[str] = mapped_column(String(10))
    hit_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
