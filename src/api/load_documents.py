"""법령 Markdown 폴더를 문서와 세 전략의 조각으로 넣는다. 몇 번을 돌려도 같다.

    python -m api.load_documents tests/fixtures/ai/documents/laws    (make docs)

자료는 scripts/fetch_laws.py가 받아 둔 것이다(docs/ai/document-rag.md 3장).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from api.application.ports import UnitOfWork
from api.application.use_cases import LoadDocuments
from api.infrastructure.db import create_db_engine
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork
from api.infrastructure.settings import Settings


def main(argv: list[str] | None = None) -> int:
    """넣은 조각 수(세 전략 합)."""
    parser = argparse.ArgumentParser(prog="python -m api.load_documents")
    parser.add_argument("folder", type=Path, help="법령 Markdown이 든 폴더")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    paths = sorted(args.folder.glob("*.md"))
    if not paths:
        raise SystemExit(f"{args.folder}에 Markdown이 없다")
    settings = Settings()
    sessions = SqlUnitOfWork.factory(create_db_engine(settings.database_url()))

    def unit_of_work() -> UnitOfWork:
        return SqlUnitOfWork(sessions, settings.user_timezone)

    counts = LoadDocuments(unit_of_work)(p.read_text(encoding="utf-8") for p in paths)
    summary = " ".join(f"{s.value}={n}" for s, n in sorted(counts.items()))
    logging.getLogger(__name__).info("loaded documents=%d %s", len(paths), summary)
    return sum(counts.values())


if __name__ == "__main__":
    main()
