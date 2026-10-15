from __future__ import annotations

from pydantic import AwareDatetime, BaseModel

from api.application.dto import Outliers

from .outlier_body import OutlierBody
from .skipped_category_body import SkippedCategoryBody


class OutliersBody(BaseModel):
    """`GET /v1/stats/outliers`의 답. 평소를 잰 기간 `[baseline_from, baseline_to)`, 넘은 정도가
    큰 순서의 거래(최대 5건), 넘쳤는지, 판정하지 않은 카테고리와 그 이유."""

    baseline_from: AwareDatetime
    baseline_to: AwareDatetime
    items: list[OutlierBody]
    truncated: bool
    skipped: list[SkippedCategoryBody]

    @classmethod
    def of(cls, found: Outliers) -> OutliersBody:
        return cls(
            baseline_from=found.baseline.start,
            baseline_to=found.baseline.end,
            items=[OutlierBody.of(item) for item in found.items],
            truncated=found.truncated,
            skipped=[SkippedCategoryBody.of(s) for s in found.skipped],
        )
