"""Evaluation Benchmark Schemas for Extraction, Grounding, and RAG."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class FieldAccuracyMetrics(BaseModel):
    """Precision, Recall, and F1 metrics for structured field extraction."""

    model_config = ConfigDict(frozen=True)

    exact_match_rate: float = Field(ge=0.0, le=1.0)
    fuzzy_match_rate: float = Field(ge=0.0, le=1.0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1_score: float = Field(ge=0.0, le=1.0)


class GroundingMetrics(BaseModel):
    """Provenance coverage and hallucination rate metrics."""

    model_config = ConfigDict(frozen=True)

    grounding_coverage: float = Field(ge=0.0, le=1.0)
    hallucination_rate: float = Field(ge=0.0, le=1.0)


class BenchmarkReport(BaseModel):
    """Aggregate benchmark summary across a golden evaluation dataset."""

    model_config = ConfigDict(frozen=True)

    dataset_name: str
    documents_evaluated: int = Field(ge=0)
    extraction_metrics: FieldAccuracyMetrics
    grounding_metrics: GroundingMetrics
    rag_recall_at_k: float = Field(default=0.0, ge=0.0, le=1.0)
    rag_mrr: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: List[str] = Field(default_factory=list)
