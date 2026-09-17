#!/usr/bin/env python3
"""문서끼리 어긋난 곳을 찾는다.

문서가 서로를 참조하기 시작하면(장 번호, 앵커, 도구 이름, 에러 코드) 사람 눈으로는
맞출 수 없다. 기계가 대조할 수 있는 것만 여기서 본다. 사람과 에이전트는 문서를 다시
읽지 않고 이 결과만 보면 된다.

  python3 scripts/check_docs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DOC_DIRS = ("docs", "ui_docs", "mock_ui")
DOCS = [
    Path("README.md"),
    *sorted(p for d in DOC_DIRS for p in Path(d).rglob("*.md") if Path(d).is_dir()),
]
RULES = Path("docs/development-rules.md")
CONTRACT = Path("docs/api-contract.md")
README = Path("README.md")

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
STATUS_CODE = re.compile(r"\b[45]\d\d\s+([a-z][a-z0-9_]+)\b")
BACKTICKED = re.compile(r"`([^`]+)`")


def anchor(heading_text: str) -> str:
    """GitHub이 제목에서 앵커를 만드는 방식."""
    text = heading_text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def anchors_of(text: str) -> set[str]:
    return {anchor(m.group(2)) for m in HEADING.finditer(text)}


def section(text: str, heading_prefix: str) -> str:
    """`## 4. 도구` 처럼 시작하는 장 하나를 잘라낸다."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(heading_prefix)), None)
    if start is None:
        return ""
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    for i in range(start + 1, len(lines)):
        stripped = lines[i].lstrip("#")
        if lines[i].startswith("#") and len(lines[i]) - len(stripped) <= level:
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:])


def table_column(block: str, index: int) -> list[str]:
    """표에서 한 열을 뽑는다. 구분선과 머리글은 건너뛴다."""
    out: list[str] = []
    for line in block.splitlines():
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if index < len(cells):
            out.append(cells[index])
    return out[1:]  # 머리글 제거


def check_links() -> list[str]:
    """문서 간 링크가 가리키는 파일과 앵커가 실제로 있는지."""
    problems: list[str] = []
    cache: dict[Path, set[str]] = {}
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, _, frag = target.partition("#")
            dest = (doc.parent / path_part).resolve() if path_part else doc.resolve()
            if not dest.exists():
                problems.append(f"{doc}: 링크가 가리키는 파일이 없다 — {target}")
                continue
            if not frag:
                continue
            rel = dest.relative_to(Path.cwd())
            if rel not in cache:
                cache[rel] = anchors_of(dest.read_text(encoding="utf-8"))
            if frag not in cache[rel]:
                problems.append(f"{doc}: 앵커가 없다 — {target}")
    return problems


def check_tool_names() -> list[str]:
    """README의 도구 목록과 api 계약의 엔드포인트 표가 같은 도구를 말하는지."""
    readme = README.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    declared = {
        m.group(1)
        for cell in table_column(section(readme, "## 4. 도구"), 0)
        if (m := BACKTICKED.search(cell))
    }
    mapped = {
        m.group(1)
        for cell in table_column(section(contract, "## 6. 엔드포인트"), 2)
        if (m := BACKTICKED.search(cell))
    }
    problems: list[str] = []
    for name in sorted(declared - mapped):
        problems.append(f"{CONTRACT}: README에 있는 도구 `{name}`에 대응하는 엔드포인트가 없다")
    for name in sorted(mapped - declared):
        problems.append(f"{README}: 계약에 있는 도구 `{name}`가 README 4장 표에 없다")
    return problems


def check_error_codes() -> list[str]:
    """문서에 쓰인 `4xx code`가 정의된 코드 목록 안에 있는지."""
    rules = RULES.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    known = {
        m.group(1)
        for cell in table_column(section(rules, "### 6.5 예외"), 2)
        if (m := BACKTICKED.search(cell))
    }
    known |= {
        m.group(1)
        for cell in table_column(section(contract, "### 5.1 프로토콜 코드"), 1)
        if (m := BACKTICKED.search(cell))
    }
    problems: list[str] = []
    for doc in DOCS:
        for match in STATUS_CODE.finditer(doc.read_text(encoding="utf-8")):
            code = match.group(1)
            if code not in known:
                problems.append(f"{doc}: 정의되지 않은 에러 코드 — {code}")
    return sorted(set(problems))


def check_rule_refs() -> list[str]:
    """`6.1`, `10장` 같은 규칙 참조가 실제 있는 절인지."""
    rules = RULES.read_text(encoding="utf-8")
    chapters = {
        m.group(2).split(".")[0].split(" ")[0]
        for m in HEADING.finditer(rules)
        if re.match(r"\d", m.group(2))
    }
    sections = {
        m.group(2).split(" ")[0]
        for m in HEADING.finditer(rules)
        if re.match(r"\d+\.\d", m.group(2))
    }
    known = chapters | sections
    problems: list[str] = []
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8")
        # 링크 텍스트의 "development-rules.md 6.5" 형태만 본다.
        # URL 쪽 "#65-예외"는 앵커라서 check_links가 따로 검사한다.
        for ref in re.findall(r"development-rules\.md (\d+(?:\.\d+)?)장?", text):
            if ref not in known:
                problems.append(f"{doc}: development-rules에 없는 절을 가리킨다 — {ref}")
        if doc == RULES:
            for ref in re.findall(r"\((\d+\.\d+)\)", text):
                if ref not in known:
                    problems.append(f"{doc}: 자기 문서에 없는 절을 가리킨다 — {ref}")
        if doc.name == "git-flow-guide.md":
            for cell in table_column(section(text, "### 3.3 에이전트가 확인하는 것"), 2):
                for ref in re.findall(r"\d+\.\d+|\d+장", cell):
                    if ref.rstrip("장") not in known:
                        problems.append(f"{doc}: 점검 표가 없는 규칙을 가리킨다 — {ref}")
    return sorted(set(problems))


def check_env_sample() -> list[str]:
    """README에 적은 환경변수와 .env.sample이 같은지. 파일이 생기면 검사한다."""
    sample = Path(".env.sample")
    if not sample.exists():
        return []
    readme = README.read_text(encoding="utf-8")
    documented = set(re.findall(r"^([A-Z][A-Z0-9_]+)=", readme, re.MULTILINE))
    sample_text = sample.read_text(encoding="utf-8")
    actual = set(re.findall(r"^([A-Z][A-Z0-9_]+)=", sample_text, re.MULTILINE))
    problems = [f"{README}: .env.sample에 없는 변수 — {n}" for n in sorted(documented - actual)]
    problems += [f"{sample}: README에 없는 변수 — {n}" for n in sorted(actual - documented)]
    return problems


def main() -> int:
    problems = (
        check_links()
        + check_tool_names()
        + check_error_codes()
        + check_rule_refs()
        + check_env_sample()
    )
    if not problems:
        print(f"문서 {len(DOCS)}개, 어긋난 곳 없음.")
        return 0
    print(f"어긋난 곳 {len(problems)}개\n")
    for problem in problems:
        print(f"  {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
