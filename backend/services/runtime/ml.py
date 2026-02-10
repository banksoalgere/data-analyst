from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class RegressionPreparedData:
    y: np.ndarray
    x: np.ndarray
    feature_names: list[str]
    cleaned_row_count: int
    requested_features: list[str]


class MLRuntime:
    @staticmethod
    def _is_temporal_series(series: pd.Series) -> bool:
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        if not pd.api.types.is_object_dtype(series):
            return False

        sample = series.dropna().astype(str).head(200)
        if sample.empty:
            return False
        parsed = pd.to_datetime(sample, errors="coerce", utc=True)
        return float(parsed.notna().mean()) >= 0.8

    @staticmethod
    def _select_default_feature_columns(
        data_frame: pd.DataFrame,
        target_column: str,
        max_features: int = 12,
    ) -> list[str]:
        numeric = [
            column
            for column in data_frame.columns
            if column != target_column and pd.api.types.is_numeric_dtype(data_frame[column])
        ]
        temporal = [
            column
            for column in data_frame.columns
            if column != target_column and column not in numeric and MLRuntime._is_temporal_series(data_frame[column])
        ]
        categorical = [
            column
            for column in data_frame.columns
            if column != target_column and column not in numeric and column not in temporal
        ]

        selected = numeric[:max_features]
        if len(selected) >= max_features:
            return selected

        for column in temporal:
            selected.append(column)
            if len(selected) >= max_features:
                return selected

        for column in categorical:
            unique_count = int(data_frame[column].nunique(dropna=True))
            if unique_count <= 20:
                selected.append(column)
                if len(selected) >= max_features:
                    return selected
        return selected

    def _prepare_regression_data(
        self,
        data_frame: pd.DataFrame,
        target_column: str,
        feature_columns: list[str] | None,
    ) -> RegressionPreparedData:
        if target_column not in data_frame.columns:
            raise ValueError(f"Target column '{target_column}' was not found in the dataset.")

        if feature_columns:
            requested_features = [column for column in feature_columns if column != target_column]
        else:
            requested_features = self._select_default_feature_columns(data_frame=data_frame, target_column=target_column)
        if not requested_features:
            raise ValueError("No usable feature columns found for regression.")

        missing = [column for column in requested_features if column not in data_frame.columns]
        if missing:
            raise ValueError(f"Feature columns not found: {', '.join(missing)}")

        work = data_frame[[target_column, *requested_features]].copy()

        for column in requested_features:
            if self._is_temporal_series(work[column]):
                parsed = pd.to_datetime(work[column], errors="coerce", utc=True)
                epoch_seconds = pd.Series(parsed.view("int64") / 1_000_000_000, index=parsed.index, dtype="float64")
                epoch_seconds[parsed.isna()] = np.nan
                work[column] = epoch_seconds

        target_numeric = pd.to_numeric(work[target_column], errors="coerce")
        features = pd.get_dummies(work[requested_features], drop_first=True, dtype=float)
        if features.empty:
            raise ValueError("Feature encoding produced no usable numeric columns.")
        for column in features.columns:
            features[column] = pd.to_numeric(features[column], errors="coerce")

        combined = pd.concat([target_numeric.rename(target_column), features], axis=1).dropna()
        if len(combined) < 25:
            raise ValueError("Not enough clean rows to run regression (need at least 25).")

        y = combined[target_column].to_numpy(dtype=float)
        x_frame = combined.drop(columns=[target_column])
        x = x_frame.to_numpy(dtype=float)
        if x.shape[1] < 1:
            raise ValueError("Regression requires at least one feature.")
        if len(combined) <= x.shape[1] + 5:
            raise ValueError("Not enough rows for stable regression given selected feature count.")

        return RegressionPreparedData(
            y=y,
            x=x,
            feature_names=list(x_frame.columns),
            cleaned_row_count=len(combined),
            requested_features=requested_features,
        )

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return 0.0
        if np.isnan(result) or np.isinf(result):
            return 0.0
        return float(round(result, 6))

    def build_regression_result(
        self,
        data_frame: pd.DataFrame,
        target_column: str,
        feature_columns: list[str] | None = None,
        test_fraction: float = 0.2,
    ) -> dict[str, Any]:
        prepared = self._prepare_regression_data(
            data_frame=data_frame,
            target_column=target_column,
            feature_columns=feature_columns,
        )

        n_rows = len(prepared.y)
        rng = np.random.default_rng(42)
        indices = np.arange(n_rows)
        rng.shuffle(indices)

        raw_test_size = max(1, int(round(n_rows * test_fraction)))
        max_test_size = max(1, n_rows - (prepared.x.shape[1] + 5))
        test_size = min(raw_test_size, max_test_size)
        train_idx = indices[test_size:]
        test_idx = indices[:test_size]
        if len(train_idx) <= prepared.x.shape[1]:
            raise ValueError("Not enough training rows for regression.")

        x_train = prepared.x[train_idx]
        y_train = prepared.y[train_idx]
        x_test = prepared.x[test_idx]
        y_test = prepared.y[test_idx]

        x_train_design = np.column_stack([np.ones(len(x_train)), x_train])
        coefficients = np.linalg.lstsq(x_train_design, y_train, rcond=None)[0]

        def predict(x_values: np.ndarray) -> np.ndarray:
            design = np.column_stack([np.ones(len(x_values)), x_values])
            return design @ coefficients

        predictions = predict(x_test)
        residuals = y_test - predictions
        rmse = float(np.sqrt(np.mean(np.square(residuals))))
        mae = float(np.mean(np.abs(residuals)))
        ss_res = float(np.sum(np.square(residuals)))
        ss_tot = float(np.sum(np.square(y_test - np.mean(y_test))))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

        coefficient_rows = [{"feature": "intercept", "coefficient": self._safe_float(coefficients[0])}]
        coefficient_rows.extend(
            {
                "feature": feature_name,
                "coefficient": self._safe_float(coeff),
            }
            for feature_name, coeff in zip(prepared.feature_names, coefficients[1:])
        )

        top_drivers = sorted(
            [row for row in coefficient_rows if row["feature"] != "intercept"],
            key=lambda item: abs(item["coefficient"]),
            reverse=True,
        )[:12]

        sample_count = min(25, len(y_test))
        sample_indices = np.arange(len(y_test))
        if len(sample_indices) > sample_count:
            sample_indices = np.sort(rng.choice(sample_indices, size=sample_count, replace=False))
        prediction_sample = [
            {
                "actual": self._safe_float(y_test[idx]),
                "predicted": self._safe_float(predictions[idx]),
                "residual": self._safe_float(y_test[idx] - predictions[idx]),
            }
            for idx in sample_indices
        ]

        return {
            "analysis_type": "linear_regression",
            "target_column": target_column,
            "feature_columns": prepared.requested_features,
            "encoded_feature_count": int(len(prepared.feature_names)),
            "rows_analyzed": int(prepared.cleaned_row_count),
            "rows_train": int(len(train_idx)),
            "rows_test": int(len(test_idx)),
            "metrics": {
                "r_squared": self._safe_float(r_squared),
                "rmse": self._safe_float(rmse),
                "mae": self._safe_float(mae),
            },
            "coefficients": coefficient_rows,
            "top_drivers": top_drivers,
            "prediction_sample": prediction_sample,
            "notes": [
                "Model is ordinary least squares linear regression.",
                "Categorical features are one-hot encoded (drop-first).",
                "Use this for directional insight; validate before production decisions.",
            ],
        }

    def detect_anomalies(
        self,
        data_frame: pd.DataFrame,
        metric_column: str,
        group_by: str | None = None,
        z_threshold: float = 3.0,
        max_results: int = 25,
    ) -> dict[str, Any]:
        if metric_column not in data_frame.columns:
            raise ValueError(f"Metric column '{metric_column}' was not found in the dataset.")
        if group_by and group_by not in data_frame.columns:
            raise ValueError(f"Group-by column '{group_by}' was not found in the dataset.")

        work = data_frame.copy().reset_index(drop=False).rename(columns={"index": "source_row_index"})
        work[metric_column] = pd.to_numeric(work[metric_column], errors="coerce")
        work = work.dropna(subset=[metric_column])
        if len(work) < 30:
            raise ValueError("Not enough numeric rows to detect anomalies (need at least 30).")

        if group_by:
            grouped = work.groupby(group_by)[metric_column]
            baseline_mean = grouped.transform("mean")
            baseline_std = grouped.transform("std").replace(0, np.nan)
        else:
            baseline_mean = pd.Series(work[metric_column].mean(), index=work.index)
            std_value = float(work[metric_column].std())
            if std_value <= 1e-12:
                raise ValueError("Metric has near-zero variance; anomaly detection is not meaningful.")
            baseline_std = pd.Series(std_value, index=work.index)

        work["baseline_mean"] = baseline_mean
        work["baseline_std"] = baseline_std
        work["z_score"] = (work[metric_column] - work["baseline_mean"]) / work["baseline_std"]
        work = work.replace([np.inf, -np.inf], np.nan).dropna(subset=["z_score"])
        work["abs_z_score"] = work["z_score"].abs()

        anomalies_all = work[work["abs_z_score"] >= z_threshold].sort_values("abs_z_score", ascending=False)
        anomalies = anomalies_all.head(max_results)

        context_columns = [metric_column]
        if group_by:
            context_columns.insert(0, group_by)

        anomaly_rows = []
        for _, row in anomalies.iterrows():
            anomaly_rows.append(
                {
                    "source_row_index": int(row["source_row_index"]),
                    "metric_value": self._safe_float(row[metric_column]),
                    "z_score": self._safe_float(row["z_score"]),
                    "abs_z_score": self._safe_float(row["abs_z_score"]),
                    "baseline_mean": self._safe_float(row["baseline_mean"]),
                    "baseline_std": self._safe_float(row["baseline_std"]),
                    "group_value": str(row[group_by]) if group_by else None,
                    "context": {
                        column: (None if pd.isna(row[column]) else str(row[column]))
                        for column in context_columns
                    },
                }
            )

        metric_mean = float(work[metric_column].mean())
        metric_std = float(work[metric_column].std())
        metric_median = float(work[metric_column].median())

        return {
            "analysis_type": "anomaly_detection",
            "metric_column": metric_column,
            "group_by": group_by,
            "z_threshold": float(z_threshold),
            "rows_analyzed": int(len(work)),
            "anomaly_count": int(len(anomalies_all)),
            "returned_count": int(len(anomaly_rows)),
            "distribution": {
                "mean": self._safe_float(metric_mean),
                "std_dev": self._safe_float(metric_std),
                "median": self._safe_float(metric_median),
            },
            "anomalies": anomaly_rows,
            "notes": [
                "Anomalies are identified using z-score thresholding.",
                "Group baseline is used when group_by is provided.",
                "Review domain context before taking action on outliers.",
            ],
        }
