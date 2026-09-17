#!/usr/bin/env python3
"""파일 300줄 상한 검사 — docs/development-rules.md 1.1.

의존성 없이 표준 라이브러리만 쓴다. 컨테이너가 떠 있지 않아도 훅에서 돌아야 하기 때문이다.

  python3 scripts/check_file_length.py                # 작업 트리 전체
  python3 scripts/check_file_length.py --base develop # base 이후 바뀐 파일만
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

LIMIT = 300
WARN = 250
TARGET_DIRS = ("src", "tests", "scripts")
SUFFIXES = {".py"}


def _is_target(path: Path) -> bool:
    return path.suffix in SUFFIXES and path.parts and path.parts[0] in TARGET_DIRS


def changed_files(base: str) -> list[Path]:
    """base와 HEAD의 공통 조상 이후 추가·수정된 파일."""
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=d", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [Path(line) for line in out.splitlines() if line]


def all_files() -> list[Path]:
    return [p for d in TARGET_DIRS for p in Path(d).rglob("*") if p.is_file()]


def line_count(path: Path) -> int:
    with path.open("rb") as fh:
        return sum(1 for _ in fh)


def main() -> int:
    parser = argparse.ArgumentParser(description="파일 300줄 상한 검사")
    parser.add_argument("--base", help="이 브랜치 이후 바뀐 파일만 검사한다")
    args = parser.parse_args()

    candidates = changed_files(args.base) if args.base else all_files()
    targets = sorted({p for p in candidates if _is_target(p) and p.exists()})

    over: list[tuple[Path, int]] = []
    near: list[tuple[Path, int]] = []
    for path in targets:
        count = line_count(path)
        if count > LIMIT:
            over.append((path, count))
        elif count > WARN:
            near.append((path, count))

    for path, count in near:
        print(f"  주의  {path}  {count}줄 (상한 {LIMIT})")

    if not over:
        return 0

    print(f"\n파일 {LIMIT}줄 상한을 넘었습니다. ({len(over)}개)\n")
    for path, count in over:
        print(f"  초과  {path}  {count}줄  (+{count - LIMIT})")
    print(
        "\n쪼개는 순서는 docs/development-rules.md 1.1을 따릅니다."
        "\n반으로 잘라 _part2.py를 만드는 건 규칙 위반보다 나쁩니다."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
