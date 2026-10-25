"""TCO (Total Cost of Ownership) and ROI analytics engine comparing Forkfix against industry baselines."""

from __future__ import annotations
from typing import Any

# Published benchmark averages ($ per resolved software engineering task)
INDUSTRY_BASELINES = {
    "devin": {"name": "Cognition Devin", "cost_per_task": 3.50, "avg_seconds": 180.0},
    "claude_sonnet": {"name": "Claude 3.5 Sonnet (Linear SWE-agent)", "cost_per_task": 1.20, "avg_seconds": 120.0},
    "nemotron_ultra_monolith": {"name": "Nemotron-3-Ultra (Monolithic Single-Branch)", "cost_per_task": 0.48, "avg_seconds": 95.0},
    "human_senior_swe": {"name": "Human Senior SWE ($120/hr, 30 min debug)", "cost_per_task": 60.00, "avg_seconds": 1800.0},
}


class EconomicsAnalytics:
    @staticmethod
    def calculate_roi(actual_cost: float, actual_seconds: float) -> dict[str, Any]:
        """Calculates comparative savings and multiplier against industry standards."""
        safe_cost = max(actual_cost, 0.0001)

        comparisons = {}
        for key, baseline in INDUSTRY_BASELINES.items():
            savings_dollars = max(0.0, baseline["cost_per_task"] - safe_cost)
            cost_multiplier = round(baseline["cost_per_task"] / safe_cost, 1)
            speedup = round(baseline["avg_seconds"] / max(actual_seconds, 1.0), 1)

            comparisons[key] = {
                "name": baseline["name"],
                "baseline_cost": baseline["cost_per_task"],
                "savings_dollars": round(savings_dollars, 4),
                "multiplier": cost_multiplier,
                "speedup": speedup,
            }

        return {
            "actual_cost": round(actual_cost, 5),
            "actual_seconds": round(actual_seconds, 2),
            "comparisons": comparisons,
            "annual_savings_1000_issues": round((INDUSTRY_BASELINES["nemotron_ultra_monolith"]["cost_per_task"] - safe_cost) * 1000, 2),
        }
