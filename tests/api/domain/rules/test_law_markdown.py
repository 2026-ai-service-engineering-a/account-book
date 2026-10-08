from __future__ import annotations

from datetime import date

import pytest

from api.domain.rules.law_markdown import parse_law

LAW = """# 할부거래에 관한 법률

- 출처: 국가법령정보센터 Open API (https://www.law.go.kr/DRF/lawService.do)
- 법령일련번호(MST): 289407
- 시행일자: 2026-09-08

## 제8조(청약의 철회)

① 소비자는 청약을 철회할 수 있다.
"""


def test_reads_the_head_and_keeps_the_articles_as_written():
    law = parse_law(LAW)
    assert (law.id, law.mst, law.effective_date) == (
        "할부거래에 관한 법률",
        "289407",
        date(2026, 9, 8),
    )
    assert law.source.startswith("국가법령정보센터")
    assert law.body == "## 제8조(청약의 철회)\n\n① 소비자는 청약을 철회할 수 있다.\n"


@pytest.mark.parametrize(
    "broken", [LAW.replace("# 할부", "할부"), LAW.replace("- 시행일자: 2026-09-08\n", "")]
)
def test_a_law_without_its_head_is_refused(broken):
    with pytest.raises(ValueError):
        parse_law(broken)
