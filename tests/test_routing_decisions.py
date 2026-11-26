"""Unit tests for Phase 6 Part 6.3: Multi-Tier Decision Router and Cost Estimator."""

from app.routing.cost_estimator import calculate_batch_cost_savings, estimate_route_cost
from app.routing.router import DocumentTriageRouter
from app.routing.schema import RouteDecision, RouteType, RoutingPolicy
from app.triage.schema import TextLayerHealth
from app.triage.visual_schema import VisualComplexityScore


def test_native_route_selection() -> None:
    """Verify clean digital text and minimal visual clutter routes to Native ($0 cost)."""
    text_health = TextLayerHealth(
        has_text_layer=True,
        total_characters=500,
        printable_ratio=0.99,
        alpha_ratio=0.88,
        dictionary_word_ratio=0.85,
        is_garbled=False,
        health_score=0.92,
    )
    visual_score = VisualComplexityScore(
        edge_density=0.01,
        gradient_energy=1.2,
        has_complex_graphics=False,
        graphics_regions=[],
        complexity_score=0.08,
        recommended_mode="native",
    )

    router = DocumentTriageRouter()
    decision = router.route_page(text_health, visual_score)

    assert decision.route == RouteType.NATIVE
    assert decision.confidence > 0.85
    assert decision.cost_estimate.usd_cost == 0.0
    assert decision.cost_estimate.free_tier_eligible is True


def test_ocr_route_selection_for_garbled_or_scanned() -> None:
    """Verify garbled text layer routes to local OCR engine."""
    text_health = TextLayerHealth(
        has_text_layer=True,
        total_characters=300,
        printable_ratio=0.60,
        alpha_ratio=0.40,
        dictionary_word_ratio=0.30,
        is_garbled=True,
        health_score=0.0,
    )
    visual_score = VisualComplexityScore(
        edge_density=0.08,
        gradient_energy=12.0,
        has_complex_graphics=False,
        graphics_regions=[],
        complexity_score=0.25,
        recommended_mode="ocr",
    )

    router = DocumentTriageRouter()
    decision = router.route_page(text_health, visual_score)

    assert decision.route == RouteType.OCR
    assert decision.cost_estimate.usd_cost == 0.0
    assert "local OCR engine" in decision.reason


def test_vlm_route_selection_for_diagrams() -> None:
    """Verify pages with graphics, charts, or heavy diagrams route to VLM."""
    text_health = TextLayerHealth(
        has_text_layer=False,
        total_characters=0,
        printable_ratio=0.0,
        alpha_ratio=0.0,
        dictionary_word_ratio=0.0,
        is_garbled=False,
        health_score=0.0,
    )
    visual_score = VisualComplexityScore(
        edge_density=0.22,
        gradient_energy=35.0,
        has_complex_graphics=True,
        graphics_regions=[(0.2, 0.2, 0.8, 0.8)],
        complexity_score=0.75,
        recommended_mode="vlm",
    )

    router = DocumentTriageRouter()
    decision = router.route_page(text_health, visual_score, use_paid_cloud_vlm=True)

    assert decision.route == RouteType.VLM
    assert decision.cost_estimate.usd_cost > 0.0
    assert decision.cost_estimate.free_tier_eligible is False


def test_policy_forced_route_override() -> None:
    """Verify explicit policy override takes precedence over automated metrics."""
    policy = RoutingPolicy(forced_route=RouteType.OCR)
    router = DocumentTriageRouter(policy=policy)

    text_health = TextLayerHealth(
        has_text_layer=True,
        total_characters=1000,
        printable_ratio=1.0,
        alpha_ratio=0.9,
        dictionary_word_ratio=0.95,
        is_garbled=False,
        health_score=0.98,
    )
    visual_score = VisualComplexityScore(
        edge_density=0.01,
        gradient_energy=0.5,
        has_complex_graphics=False,
        graphics_regions=[],
        complexity_score=0.02,
        recommended_mode="native",
    )

    decision = router.route_page(text_health, visual_score)
    assert decision.route == RouteType.OCR
    assert decision.confidence == 1.0
    assert "forcibly overridden" in decision.reason


def test_batch_cost_savings_calculation() -> None:
    """Verify batch cost accounting compares accurately against 100% cloud VLM counterfactual."""
    decisions = [
        RouteDecision(
            route=RouteType.NATIVE,
            confidence=0.95,
            reason="Native",
            cost_estimate=estimate_route_cost(RouteType.NATIVE),
            text_health_score=0.95,
            visual_complexity_score=0.05,
        ),
        RouteDecision(
            route=RouteType.OCR,
            confidence=0.88,
            reason="OCR",
            cost_estimate=estimate_route_cost(RouteType.OCR),
            text_health_score=0.10,
            visual_complexity_score=0.20,
        ),
        RouteDecision(
            route=RouteType.VLM,
            confidence=0.90,
            reason="VLM",
            cost_estimate=estimate_route_cost(RouteType.VLM, use_paid_cloud_vlm=True),
            text_health_score=0.0,
            visual_complexity_score=0.80,
        ),
    ]

    savings = calculate_batch_cost_savings(decisions, cloud_reference_cost_per_page=0.015)
    assert savings["total_pages"] == 3.0
    assert savings["actual_cost_usd"] == 0.015  # Only 1 paid page
    assert savings["unoptimized_cost_usd"] == 0.045  # 3 * 0.015
    assert savings["saved_usd"] == 0.030
    assert savings["savings_percentage"] == 66.67
