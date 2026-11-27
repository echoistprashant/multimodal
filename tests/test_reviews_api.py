"""Integration tests for Phase 11 Part 11.4: Review Queue Repository and API."""

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.review_repo import ReviewQueueRepository
from app.review.task_generator import ReviewTaskItem

client = TestClient(app)


def test_reviews_api_list_and_resolve() -> None:
    """Verify listing pending review tasks and resolving one via POST /resolve."""
    repo = ReviewQueueRepository()
    repo.clear_cache()

    task = ReviewTaskItem(
        document_id="doc-rev-1",
        field_id="doc-rev-1::field_0",
        field_path="total_amount",
        original_value=999.0,
        confidence=0.40,
        bbox=[0.7, 0.8, 0.9, 0.85],
        page_no=1,
        reason="Arithmetic mismatch with subtotal + tax",
        priority=1,
    )
    repo.enqueue_tasks([task])

    # 1. List pending
    list_res = client.get("/api/v1/reviews?task_status=pending")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["items"][0]["task_id"] == task.task_id

    # 2. Resolve task
    resolve_res = client.post(
        f"/api/v1/reviews/{task.task_id}/resolve",
        json={
            "corrected_value": 110.0,
            "reviewer": "alice@enterprise.com",
            "notes": "Verified against PDF scan",
        },
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    assert resolved["status"] == "resolved"
    assert resolved["corrected_value"] == 110.0
    assert resolved["assigned_to"] == "alice@enterprise.com"

    # 3. Pending queue should now be empty
    after_res = client.get("/api/v1/reviews?task_status=pending")
    assert after_res.json()["total"] == 0

    # 4. 404 on unknown task
    assert client.post("/api/v1/reviews/nonexistent-id/resolve", json={"corrected_value": 1}).status_code == 404
