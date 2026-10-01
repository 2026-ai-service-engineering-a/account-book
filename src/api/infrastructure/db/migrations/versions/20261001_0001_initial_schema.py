"""첫 스키마 — README 7장의 테이블과 카테고리 고르기의 text_embeddings·category_rules.

pgvector 확장을 켜고 text_embeddings.vector(768)에 HNSW(코사인) 인덱스를 건다.

Revision ID: 0001
Revises:
Create Date: 2026-10-01 10:29:22.827675+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # vector 타입이 있어야 text_embeddings를 만들 수 있다. 확장은 DB 이미지(pgvector/pgvector)에
    # 들어 있고, 켜는 것은 DB마다 한 번이다.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.CheckConstraint("kind IN ('cash', 'card', 'bank')", name=op.f("ck_accounts_kind")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
    )
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("utterance", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("steps", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "cost_usd", sa.Numeric(precision=10, scale=6), server_default="0", nullable=False
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_runs")),
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("parent_id", sa.String(length=32), nullable=True),
        sa.CheckConstraint(
            "direction IN ('expense', 'income')", name=op.f("ck_categories_direction")
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"], ["categories.id"], name=op.f("fk_categories_parent_id_categories")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
    )
    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_idempotency_keys")),
    )
    op.create_index(
        op.f("ix_idempotency_keys_created_at"), "idempotency_keys", ["created_at"], unique=False
    )
    op.create_table(
        "text_embeddings",
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("vector", pgvector.sqlalchemy.vector.VECTOR(dim=768), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("model", "text_hash", name=op.f("pk_text_embeddings")),
    )
    op.create_index(
        "ix_text_embeddings_vector",
        "text_embeddings",
        ["vector"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"vector": "vector_cosine_ops"},
    )
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("category_id", sa.String(length=32), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("limit_amount", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'", name=op.f("ck_budgets_period_format")
        ),
        sa.CheckConstraint("limit_amount > 0", name=op.f("ck_budgets_limit_positive")),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name=op.f("fk_budgets_category_id_categories")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_budgets")),
        sa.UniqueConstraint("category_id", "period", name=op.f("uq_budgets_category_id_period")),
    )
    op.create_table(
        "category_rules",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("merchant_pattern", sa.String(length=100), nullable=False),
        sa.Column("category_id", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("hit_count", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint("source IN ('seed', 'user')", name=op.f("ck_category_rules_source")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_category_rules_category_id_categories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_category_rules")),
        sa.UniqueConstraint("merchant_pattern", name=op.f("uq_category_rules_merchant_pattern")),
    )
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("tool", sa.String(length=50), nullable=False),
        sa.Column("args", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["agent_runs.id"], name=op.f("fk_tool_calls_run_id_agent_runs")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tool_calls")),
    )
    op.create_index(op.f("ix_tool_calls_run_id"), "tool_calls", ["run_id"], unique=False)
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("account_id", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.String(length=32), nullable=False),
        sa.Column("merchant", sa.String(length=100), server_default="", nullable=False),
        sa.Column("memo", sa.String(length=200), server_default="", nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "direction IN ('expense', 'income')", name=op.f("ck_transactions_direction")
        ),
        sa.CheckConstraint(
            "source IN ('manual', 'agent', 'import')", name=op.f("ck_transactions_source")
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_transactions_amount_positive")),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.id"], name=op.f("fk_transactions_account_id_accounts")
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name=op.f("fk_transactions_category_id_categories")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
    )
    op.create_index(
        op.f("ix_transactions_category_id_occurred_at"),
        "transactions",
        ["category_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_occurred_at"), "transactions", ["occurred_at"], unique=False
    )


def downgrade() -> None:
    # 확장은 끄지 않는다. 같은 DB의 다른 것이 쓰고 있을 수 있고, 켜 두어도 비용이 없다.
    op.drop_index(op.f("ix_transactions_occurred_at"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_category_id_occurred_at"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(op.f("ix_tool_calls_run_id"), table_name="tool_calls")
    op.drop_table("tool_calls")
    op.drop_table("category_rules")
    op.drop_table("budgets")
    op.drop_index(
        "ix_text_embeddings_vector",
        table_name="text_embeddings",
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"vector": "vector_cosine_ops"},
    )
    op.drop_table("text_embeddings")
    op.drop_index(op.f("ix_idempotency_keys_created_at"), table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
    op.drop_table("categories")
    op.drop_table("agent_runs")
    op.drop_table("accounts")
