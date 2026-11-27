"""Unit tests for Phase 13 Part 13.1: Extraction F1, Grounding, and RAG MRR Benchmarks."""

from app.evaluation.benchmark import evaluate_extraction_accuracy
from app.evaluation.rag_metrics import compute_mrr, compute_recall_at_k
from app.evaluation.runner import BenchmarkRunner
from app.grounding.schema import GroundingStatus, ProvenanceMatch


def test_extraction_f1_and_rag_metrics() -> None:
    """Verify F1 accuracy, Recall@K, MRR, and BenchmarkRunner aggregation."""
    pred = {"invoice_number": "INV-100", "vendor": {"name": "Acme Corp"}, "total_amount": 500.0}
    gt = {"invoice_number": "INV-100", "vendor": {"name": "Acme Corp."}, "total_amount": 500.0}

    metrics = evaluate_extraction_accuracy(pred, gt)
    assert metrics.f1_score == 1.0
    assert metrics.precision == 1.0

    assert compute_recall_at_k(["c1", "c2", "c3"], {"c2", "c4"}, k=3) == 0.5
    assert compute_mrr([["c3", "c1"], ["c2", "c4"]], [{"c1"}, {"c2"}]) == 0.75

    matches = [
        ProvenanceMatch(field_path="invoice_number", extracted_value="INV-100", status=GroundingStatus.EXACT, grounded=True, confidence=1.0),
        ProvenanceMatch(field_path="total_amount", extracted_value=500.0, status=GroundingStatus.NUMERIC, grounded=True, confidence=1.0),
    ]
    report = BenchmarkRunner().run_suite(
        dataset_name="golden_v1",
        extraction_pairs=[(pred, gt)],
        grounding_batches=[matches],
        rag_ranked_lists=[["c1", "c2"]],
        rag_relevant_sets=[{"c1"}],
        k=2,
    )
    assert report.documents_evaluated == 1
    assert report.grounding_metrics.hallucination_rate == 0.0
    assert report.rag_recall_at_k == 1.0
    assert report.rag_mrr == 1.0
