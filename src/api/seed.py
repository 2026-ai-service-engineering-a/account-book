"""기준 데이터를 넣는다. 몇 번을 돌려도 같다.

docker compose exec api python -m api.seed      # make seed
"""

from __future__ import annotations

import logging

from api.infrastructure.db import create_db_engine
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.settings import Settings


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    engine = create_db_engine(Settings().database_url())
    with engine.begin() as connection:
        count = seed_reference(connection)
    logging.getLogger(__name__).info("seeded reference rows=%d", count)
    return count


if __name__ == "__main__":
    main()
