import unittest

from services.analysis_runtime import AnalysisRuntime


class _DummyAIAnalyst:
    pass


class _DummyDataService:
    pass


class AnalysisRuntimePrimaryProbeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = AnalysisRuntime(ai_analyst=_DummyAIAnalyst(), data_service=_DummyDataService())

    def test_select_primary_probe_prefers_richer_evidence_over_sparse_probe(self):
        probes = [
            {
                "probe_id": "probe_1",
                "row_count": 1,
                "chart_data": [{"metric": "total", "value": 100}],
                "chart_options": [{"type": "bar", "xKey": "metric", "yKey": "value"}],
            },
            {
                "probe_id": "probe_2",
                "row_count": 180,
                "chart_data": [{"date": f"2025-01-{day:02d}", "value": day} for day in range(1, 40)],
                "chart_options": [{"type": "line", "xKey": "date", "yKey": "value"}],
            },
        ]

        selected = self.runtime._select_primary_probe("probe_1", probes)
        self.assertEqual(selected["probe_id"], "probe_2")

    def test_select_primary_probe_keeps_requested_when_evidence_is_strong(self):
        probes = [
            {
                "probe_id": "probe_1",
                "row_count": 130,
                "chart_data": [{"region": f"R{idx}", "value": idx} for idx in range(30)],
                "chart_options": [{"type": "bar", "xKey": "region", "yKey": "value"}],
            },
            {
                "probe_id": "probe_2",
                "row_count": 90,
                "chart_data": [{"region": f"R{idx}", "value": idx} for idx in range(20)],
                "chart_options": [{"type": "bar", "xKey": "region", "yKey": "value"}],
            },
        ]

        selected = self.runtime._select_primary_probe("probe_1", probes)
        self.assertEqual(selected["probe_id"], "probe_1")


if __name__ == "__main__":
    unittest.main()
