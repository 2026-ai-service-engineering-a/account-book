from __future__ import annotations

from pydantic import BaseModel

from api.application.dto import Outlier

from .transaction_body import TransactionBody


class OutlierBody(BaseModel):
    """평소 범위를 넘은 거래 한 건과 그 카테고리의 평소(정수 원). 넘은 기준을 같이 낸다 —
    문장이 "평소 9,000원인데 45,000원"이라고 말할 근거다."""

    transaction: TransactionBody
    usual_median: int
    usual_upper: int  # 이 금액을 넘었다

    @classmethod
    def of(cls, found: Outlier) -> OutlierBody:
        return cls(
            transaction=TransactionBody.of(found.transaction),
            usual_median=found.usual_median.amount,
            usual_upper=found.usual_upper.amount,
        )
