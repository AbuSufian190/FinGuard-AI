"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("step", sa.Integer, nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("old_balance_orig", sa.Float, nullable=False),
        sa.Column("new_balance_orig", sa.Float, nullable=False),
        sa.Column("old_balance_dest", sa.Float, nullable=False),
        sa.Column("new_balance_dest", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_transactions_type", "transactions", ["type"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("transaction_id", sa.Integer,
                  sa.ForeignKey("transactions.id", ondelete="CASCADE")),
        sa.Column("fraud_probability", sa.Float, nullable=False),
        sa.Column("is_fraud", sa.Boolean, nullable=False),
        sa.Column("risk_level", sa.String(8), nullable=False),
        sa.Column("threshold", sa.Float, nullable=False),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("source", sa.String(16)),
        sa.Column("explanation", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_predictions_is_fraud", "predictions", ["is_fraud"])
    op.create_index("ix_predictions_risk_level", "predictions", ["risk_level"])
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"])
    op.create_index("ix_predictions_created_fraud", "predictions",
                    ["created_at", "is_fraud"])

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("selection_metric", sa.String(32)),
        sa.Column("metrics", sa.JSON),
        sa.Column("is_active", sa.Boolean),
        sa.Column("trained_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "training_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("status", sa.String(16)),
        sa.Column("data_source", sa.String(128)),
        sa.Column("synthetic", sa.Boolean),
        sa.Column("message", sa.String(512)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("training_runs")
    op.drop_table("model_versions")
    op.drop_index("ix_predictions_created_fraud", "predictions")
    op.drop_index("ix_predictions_created_at", "predictions")
    op.drop_index("ix_predictions_risk_level", "predictions")
    op.drop_index("ix_predictions_is_fraud", "predictions")
    op.drop_table("predictions")
    op.drop_index("ix_transactions_type", "transactions")
    op.drop_table("transactions")
