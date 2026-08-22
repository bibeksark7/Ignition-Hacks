"""Orchestrator: Contract A (dict) in -> Contract B (dict) out."""

from typing import Any, Dict, Optional

from . import config
from .hazards import lookup_hazards
from .mitigations import evaluate_catalogue
from .pricing_engine import build_peril_breakdown, total_premium
from .risk_model import compute_multipliers, compute_risk_scores
from .schema import validate_contract_a


def analyze(contract_a: Dict[str, Any], coverage_amount: Optional[float] = None) -> Dict[str, Any]:
    validate_contract_a(contract_a)

    lat, lon = contract_a["lat"], contract_a["lon"]
    hazards = lookup_hazards(lat, lon)

    home_value = contract_a.get("estimated_value")
    coverage = coverage_amount or home_value or config.DEFAULT_COVERAGE_AMOUNT

    multipliers = compute_multipliers(contract_a, hazards)
    risk_score = compute_risk_scores(multipliers)

    peril_breakdown = build_peril_breakdown(contract_a, hazards, coverage)
    premium = total_premium(peril_breakdown)

    mitigations, premium_if_all_actions, risk_score_if_all_actions = evaluate_catalogue(
        contract_a, hazards, coverage
    )

    result: Dict[str, Any] = {
        "risk_score": risk_score,
        "annual_premium": premium,
        "coverage_amount": coverage,
        "perils": peril_breakdown,
        "mitigations": mitigations,
        "premium_if_all_actions": premium_if_all_actions,
        "risk_score_if_all_actions": risk_score_if_all_actions,
        "disclaimer": "Demonstration model — not an actuarial quote or a property appraisal.",
    }

    if home_value is not None:
        result["home_value_estimate"] = home_value
        result["home_value_basis"] = contract_a.get("value_basis")
        result["home_value_confidence"] = contract_a.get("value_confidence")
        result["premium_pct_of_value"] = round(premium / home_value, 4) if home_value else None

    return result
