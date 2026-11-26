"""Deterministic Multi-Tier Decision Router.

Analyzes text layer health and visual complexity metrics to make deterministic,
cost-aware routing decisions across Native, OCR, and VLM pathways.
"""

from app.routing.cost_estimator import estimate_route_cost
from app.routing.schema import RouteDecision, RouteType, RoutingPolicy
from app.triage.schema import TextLayerHealth
from app.triage.visual_schema import VisualComplexityScore


class DocumentTriageRouter:
    """Intelligent triage router optimizing extraction accuracy against operational compute cost."""

    def __init__(self, policy: RoutingPolicy | None = None) -> None:
        self.policy = policy or RoutingPolicy()

    def route_page(
        self,
        text_health: TextLayerHealth,
        visual_complexity: VisualComplexityScore,
        use_paid_cloud_vlm: bool = False,
    ) -> RouteDecision:
        """Evaluate triage metrics and determine the optimal execution route for a page.

        Args:
            text_health: Evaluated health of the embedded PDF text layer.
            visual_complexity: Evaluated edge density and graphics metrics of page image.
            use_paid_cloud_vlm: Whether VLM execution incurs cloud API cost.

        Returns:
            RouteDecision containing the chosen route, confidence, and cost estimate.
        """
        # 1. Manual Policy Override
        if self.policy.forced_route is not None:
            cost = estimate_route_cost(self.policy.forced_route, use_paid_cloud_vlm=use_paid_cloud_vlm)
            return RouteDecision(
                route=self.policy.forced_route,
                confidence=1.0,
                reason=f"Execution pathway forcibly overridden to '{self.policy.forced_route.value}' by policy.",
                cost_estimate=cost,
                text_health_score=text_health.health_score,
                visual_complexity_score=visual_complexity.complexity_score,
            )

        # 2. Check for High-Fidelity Native PDF Text Layer
        can_use_native = (
            text_health.has_text_layer
            and not text_health.is_garbled
            and text_health.health_score >= self.policy.min_text_health_threshold
            and not visual_complexity.has_complex_graphics
            and visual_complexity.complexity_score < self.policy.max_visual_complexity_for_ocr
        )

        if can_use_native:
            cost = estimate_route_cost(RouteType.NATIVE, use_paid_cloud_vlm=use_paid_cloud_vlm)
            confidence = round(0.5 * text_health.health_score + 0.5 * (1.0 - visual_complexity.complexity_score), 4)
            return RouteDecision(
                route=RouteType.NATIVE,
                confidence=confidence,
                reason="High-fidelity digital text layer present with clean encoding and minimal visual clutter.",
                cost_estimate=cost,
                text_health_score=text_health.health_score,
                visual_complexity_score=visual_complexity.complexity_score,
            )

        # 3. Check for High Visual Complexity / Diagrams requiring Multimodal Vision
        requires_vlm = (
            visual_complexity.has_complex_graphics
            or visual_complexity.complexity_score > self.policy.max_visual_complexity_for_ocr
        )

        if requires_vlm:
            cost = estimate_route_cost(RouteType.VLM, use_paid_cloud_vlm=use_paid_cloud_vlm)
            confidence = round(max(visual_complexity.complexity_score, 0.75), 4)
            return RouteDecision(
                route=RouteType.VLM,
                confidence=confidence,
                reason="High visual complexity or diagram/chart graphics detected requiring multimodal vision reasoning.",
                cost_estimate=cost,
                text_health_score=text_health.health_score,
                visual_complexity_score=visual_complexity.complexity_score,
            )

        # 4. Standard Scanned or Degraded Text requiring Local OCR
        cost = estimate_route_cost(RouteType.OCR, use_paid_cloud_vlm=use_paid_cloud_vlm)
        ocr_confidence = round(0.85 if not text_health.is_garbled else 0.70, 4)
        reason = "Scanned document or missing/corrupted native text layer; routing to local OCR engine."

        return RouteDecision(
            route=RouteType.OCR,
            confidence=ocr_confidence,
            reason=reason,
            cost_estimate=cost,
            text_health_score=text_health.health_score,
            visual_complexity_score=visual_complexity.complexity_score,
        )
