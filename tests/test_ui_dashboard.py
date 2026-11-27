"""Tests for Interactive Web UI Dashboard, Static Assets, and CI/CD Workflow."""

from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_web_ui_dashboard_and_static_assets() -> None:
    """Verify Web UI HTML, CSS, and JS assets are served properly."""
    for path in ["/", "/ui"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "MDIS" in res.text
        assert "bbox-canvas" in res.text

    css_res = client.get("/static/styles.css")
    assert css_res.status_code == 200
    assert "--bg:" in css_res.text

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "SAMPLE_TOKENS" in js_res.text


def test_ci_workflow_and_smoke_script_exist() -> None:
    """Verify CI/CD workflow and live smoke test script are present."""
    root = Path(__file__).resolve().parent.parent
    ci_file = root / ".github" / "workflows" / "ci.yml"
    smoke_file = root / "scripts" / "smoke_test.py"
    assert ci_file.exists()
    assert "pytest" in ci_file.read_text(encoding="utf-8")
    assert smoke_file.exists()
