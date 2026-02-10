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
