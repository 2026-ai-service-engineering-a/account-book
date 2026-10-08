from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class DocumentRow(Base):
    """문서 하나 — 지금은 법령 하나(docs/ai/document-rag.md 3장). 본문은 받은 그대로다."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)  # 법령명
    title: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(300))
    mst: Mapped[str] = mapped_column(String(20))  # 법령일련번호
    effective_date: Mapped[date] = mapped_column(Date)  # 시행일자
    body: Mapped[str] = mapped_column(Text)
