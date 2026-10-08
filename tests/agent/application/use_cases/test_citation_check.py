from __future__ import annotations

import pytest

from agent.application.dto import CitationVerdict
from agent.application.use_cases.citation_check import check_citations, source_text

SOURCES = {
    "c1": source_text("할부거래에 관한 법률", "제8조 ① 1.", "계약서를 받은 날부터 7일"),
    "c2": source_text("조세특례제한법", "제126조의2 ② 2.", "대중교통이용분의 100분의 40"),
}


@pytest.mark.parametrize(
    ("answer", "citations", "verdict"),
    [
        ("계약서를 받은 날부터 7일 안에 철회해요.", ["c1"], CitationVerdict.OK),
        ("제8조에 따라 7일이에요.", ["c1"], CitationVerdict.OK),  # 자리의 숫자도 근거다
        ("버스·지하철은 40%예요.", ["c2"], CitationVerdict.OK),
        ("7일이에요.", ["c3"], CitationVerdict.UNKNOWN),
        ("7일이에요.", ["c1", "c9"], CitationVerdict.UNKNOWN),
        ("7일이에요.", [], CitationVerdict.MISSING),
        ("버스는 40%예요.", ["c1"], CitationVerdict.NUMBERS),  # 인용하지 않은 조각의 숫자
        ("14일이에요.", ["c1"], CitationVerdict.NUMBERS),
    ],
)  # fmt: skip
def test_the_table_of_five_three(answer, citations, verdict):
    assert check_citations(answer, citations, SOURCES) is verdict


def test_numbers_from_elsewhere_can_be_allowed():
    answer = "이번 달 교통비는 52,000원이고 40%를 공제해요."
    assert check_citations(answer, ["c2"], SOURCES) is CitationVerdict.NUMBERS
    assert check_citations(answer, ["c2"], SOURCES, {"52000"}) is CitationVerdict.OK
