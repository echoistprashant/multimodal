"""Live HTTP Smoke Test Script for Local or Docker MDIS Server.

Usage:
    python scripts/smoke_test.py --base-url http://localhost:8000
"""

import argparse
import sys
import httpx


def run_smoke_test(base_url: str) -> None:
    base = base_url.rstrip("/")
    with httpx.Client(timeout=15.0) as client:
        # 1. Health & System Info
        r_health = client.get(f"{base}/health")
        r_health.raise_for_status()
        print("[OK] /health:", r_health.json())

        r_info = client.get(f"{base}/api/v1/system/info")
        r_info.raise_for_status()
        print("[OK] /api/v1/system/info:", r_info.json())

        # 2. Web UI Dashboard
        r_ui = client.get(f"{base}/ui")
        r_ui.raise_for_status()
        assert "MDIS" in r_ui.text
        print("[OK] /ui Dashboard served")

        # 3. End-to-End Pipeline Execution
        tokens = [
            {"id": "t1", "text": "TAX INVOICE #SMOKE-101", "bbox": [0.1, 0.05, 0.9, 0.1]},
            {"id": "t2", "text": "Vendor: Smoke Test Corp", "bbox": [0.1, 0.14, 0.6, 0.18]},
            {"id": "t3", "text": "Total Amount: $500.00", "bbox": [0.5, 0.6, 0.9, 0.65]},
        ]
        r_proc = client.post(
            f"{base}/api/v1/documents/smoke-doc-1/process",
            json={"pages": [{"page_no": 1, "tokens": tokens}]},
        )
        r_proc.raise_for_status()
        print("[OK] /process:", r_proc.json()["approval_decision"])

        # 4. RAG Query
        r_rag = client.post(
            f"{base}/api/v1/rag/query",
            json={"query": "Smoke Test Corp $500.00", "top_k": 2},
        )
        r_rag.raise_for_status()
        print("[OK] /rag/query citations:", len(r_rag.json()["citations"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MDIS Live Smoke Test")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Server base URL")
    args = parser.parse_args()
    try:
        run_smoke_test(args.base_url)
        print("\nAll live smoke tests PASSED!")
    except Exception as exc:
        print(f"\nSmoke test FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
