from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str | None = None


class AnalyzeRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from CSV upload")
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language question")
    conversation_id: str | None = Field(default=None, max_length=100)


class HypothesisRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload")
    refresh: bool = Field(default=False, description="Force regenerate hypotheses")
    count: int = Field(default=20, ge=5, le=30, description="Number of hypotheses to generate")


class AnalysisSprintRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload")
    questions: list[str] | None = Field(default=None, description="Questions to run; defaults to generated hypotheses")
    max_questions: int = Field(default=20, ge=1, le=30, description="Maximum number of questions to run")


class CausalLabRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload")
    target_metric: str = Field(..., min_length=1, max_length=200, description="Target metric/column for driver analysis")
    max_drivers: int = Field(default=6, ge=2, le=12, description="Maximum driver findings to return")


class RegressionLabRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload")
    target_column: str = Field(..., min_length=1, max_length=200, description="Numeric target column")
    feature_columns: list[str] | None = Field(
        default=None,
        description="Optional feature columns; if omitted defaults are auto-selected",
    )
    test_fraction: float = Field(default=0.2, ge=0.1, le=0.4, description="Test split fraction")
    max_rows: int = Field(default=12000, ge=500, le=50000, description="Maximum rows sampled from session table")


class AnomalyLabRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload")
    metric_column: str = Field(..., min_length=1, max_length=200, description="Numeric metric column")
    group_by: str | None = Field(default=None, max_length=200, description="Optional grouping column")
    z_threshold: float = Field(default=3.0, ge=1.5, le=8.0, description="Absolute z-score threshold")
    max_results: int = Field(default=25, ge=5, le=100, description="Maximum anomalies returned")
    max_rows: int = Field(default=20000, ge=500, le=100000, description="Maximum rows sampled from session table")


class ActionDraftRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload")
    question: str = Field(..., min_length=1, max_length=1000)
    insight: str = Field(..., min_length=1, max_length=3000)
    sql: str = Field(..., min_length=1, max_length=10000)
    analysis_type: str = Field(default="other", max_length=100)
    trust: dict[str, Any] = Field(default_factory=dict)


class ActionApproveRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from upload")
    action_id: str = Field(..., min_length=1, max_length=200)
