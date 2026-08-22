"""Mitigation engine: for each catalogue fix, change one feature (or apply a direct
multiplier reduction), re-run pricing, and take the difference. Sort by payback.
"""

import copy
from typing import Any, Dict, List, Tuple

from . import config
from .hazards import HazardFactors
from .pricing_engine import premium_for_peril
from .risk_model import compute_multipliers, compute_risk_scores


def _premiums_from_multipliers(multipliers: Dict[str, float], coverage_amount: float) -> Dict[str, float]:
    return {peril: premium_for_peril(peril, m, coverage_amount) for peril, m in multipliers.items()}


def _total_from_premiums(premiums: Dict[str, float]) -> float:
    return round(sum(premiums.values()) * (1.0 + config.EXPENSE_LOAD), 2)


def _clamp_multiplier(value: float) -> float:
    return max(config.MULTIPLIER_MIN, min(config.MULTIPLIER_MAX, value))


def _apply_feature_entry(features: Dict[str, Any], entry: Dict[str, Any]) -> Dict[str, Any]:
    new_features = dict(features)
    feature = entry["feature"]
    if "set_value" in entry:
        new_features[feature] = entry["set_value"]
    elif "cap" in entry:
        new_features[feature] = min(features[feature], entry["cap"])
    else:
        min_value = entry.get("min_value", float("-inf"))
        new_features[feature] = max(min_value, features[feature] + entry["delta"])
    return new_features


def evaluate_catalogue(
    features: Dict[str, Any], hazards: HazardFactors, coverage_amount: float
) -> Tuple[List[Dict[str, Any]], float, Dict[str, Any]]:
    baseline_multipliers = compute_multipliers(features, hazards)
    baseline_total = _total_from_premiums(_premiums_from_multipliers(baseline_multipliers, coverage_amount))
    baseline_scores = compute_risk_scores(baseline_multipliers)

    results: List[Dict[str, Any]] = []
    all_features = copy.deepcopy(features)
    all_multiplier_overrides: Dict[str, float] = {}

    for entry in config.MITIGATION_CATALOGUE:
        if entry["mode"] == "feature":
            new_features = _apply_feature_entry(features, entry)
            new_multipliers = compute_multipliers(new_features, hazards)
            all_features = _apply_feature_entry(all_features, entry)
        else:  # direct_effect
            new_multipliers = dict(baseline_multipliers)
            peril = entry["peril"]
            new_multipliers[peril] = _clamp_multiplier(new_multipliers[peril] + entry["multiplier_delta"])
            all_multiplier_overrides[peril] = all_multiplier_overrides.get(peril, 0.0) + entry["multiplier_delta"]

        new_total = _total_from_premiums(_premiums_from_multipliers(new_multipliers, coverage_amount))
        new_scores = compute_risk_scores(new_multipliers)

        annual_saving = round(baseline_total - new_total, 2)
        payback_years = round(entry["cost"] / annual_saving, 1) if annual_saving > 0 else None

        results.append(
            {
                "action": entry["action"],
                "cost": entry["cost"],
                "annual_saving": annual_saving,
                "payback_years": payback_years,
                "peril": entry["peril"],
                "risk_score_delta": round(new_scores["overall"] - baseline_scores["overall"], 1),
                "co_benefit": entry["co_benefit"],
            }
        )

    results.sort(key=lambda r: r["payback_years"] if r["payback_years"] is not None else float("inf"))

    combined_multipliers = compute_multipliers(all_features, hazards)
    for peril, delta in all_multiplier_overrides.items():
        combined_multipliers[peril] = _clamp_multiplier(combined_multipliers[peril] + delta)
    premium_if_all_actions = _total_from_premiums(_premiums_from_multipliers(combined_multipliers, coverage_amount))
    risk_score_if_all_actions = compute_risk_scores(combined_multipliers)

    return results, premium_if_all_actions, risk_score_if_all_actions
