from __future__ import annotations

from api.infrastructure.db.rows import AgentRunRow


def test_maps_the_agent_runs_table():
    assert AgentRunRow.__tablename__ == "agent_runs"
