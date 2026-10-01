"""기준 데이터를 넣는다. 몇 번을 돌려도 같다.

    python -m api.seed           # 카테고리·결제수단 (make seed)
    python -m api.seed --demo    # 거기에 더해, 거래가 하나도 없으면 여섯 달치 예시 (make demo)

`api`가 뜰 때 기준 데이터는 늘 넣는다. 예시는 개발용 구성(docker-compose.dev.yml)만 넣는다.
"""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from api.infrastructure.db import create_db_engine
from api.infrastructure.db.demo_seeder import seed_demo
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.settings import Settings


def main(argv: list[str] | None = None, now: datetime | None = None) -> int:
    """넣은(맞춘) 행 수 — 기준 데이터 + 예시 거래. `now`는 테스트가 기준 시각을 줄 때."""
    parser = argparse.ArgumentParser(prog="python -m api.seed")
    parser.add_argument("--demo", action="store_true", help="거래가 없으면 예시 데이터도 넣는다")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    settings = Settings()
    engine = create_db_engine(settings.database_url())
    with engine.begin() as connection:
        count = seed_reference(connection)
        demo = 0
        if args.demo:
            # rule-exception: 6.1 datetime.now 직접 호출 — 조립 지점 같은 실행 진입점이라 시계
            # 포트를 둘 곳이 없다. 테스트는 now를 넘긴다.
            moment = now or datetime.now(UTC)
            demo = seed_demo(connection, moment, ZoneInfo(settings.user_timezone))
    logging.getLogger(__name__).info("seeded reference=%d demo_transactions=%d", count, demo)
    return count + demo


if __name__ == "__main__":
    main()
