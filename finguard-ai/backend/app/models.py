"""SQLAlchemy ORM models for FinGuard AI."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Index,
                        Integer, String)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    old_balance_orig: Mapped[float] = mapped_column(Float, nullable=False)
    new_balance_orig: Mapped[float] = mapped_column(Float, nullable=False)
    old_balance_dest: Mapped[float] = mapped_column(Float, nullable=False)
    new_balance_dest: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=_utcnow)

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), nullable=True)

    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False)
    is_fraud: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(8), nullable=False,
                                            index=True)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)

    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="single")
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=_utcnow, index=True)

    transaction: Mapped[Transaction | None] = relationship(
        back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_created_fraud", "created_at", "is_fraud"),
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    selection_metric: Mapped[str] = mapped_column(String(32))
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    trained_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=_utcnow)


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    data_source: Mapped[str | None] = mapped_column(String(128), nullable=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
