from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


class CausalRuntime:
    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))

    @staticmethod
    def _bootstrap_mean_diff(group_a: np.ndarray, group_b: np.ndarray, iterations: int = 180) -> tuple[float, float]:
        if len(group_a) < 4 or len(group_b) < 4:
            return float("nan"), float("nan")

        estimates = []
        for _ in range(iterations):
            sample_a = np.random.choice(group_a, size=len(group_a), replace=True)
            sample_b = np.random.choice(group_b, size=len(group_b), replace=True)
            estimates.append(float(np.mean(sample_a) - np.mean(sample_b)))

        low, high = np.percentile(estimates, [10, 90])
        return float(low), float(high)

    def _analyze_numeric_driver(self, frame: pd.DataFrame, target_metric: str, driver: str) -> dict[str, Any] | None:
        local = frame[[target_metric, driver]].copy()
        local[target_metric] = pd.to_numeric(local[target_metric], errors="coerce")
        local[driver] = pd.to_numeric(local[driver], errors="coerce")
        local = local.dropna()
        if len(local) < 40:
            return None

        x = local[driver].to_numpy()
        y = local[target_metric].to_numpy()
        if float(np.std(x)) == 0:
            return None

        slope, intercept = np.polyfit(x, y, 1)
        corr = float(np.corrcoef(x, y)[0, 1]) if len(x) > 1 else 0.0
        if not np.isfinite(corr):
            return None

        q1, q3 = np.percentile(x, [25, 75])
        upper = y[x >= q3]
        lower = y[x <= q1]
        if len(upper) < 10 or len(lower) < 10:
            return None

        mean_delta = float(np.mean(upper) - np.mean(lower))
        ci_low, ci_high = self._bootstrap_mean_diff(upper, lower)
        confidence = self._clamp(0.42 + (abs(corr) * 0.42) + min(len(local) / 4000, 0.12), 0.1, 0.97)

        return {
            "driver": driver,
            "kind": "numeric",
            "effect_estimate": round(mean_delta, 4),
            "uncertainty_range": [round(ci_low, 4), round(ci_high, 4)],
            "association": round(corr, 4),
            "slope": round(float(slope), 6),
            "intercept": round(float(intercept), 6),
            "support_rows": int(len(local)),
            "confidence_score": round(confidence, 2),
            "check": f"Top quartile of {driver} vs bottom quartile mean difference in {target_metric}.",
        }

    def _analyze_categorical_driver(self, frame: pd.DataFrame, target_metric: str, driver: str) -> dict[str, Any] | None:
        local = frame[[target_metric, driver]].copy()
        local[target_metric] = pd.to_numeric(local[target_metric], errors="coerce")
        local = local.dropna(subset=[target_metric, driver])
        if len(local) < 60:
            return None

        local[driver] = local[driver].astype(str)
        counts = local[driver].value_counts()
        if len(counts) < 2:
            return None

        top_categories = list(counts.head(8).index)
        local = local[local[driver].isin(top_categories)]
        baseline = top_categories[0]
        baseline_values = local[local[driver] == baseline][target_metric].to_numpy()
        if len(baseline_values) < 10:
            return None

        best: dict[str, Any] | None = None
        for category in top_categories[1:]:
            category_values = local[local[driver] == category][target_metric].to_numpy()
            if len(category_values) < 10:
                continue

            delta = float(np.mean(category_values) - np.mean(baseline_values))
            low, high = self._bootstrap_mean_diff(category_values, baseline_values)
            score = abs(delta)
            if not best or score > best["score"]:
                confidence = self._clamp(0.38 + min((len(category_values) + len(baseline_values)) / 3000, 0.25), 0.1, 0.92)
                best = {
                    "driver": driver,
                    "kind": "categorical",
                    "effect_estimate": round(delta, 4),
                    "uncertainty_range": [round(low, 4), round(high, 4)],
                    "comparison": {"category": category, "baseline": baseline},
                    "support_rows": int(len(category_values) + len(baseline_values)),
                    "confidence_score": round(confidence, 2),
                    "check": f"Difference in mean {target_metric} between {category} and {baseline}.",
                    "score": score,
                }

        if best:
            best.pop("score", None)
        return best

    def build_causal_lab_result(
        self,
        data_frame: pd.DataFrame,
        target_metric: str,
        max_drivers: int,
    ) -> dict[str, Any]:
        if target_metric not in data_frame.columns:
            raise ValueError(f"Target metric '{target_metric}' not found in dataset.")

        candidate_numeric = []
        candidate_categorical = []
        for column in data_frame.columns:
            if column == target_metric:
                continue

            series = data_frame[column]
            numeric_ratio = pd.to_numeric(series, errors="coerce").notna().mean()
            unique_values = series.dropna().nunique()
            if numeric_ratio >= 0.75:
                candidate_numeric.append(column)
            elif 1 < unique_values <= 25:
                candidate_categorical.append(column)

        findings: list[dict[str, Any]] = []
        for column in candidate_numeric[:18]:
            result = self._analyze_numeric_driver(data_frame, target_metric, column)
            if result:
                findings.append(result)

        for column in candidate_categorical[:14]:
            result = self._analyze_categorical_driver(data_frame, target_metric, column)
            if result:
                findings.append(result)

        if not findings:
            raise ValueError("Not enough usable signal to produce causal lab findings.")

        findings.sort(key=lambda item: abs(item["effect_estimate"]), reverse=True)
        top_findings = findings[:max_drivers]

        graph_nodes = [{"id": target_metric, "label": target_metric, "role": "target"}]
        graph_edges = []
        for item in top_findings:
            graph_nodes.append({"id": item["driver"], "label": item["driver"], "role": item["kind"]})
            graph_edges.append(
                {
                    "source": item["driver"],
                    "target": target_metric,
                    "weight": round(abs(item["effect_estimate"]), 4),
                    "direction": "positive" if item["effect_estimate"] >= 0 else "negative",
                }
            )

        confidence = float(np.mean([item["confidence_score"] for item in top_findings]))
        limitations = [
            "Causal lab uses quasi-experimental heuristics and observational data.",
            "Results should be validated with controlled experiments when possible.",
        ]
        if len(data_frame) < 120:
            limitations.append("Limited row count can widen uncertainty intervals.")

        return {
            "target_metric": target_metric,
            "most_likely_drivers": top_findings,
            "candidate_causal_graph": {"nodes": graph_nodes, "edges": graph_edges},
            "quasi_experimental_checks": [
                {
                    "driver": item["driver"],
                    "effect_estimate": item["effect_estimate"],
                    "uncertainty_range": item["uncertainty_range"],
                    "check": item["check"],
                    "confidence_score": item["confidence_score"],
                }
                for item in top_findings
            ],
            "confidence_score": round(confidence, 2),
            "limitations": limitations,
            "provenance": {
                "rows_analyzed": int(len(data_frame)),
                "target_metric": target_metric,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }
