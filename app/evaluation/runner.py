"""Benchmark Runner for Golden Dataset Evaluation."""

from typing import Any, Dict, List, Set
from app.evaluation.benchmark import evaluate_extraction_accuracy, evaluate_grounding_metrics
from app.evaluation.extraction_metrics import BenchmarkReport, FieldAccuracyMetrics, GroundingMetrics
from app.evaluation.rag_metrics import compute_mrr, compute_recall_at_k
from app.grounding.schema import ProvenanceMatch


class BenchmarkRunner:
    """Aggregates extraction F1, grounding coverage, and RAG retrieval metrics."""

    def run_suite(
        self,
        dataset_name: str,
        extraction_pairs: List[tuple[Dict[str, Any], Dict[str, Any]]],
        grounding_batches: List[List[ProvenanceMatch]],
        rag_ranked_lists: List[List[str]] | None = None,
        rag_relevant_sets: List[Set[str]] | None = None,
        k: int = 5,
    ) -> BenchmarkReport:
        """Compute aggregate benchmark report across all evaluation cases."""
        if extraction_pairs:
            ext_results = [evaluate_extraction_accuracy(pred, gt) for pred, gt in extraction_pairs]
            n = len(ext_results)
            ext_metrics = FieldAccuracyMetrics(
                exact_match_rate=round(sum(r.exact_match_rate for r in ext_results) / n, 4),
                fuzzy_match_rate=round(sum(r.fuzzy_match_rate for r in ext_results) / n, 4),
                precision=round(sum(r.precision for r in ext_results) / n, 4),
                recall=round(sum(r.recall for r in ext_results) / n, 4),
                f1_score=round(sum(r.f1_score for r in ext_results) / n, 4),
            )
        else:
            ext_metrics = FieldAccuracyMetrics(
                exact_match_rate=0.0, fuzzy_match_rate=0.0, precision=0.0, recall=0.0, f1_score=0.0
            )

        all_matches = [m for batch in grounding_batches for m in batch]
        grd_metrics: GroundingMetrics = evaluate_grounding_metrics(all_matches)

        recall_k = 0.0
        mrr = 0.0
        if rag_ranked_lists and rag_relevant_sets and len(rag_ranked_lists) == len(rag_relevant_sets):
            recalls = [compute_recall_at_k(r, rel, k=k) for r, rel in zip(rag_ranked_lists, rag_relevant_sets)]
            recall_k = round(sum(recalls) / len(recalls), 4)
            mrr = compute_mrr(rag_ranked_lists, rag_relevant_sets)

        return BenchmarkReport(
            dataset_name=dataset_name,
            documents_evaluated=len(extraction_pairs),
            extraction_metrics=ext_metrics,
            grounding_metrics=grd_metrics,
            rag_recall_at_k=recall_k,
            rag_mrr=mrr,
        )
