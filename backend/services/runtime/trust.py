from __future__ import annotations

from datetime import datetime
from typing import Any

from services.runtime.charting import MAX_PIE_POINTS


class TrustRuntime:
    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    def build_trust_layer(
        self,
        question: str,
        analysis_type: str,
        sql: str,
        row_count: int,
        visualized_row_count: int,
        chart_config: dict[str, Any],
        profile: dict[str, Any] | None,
        latency_ms: float,
    ) -> dict[str, Any]:
        profile = profile or {}
        limitations: list[str] = []

        confidence = 0.55
        if row_count == 0:
            confidence = 0.08
            limitations.append("Query returned no rows.")
        else:
            if row_count >= 500:
                confidence += 0.16
            elif row_count >= 100:
                confidence += 0.11
            elif row_count < 20:
                confidence -= 0.12
                limitations.append("Small sample size may reduce reliability.")

            if visualized_row_count < row_count:
                confidence -= 0.03
                limitations.append(
                    f"Visualization is sampled/aggregated ({visualized_row_count} of {row_count} rows shown)."
                )

            if analysis_type == "trend" and not profile.get("temporal_columns"):
                confidence -= 0.12
                limitations.append("No strongly typed temporal column detected for trend analysis.")
            if analysis_type == "correlation" and len(profile.get("numeric_columns", [])) < 2:
                confidence -= 0.12
                limitations.append("Dataset has limited numeric coverage for correlation analysis.")

        question_lower = question.lower()
        if "causal" in question_lower or "cause" in question_lower:
            confidence -= 0.08
            limitations.append("Causal inference is approximate and should be validated with experiments.")

        chart_type = chart_config.get("type", "unknown")
        if chart_type == "pie" and row_count > MAX_PIE_POINTS:
            limitations.append("Pie chart may hide detail in long-tail categories.")

        confidence = self._clamp(confidence, 0.05, 0.98)

        return {
            "confidence_score": round(confidence, 2),
            "limitations": limitations,
            "provenance": {
                "sql": sql,
                "rows_analyzed": row_count,
                "rows_visualized": visualized_row_count,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "analysis_type": analysis_type,
                "chart_type": chart_type,
                "latency_ms": round(latency_ms, 1),
            },
        }
