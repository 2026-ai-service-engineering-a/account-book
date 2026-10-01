from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class TransactionRow(Base):
    """거래 한 건. 금액은 정수 원이고, 시각은 전부 UTC로 저장한다(development-rules 6.1).

    `occurred_at`은 사용자가 말한 시점, `created_at`은 기록된 시각이다. 섞지 않는다.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("direction IN ('expense', 'income')", name="direction"),
        CheckConstraint("source IN ('manual', 'agent', 'import')", name="source"),
        # 기간 조회와 카테고리별 집계가 가장 잦다
        Index(None, "occurred_at"),
        Index(None, "category_id", "occurred_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount: Mapped[int] = mapped_column(BigInteger)
    direction: Mapped[str] = mapped_column(String(10))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"))
    merchant: Mapped[str] = mapped_column(String(100), default="", server_default="")
    memo: Mapped[str] = mapped_column(String(200), default="", server_default="")
    # 출처. 에이전트가 만든 기록은 언제나 구분된다(README 6장)
    source: Mapped[str] = mapped_column(String(10))
    run_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
