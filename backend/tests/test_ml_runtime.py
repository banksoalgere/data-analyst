import unittest

import numpy as np
import pandas as pd

from services.runtime.ml import MLRuntime


class MLRuntimeRegressionTests(unittest.TestCase):
    def setUp(self):
        self.runtime = MLRuntime()

    def test_build_regression_result_returns_strong_metrics(self):
        rng = np.random.default_rng(7)
        rows = 450
        x1 = rng.normal(loc=20.0, scale=4.0, size=rows)
        x2 = rng.uniform(low=0.0, high=10.0, size=rows)
        segment = rng.choice(["A", "B"], size=rows, p=[0.6, 0.4])

        noise = rng.normal(loc=0.0, scale=0.5, size=rows)
        target = (3.2 * x1) - (1.1 * x2) + (segment == "B").astype(float) * 4.5 + noise

        frame = pd.DataFrame(
            {
                "x1": x1,
                "x2": x2,
                "segment": segment,
                "target": target,
            }
        )

        result = self.runtime.build_regression_result(
            data_frame=frame,
            target_column="target",
            feature_columns=["x1", "x2", "segment"],
            test_fraction=0.2,
        )

        self.assertEqual(result["analysis_type"], "linear_regression")
        self.assertEqual(result["target_column"], "target")
        self.assertGreater(result["rows_analyzed"], 350)
        self.assertGreater(result["encoded_feature_count"], 2)
        self.assertGreater(result["metrics"]["r_squared"], 0.95)
        self.assertLess(result["metrics"]["rmse"], 2.0)
        self.assertTrue(len(result["top_drivers"]) >= 2)

    def test_build_regression_result_rejects_too_few_rows(self):
        frame = pd.DataFrame(
            {
                "feature_a": [1, 2, 3, 4, 5, 6],
                "feature_b": [6, 5, 4, 3, 2, 1],
                "target": [2, 4, 6, 8, 10, 12],
            }
        )

        with self.assertRaises(ValueError):
            self.runtime.build_regression_result(
                data_frame=frame,
                target_column="target",
                feature_columns=["feature_a", "feature_b"],
            )


class MLRuntimeAnomalyTests(unittest.TestCase):
    def setUp(self):
        self.runtime = MLRuntime()

    def test_detect_anomalies_with_group_baseline(self):
        rng = np.random.default_rng(11)
        group_a = rng.normal(loc=50.0, scale=2.0, size=180)
        group_b = rng.normal(loc=100.0, scale=3.0, size=180)
        values = np.concatenate([group_a, group_b, np.array([180.0])])
        groups = np.array(["A"] * 180 + ["B"] * 180 + ["A"])

        frame = pd.DataFrame({"coin": groups, "funding": values})
        result = self.runtime.detect_anomalies(
            data_frame=frame,
            metric_column="funding",
            group_by="coin",
            z_threshold=3.0,
            max_results=10,
        )

        self.assertEqual(result["analysis_type"], "anomaly_detection")
        self.assertGreater(result["rows_analyzed"], 300)
        self.assertGreaterEqual(result["anomaly_count"], 1)
        self.assertTrue(
            any(
                item.get("group_value") == "A" and float(item.get("metric_value", 0)) > 150
                for item in result["anomalies"]
            )
        )

    def test_detect_anomalies_rejects_near_zero_variance(self):
        frame = pd.DataFrame({"metric": [5.0] * 60})
        with self.assertRaises(ValueError):
            self.runtime.detect_anomalies(
                data_frame=frame,
                metric_column="metric",
                z_threshold=2.5,
            )


if __name__ == "__main__":
    unittest.main()
