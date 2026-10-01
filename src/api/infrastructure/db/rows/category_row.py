from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class CategoryRow(Base):
    """카테고리. 목록은 사용자의 것이다 — LLM이 새로 만들지 못한다(docs/ai 기능 1의 11장)."""

    __tablename__ = "categories"
    __table_args__ = (CheckConstraint("direction IN ('expense', 'income')", name="direction"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    direction: Mapped[str] = mapped_column(String(10))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"))
    # 화면의 셀렉트에 보이는 순서. 이름순이면 "기타"가 둘째 줄에 온다
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
