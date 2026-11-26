"""Cost and Latency Estimation Engine.

Computes fine-grained resource expenditure, dollar costs, and financial savings
for document processing pathways (Native PDF vs. Local Open-Source OCR vs. Multimodal VLM).
"""

from typing import Sequence
from app.routing.schema import EstimatedCost, RouteDecision, RouteType

# Baseline cost and latency benchmarks per page
BENCHMARK_PROFILES: dict[RouteType, dict[str, float | bool]] = {
    RouteType.NATIVE: {
        "usd_cost": 0.0000,
        "latency_ms": 15.0,
        "free_tier_eligible": True,
    },
    RouteType.OCR: {
        "usd_cost": 0.0000,
        "latency_ms": 350.0,
        "free_tier_eligible": True,
    },
    RouteType.VLM: {
        # Default open-source local / free-tier model (e.g. Gemini Free / Ollama)
        "usd_cost": 0.0000,
        "latency_ms": 1800.0,
        "free_tier_eligible": True,
    },
    RouteType.FALLBACK: {
        "usd_cost": 0.0000,
        "latency_ms": 400.0,
        "free_tier_eligible": True,
    },
}

# Commercial cloud VLM reference pricing (e.g., standard proprietary vision API)
CLOUD_VLM_REFERENCE_USD_PER_PAGE = 0.0150


def estimate_route_cost(
    route: RouteType,
    use_paid_cloud_vlm: bool = False,
) -> EstimatedCost:
    """Calculate cost and expected latency for a given execution route.

    Args:
        route: The execution route tier.
        use_paid_cloud_vlm: Whether VLM execution uses commercial paid API rather than free/local.

    Returns:
        EstimatedCost model with USD cost, latency in ms, and free tier status.
    """
    profile = BENCHMARK_PROFILES.get(route, BENCHMARK_PROFILES[RouteType.FALLBACK])

    usd_cost = float(profile["usd_cost"])
    latency_ms = float(profile["latency_ms"])
    free_tier_eligible = bool(profile["free_tier_eligible"])

    if route == RouteType.VLM and use_paid_cloud_vlm:
        usd_cost = CLOUD_VLM_REFERENCE_USD_PER_PAGE
        free_tier_eligible = False

    return EstimatedCost(
        route=route,
        usd_cost=usd_cost,
        latency_ms=latency_ms,
        free_tier_eligible=free_tier_eligible,
    )


def calculate_batch_cost_savings(
    decisions: Sequence[RouteDecision],
    cloud_reference_cost_per_page: float = CLOUD_VLM_REFERENCE_USD_PER_PAGE,
) -> dict[str, float]:
    """Calculate financial cost savings achieved by intelligent multi-tier triage routing.

    Compares the total incurred triage cost against the counterfactual scenario
    where 100% of pages were sent directly to high-cost commercial vision models.

    Returns:
        dict with total_pages, actual_cost_usd, unoptimized_cost_usd, saved_usd, savings_percentage.
    """
    total_pages = len(decisions)
    if total_pages == 0:
        return {
            "total_pages": 0.0,
            "actual_cost_usd": 0.0,
            "unoptimized_cost_usd": 0.0,
            "saved_usd": 0.0,
            "savings_percentage": 0.0,
        }

    actual_cost = sum(d.cost_estimate.usd_cost for d in decisions)
    unoptimized_cost = total_pages * cloud_reference_cost_per_page
    saved_usd = max(0.0, unoptimized_cost - actual_cost)
    savings_pct = (saved_usd / unoptimized_cost) * 100.0 if unoptimized_cost > 0 else 0.0

    return {
        "total_pages": float(total_pages),
        "actual_cost_usd": round(actual_cost, 4),
        "unoptimized_cost_usd": round(unoptimized_cost, 4),
        "saved_usd": round(saved_usd, 4),
        "savings_percentage": round(savings_pct, 2),
    }
