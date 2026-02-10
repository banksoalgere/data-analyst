from __future__ import annotations

from datetime import datetime
from typing import Any

MAX_VIZ_POINTS = 320
MAX_SCATTER_POINTS = 700
MAX_BAR_POINTS = 30
MAX_PIE_POINTS = 12
CHART_TYPES = {"line", "bar", "scatter", "pie", "area"}


class ChartRuntime:
    @staticmethod
    def _is_numeric(value: Any) -> bool:
        if isinstance(value, bool) or value is None:
            return False
        if isinstance(value, (int, float)):
            return True
        try:
            float(str(value).replace(",", ""))
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _looks_temporal(value: Any) -> bool:
        if isinstance(value, datetime):
            return True
        if not isinstance(value, str):
            return False

        raw = value.strip()
        if not raw:
            return False

        if any(token in raw for token in ("-", "/", ":")) and len(raw) >= 8:
            try:
                datetime.fromisoformat(raw.replace("Z", "+00:00"))
                return True
            except ValueError:
                return False
        return False

    def infer_chart_columns(self, data: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
        if not data:
            return [], [], []

        sample = data[: min(200, len(data))]
        keys = list(sample[0].keys())
        numeric_keys: list[str] = []
        temporal_keys: list[str] = []
        categorical_keys: list[str] = []

        for key in keys:
            values = [row.get(key) for row in sample if row.get(key) is not None]
            if not values:
                continue

            numeric_ratio = sum(1 for value in values if self._is_numeric(value)) / len(values)
            temporal_ratio = sum(1 for value in values if self._looks_temporal(value)) / len(values)

            if numeric_ratio >= 0.8:
                numeric_keys.append(key)
            elif temporal_ratio >= 0.8:
                temporal_keys.append(key)
            else:
                categorical_keys.append(key)

        return numeric_keys, temporal_keys, categorical_keys

    def normalize_chart_config(
        self,
        data: list[dict[str, Any]],
        base_config: dict[str, Any],
    ) -> dict[str, Any]:
        if not data:
            return {"type": "bar", "xKey": "", "yKey": ""}

        keys = list(data[0].keys())
        numeric_keys, temporal_keys, categorical_keys = self.infer_chart_columns(data)

        chart_type = base_config.get("type")
        if chart_type not in CHART_TYPES:
            chart_type = "bar"

        x_key = base_config.get("xKey")
        y_key = base_config.get("yKey")
        group_by = base_config.get("groupBy")

        if x_key not in keys:
            x_key = temporal_keys[0] if temporal_keys else (categorical_keys[0] if categorical_keys else keys[0])

        if y_key not in keys or y_key == x_key:
            if numeric_keys:
                candidate = numeric_keys[0]
                if candidate == x_key and len(numeric_keys) > 1:
                    candidate = numeric_keys[1]
                y_key = candidate
            else:
                y_key = keys[1] if len(keys) > 1 else keys[0]

        if chart_type == "scatter":
            if len(numeric_keys) >= 2:
                x_key = numeric_keys[0]
                y_key = numeric_keys[1]
            else:
                chart_type = "bar"

        if chart_type in {"line", "area"} and temporal_keys and x_key not in temporal_keys:
            x_key = temporal_keys[0]

        normalized = {"type": chart_type, "xKey": x_key, "yKey": y_key}
        if isinstance(group_by, str) and group_by in keys and group_by not in {x_key, y_key}:
            normalized["groupBy"] = group_by

        return normalized

    def build_chart_options(
        self,
        data: list[dict[str, Any]],
        base_config: dict[str, Any],
        analysis_type: str,
    ) -> list[dict[str, Any]]:
        if not data:
            return [base_config]

        numeric_keys, temporal_keys, categorical_keys = self.infer_chart_columns(data)
        base = self.normalize_chart_config(data, base_config)
        options: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()

        def add_option(option: dict[str, Any]):
            signature = (
                option.get("type"),
                option.get("xKey"),
                option.get("yKey"),
                option.get("groupBy"),
            )
            if signature in seen:
                return
            seen.add(signature)
            options.append(option)

        add_option(base)

        if temporal_keys and numeric_keys:
            add_option({"type": "line", "xKey": temporal_keys[0], "yKey": numeric_keys[0]})
            add_option({"type": "area", "xKey": temporal_keys[0], "yKey": numeric_keys[0]})

        if categorical_keys and numeric_keys:
            add_option({"type": "bar", "xKey": categorical_keys[0], "yKey": numeric_keys[0]})
            unique_values = len({str(row.get(categorical_keys[0])) for row in data if row.get(categorical_keys[0]) is not None})
            if unique_values <= MAX_PIE_POINTS:
                add_option({"type": "pie", "xKey": categorical_keys[0], "yKey": numeric_keys[0]})

        if len(numeric_keys) >= 2:
            add_option({"type": "scatter", "xKey": numeric_keys[0], "yKey": numeric_keys[1]})

        if analysis_type == "correlation":
            options.sort(key=lambda item: 0 if item["type"] == "scatter" else 1)
        elif analysis_type == "trend":
            options.sort(key=lambda item: 0 if item["type"] in {"line", "area"} else 1)

        return options[:4]

    @staticmethod
    def sample_evenly(data: list[dict[str, Any]], max_points: int) -> list[dict[str, Any]]:
        if len(data) <= max_points:
            return data

        step = max(1, len(data) // max_points)
        sampled = data[::step]
        if sampled[-1] != data[-1]:
            sampled.append(data[-1])

        return sampled[:max_points]

    def aggregate_categories(
        self,
        data: list[dict[str, Any]],
        x_key: str,
        y_key: str,
        max_points: int,
    ) -> list[dict[str, Any]]:
        buckets: dict[str, float] = {}
        for row in data:
            x_value = row.get(x_key)
            numeric_value = self._to_float(row.get(y_key))
            if x_value is None or numeric_value is None:
                continue
            label = str(x_value)
            buckets[label] = buckets.get(label, 0.0) + numeric_value

        ranked = sorted(buckets.items(), key=lambda pair: abs(pair[1]), reverse=True)
        if len(ranked) <= max_points:
            return [{x_key: key, y_key: value} for key, value in ranked]

        top = ranked[: max_points - 1]
        other_total = sum(value for _, value in ranked[max_points - 1 :])
        result = [{x_key: key, y_key: value} for key, value in top]
        result.append({x_key: "Other", y_key: other_total})
        return result

    def optimize_data_for_chart(
        self,
        data: list[dict[str, Any]],
        chart_config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not data:
            return data

        chart_type = chart_config.get("type")
        x_key = chart_config.get("xKey")
        y_key = chart_config.get("yKey")

        if not isinstance(x_key, str) or not isinstance(y_key, str):
            return self.sample_evenly(data, MAX_VIZ_POINTS)

        if chart_type == "scatter":
            return self.sample_evenly(data, MAX_SCATTER_POINTS)

        if chart_type in {"line", "area"}:
            return self.sample_evenly(data, MAX_VIZ_POINTS)

        if chart_type == "bar":
            return self.aggregate_categories(data, x_key, y_key, MAX_BAR_POINTS)

        if chart_type == "pie":
            return self.aggregate_categories(data, x_key, y_key, MAX_PIE_POINTS)

        return self.sample_evenly(data, MAX_VIZ_POINTS)
