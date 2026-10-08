"""국가법령정보센터 Open API에서 문서 Q&A(이슈 #11)의 자료 조문을 받아 Markdown으로 둔다.

    LAW_API_OC=<기관 코드> python3 scripts/fetch_laws.py

법령 하나에 파일 하나, 조 하나에 `##` 제목 하나. 파일 머리에 출처·법령일련번호·시행일자를
적는다. 조문의 글은 고치지 않는다 — 항은 문단, 호·목은 목록 항목으로 옮길 뿐이다.
표준 라이브러리만 쓴다(scripts/의 다른 검사들과 같다).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

BASE = "https://www.law.go.kr/DRF"
OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ai" / "documents" / "laws"

# (파일 이름, 법령명, 받을 조) — 조는 "126의2"처럼 조 번호와 가지 번호
TARGETS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("tax-incentives-act.md", "조세특례제한법", ("126의2",)),
    ("tax-incentives-decree.md", "조세특례제한법 시행령", ("121의2",)),
    ("income-tax-act.md", "소득세법", ("59의4",)),
    ("credit-finance-act.md", "여신전문금융업법", ("16", "19")),
    ("installment-transactions-act.md", "할부거래에 관한 법률", ("8", "16")),
    ("electronic-financial-transactions-act.md", "전자금융거래법", ("8", "9")),
)


@dataclass(frozen=True)
class Law:
    name: str
    serial: str  # 법령일련번호(MST)
    effective: str  # 시행일자 YYYYMMDD


def main() -> int:
    oc = os.environ.get("LAW_API_OC", "")
    if not oc:
        print(
            "LAW_API_OC가 비었다 — 국가법령정보센터 Open API의 기관 코드(OC)를 넣는다",
            file=sys.stderr,
        )
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, name, articles in TARGETS:
        law = find(oc, name)
        sections = [article(oc, law, number) for number in articles]
        (OUT / filename).write_text(render(law, sections), encoding="utf-8")
        print(f"{filename}: {name} MST={law.serial} 시행 {law.effective} 조 {len(sections)}개")
    return 0


def get(path: str, params: dict[str, str]) -> dict[str, object]:
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as response:  # 고정된 https 주소다
        found = json.loads(response.read().decode("utf-8"))
    if not isinstance(found, dict):
        raise SystemExit(f"모르는 응답: {path}")
    return found


def find(oc: str, name: str) -> Law:
    """이름이 정확히 같은 현행 법령 하나. 시행령·시행규칙이 같이 걸려 나와서 이름으로 고른다."""
    query = {"OC": oc, "target": "law", "type": "JSON", "query": name, "display": "100"}
    found = get("lawSearch.do", query).get("LawSearch", {})
    laws = _list(found.get("law") if isinstance(found, dict) else None)
    for law in laws:
        if law.get("법령명한글") == name and law.get("현행연혁코드") == "현행":
            return Law(name, str(law["법령일련번호"]), str(law["시행일자"]))
    raise SystemExit(f"현행 법령을 찾지 못했다: {name}")


def article(oc: str, law: Law, number: str) -> str:
    """조 하나를 `##` 절로. JO는 조 번호 4자리 + 가지 번호 2자리(제126조의2 → 012602)."""
    main_no, _, branch = number.partition("의")
    jo = f"{int(main_no):04d}{int(branch or 0):02d}"
    params = {"OC": oc, "target": "law", "type": "JSON", "MST": law.serial, "JO": jo}
    body = get("lawService.do", params).get("법령", {})
    units = _list(body.get("조문", {}).get("조문단위") if isinstance(body, dict) else None)
    unit = next(
        (
            u
            for u in units
            if u.get("조문여부") == "조문"
            and u.get("조문번호") == main_no
            and (u.get("조문가지번호") or "") == branch
        ),
        None,
    )
    if unit is None:
        raise SystemExit(f"조문을 찾지 못했다: {law.name} 제{number}조")
    return section(unit)


def section(unit: dict[str, object]) -> str:
    heading = _text(unit.get("조문내용")).split(")")[0] + ")"
    lines = [f"## {heading}", ""]
    note = _text(unit.get("조문참고자료"))
    if note:
        lines += [note, ""]
    clauses = _list(unit.get("항"))
    if not clauses:  # 항이 없는 조 — 본문이 조문내용에 붙어 있다
        lines += [_text(unit.get("조문내용"))[len(heading) :].strip(), ""]
    for clause in clauses:
        text = _text(clause.get("항내용"))
        if text:
            lines += [text, ""]
        items = _list(clause.get("호"))
        for item in items:
            lines.append(f"- {_text(item.get('호내용'))}")
            lines += [f"  - {_text(sub.get('목내용'))}" for sub in _list(item.get("목"))]
        if items:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render(law: Law, sections: list[str]) -> str:
    effective = f"{law.effective[:4]}-{law.effective[4:6]}-{law.effective[6:]}"
    head = [
        f"# {law.name}",
        "",
        "- 출처: 국가법령정보센터 Open API (https://www.law.go.kr/DRF/lawService.do)",
        f"- 법령일련번호(MST): {law.serial}",
        f"- 시행일자: {effective}",
        "",
    ]
    return "\n".join(head) + "\n" + "\n".join(sections)


def _list(value: object) -> list[dict[str, object]]:
    """API는 하나면 객체, 여럿이면 배열로 준다. 둘 다 배열로."""
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, dict)]
    return []


def _text(value: object) -> str:
    """내용은 글 하나이거나 여러 줄의 배열이다."""
    if isinstance(value, list):
        return "\n".join(_text(v) for v in value).strip()
    return str(value).strip() if value is not None else ""


if __name__ == "__main__":
    sys.exit(main())
