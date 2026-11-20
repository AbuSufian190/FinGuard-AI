"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .ml.config import TRANSACTION_TYPES

TransactionType = Literal["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"]


class TransactionInput(BaseModel):
    """A single transaction to score. Mirrors the PaySim raw schema."""
    step: int = Field(0, ge=0, le=100_000,
                      description="Simulation hour (0 = unknown).")
    type: TransactionType
    amount: float = Field(..., ge=0, le=1e12)
    oldbalanceOrg: float = Field(..., ge=0, le=1e12)
    newbalanceOrig: float = Field(..., ge=0, le=1e12)
    oldbalanceDest: float = Field(..., ge=0, le=1e12)
    newbalanceDest: float = Field(..., ge=0, le=1e12)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "step": 100, "type": "TRANSFER", "amount": 181000.0,
            "oldbalanceOrg": 181000.0, "newbalanceOrig": 0.0,
            "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
        }
    })


class ExplanationFeature(BaseModel):
    feature: str
    contribution: float
    value: float
    direction: str


class Explanation(BaseModel):
    method: str
    top_features: list[ExplanationFeature]


class PredictionResult(BaseModel):
    fraud_probability: float
    is_fraud: bool
    risk_level: str
    threshold: float
    model_name: str
    model_version: str


class PredictionResponse(PredictionResult):
    id: int
    created_at: datetime
    transaction: TransactionInput
    explanation: Explanation | None = None


class BatchRowResult(BaseModel):
    row: int
    fraud_probability: float
    is_fraud: bool
    risk_level: str


class BatchSummary(BaseModel):
    total_rows: int
    flagged_fraud: int
    fraud_rate: float
    high_risk: int


class BatchPredictionResponse(BaseModel):
    summary: BatchSummary
    results: list[BatchRowResult]
    result_csv_base64: str | None = None


class HistoryItem(BaseModel):
    id: int
    created_at: datetime
    type: str
    amount: float
    fraud_probability: float
    is_fraud: bool
    risk_level: str
    source: str
    model_config = ConfigDict(from_attributes=True)


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class DashboardSummary(BaseModel):
    total_transactions: int
    fraudulent_detected: int
    fraud_detection_rate: float
    average_amount: float
    trend: list[dict]
    fraud_distribution: list[dict]
    recent_suspicious: list[HistoryItem]


class ModelInfo(BaseModel):
    model_name: str
    model_version: str
    selection_metric: str
    decision_threshold: float
    trained_at: str | None = None
    data_source: str | None = None
    synthetic_data: bool | None = None
    features: list[str]
    loaded: bool


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    database: str
    version: str


class TrainResponse(BaseModel):
    training_run_id: int
    status: str
    message: str
