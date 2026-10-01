from __future__ import annotations

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class AccountRow(Base):
    """결제수단. id는 사람이 읽는 짧은 이름이다("card") — 화면과 에이전트가 그대로 쓴다."""

    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("kind IN ('cash', 'card', 'bank')", name="kind"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    kind: Mapped[str] = mapped_column(String(10))
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
