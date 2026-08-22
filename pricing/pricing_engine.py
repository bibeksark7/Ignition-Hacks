"""Premium calculation: rate x units per peril, summed, plus expense loading."""

from typing import Any, Dict, List

from . import config
from .hazards import HazardFactors
from .risk_model import compute_feature_riskiness, compute_multiplier, top_drivers


def premium_for_peril(peril: str, multiplier: float, coverage_amount: float) -> float:
    units = coverage_amount / 100.0
    return config.BASE_RATES[peril] * multiplier * units


def build_peril_breakdown(
    features: Dict[str, Any], hazards: HazardFactors, coverage_amount: float
) -> List[Dict[str, Any]]:
    riskiness = compute_feature_riskiness(features, hazards)
    breakdown = []
    for peril in config.RISK_WEIGHTS:
        multiplier = compute_multiplier(peril, riskiness)
        premium = premium_for_peril(peril, multiplier, coverage_amount)
        breakdown.append(
            {
                "name": peril,
                "premium": round(premium, 2),
                "multiplier": round(multiplier, 3),
                "drivers": top_drivers(peril, features, hazards, riskiness),
            }
        )
    return breakdown


def total_premium(peril_breakdown: List[Dict[str, Any]]) -> float:
    subtotal = sum(p["premium"] for p in peril_breakdown)
    return round(subtotal * (1.0 + config.EXPENSE_LOAD), 2)
