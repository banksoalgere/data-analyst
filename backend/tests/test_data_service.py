import os
import tempfile
import unittest

import duckdb

from services.data_service import DataService, execute_safe_query, validate_sql


class SQLValidationTests(unittest.TestCase):
    def test_validate_sql_accepts_select(self):
        self.assertTrue(validate_sql("SELECT 1 AS value"))
        self.assertTrue(validate_sql("WITH x AS (SELECT 1) SELECT * FROM x"))

    def test_validate_sql_rejects_dangerous_or_invalid(self):
        self.assertFalse(validate_sql("DROP TABLE uploaded_data"))
        self.assertFalse(validate_sql("SELECT 1; SELECT 2"))
        self.assertFalse(validate_sql("SELECT 1 -- comment"))
        self.assertFalse(validate_sql("SELECT * FROM read_csv('foo.csv')"))

    def test_execute_safe_query_applies_row_limit(self):
        conn = duckdb.connect(":memory:")
        conn.execute("CREATE TABLE numbers AS SELECT * FROM range(0, 100)")
        result = execute_safe_query(conn, "SELECT * FROM numbers", max_rows=5)
        self.assertEqual(len(result), 5)
        conn.close()


class DataServiceUploadTests(unittest.TestCase):
    def test_upload_csv_builds_profile_and_session_metadata(self):
        csv_content = (
            "date,revenue,cost,region\n"
            "2025-01-01,100,60,US\n"
            "2025-02-01,200,100,US\n"
            "2025-03-01,300,130,EU\n"
            "2025-04-01,400,180,EU\n"
        )
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as handle:
            handle.write(csv_content)
            tmp_path = handle.name

        service = DataService()
        try:
            uploaded = service.upload_csv(tmp_path)
            self.assertIn("session_id", uploaded)
            self.assertEqual(uploaded["row_count"], 4)
            self.assertIn("profile", uploaded)
            self.assertIn("revenue", uploaded["profile"]["numeric_columns"])
            self.assertIn("date", uploaded["profile"]["temporal_columns"])
            self.assertGreaterEqual(len(uploaded["profile"]["recommended_questions"]), 1)

            session = service.get_session_info(uploaded["session_id"])
            self.assertEqual(session["row_count"], 4)
            self.assertEqual(session["table_name"], "uploaded_data")
            self.assertIn("profile", session)
        finally:
            os.unlink(tmp_path)
            if "session_id" in locals().get("uploaded", {}):
                service.delete_session(uploaded["session_id"])

    def test_upload_file_rejects_unsupported_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as handle:
            handle.write("not tabular")
            tmp_path = handle.name

        service = DataService()
        try:
            with self.assertRaises(ValueError):
                service.upload_file(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_persist_and_load_analysis_artifacts(self):
        csv_content = (
            "date,revenue,region\n"
            "2025-01-01,100,US\n"
            "2025-02-01,200,US\n"
            "2025-03-01,300,EU\n"
        )
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as handle:
            handle.write(csv_content)
            tmp_path = handle.name

        service = DataService()
        try:
            uploaded = service.upload_file(tmp_path)
            session_id = uploaded["session_id"]
            run_id = "test_run_1"

            service.persist_analysis_artifacts(
                session_id=session_id,
                run_id=run_id,
                question="overview",
                analysis_goal="find key patterns",
                artifacts=[
                    {
                        "probe_id": "probe_1",
                        "question": "overview metrics",
                        "analysis_type": "overview",
                        "rationale": "baseline snapshot",
                        "sql": "SELECT SUM(revenue) AS total_revenue FROM uploaded_data",
                        "row_count": 1,
                        "chart_config": {"type": "bar", "xKey": "metric", "yKey": "value"},
                        "graph_data": [{"metric": "total_revenue", "value": 600}],
                        "llm_sample": {
                            "columns": ["total_revenue"],
                            "sample_rows": [{"total_revenue": 600}],
                            "chart_sample": [{"metric": "total_revenue", "value": 600}],
                        },
                        "stats": {"column_count": 1},
                    },
                    {
                        "probe_id": "probe_2",
                        "question": "revenue by region",
                        "analysis_type": "comparison",
                        "rationale": "segment differences",
                        "sql": "SELECT region, SUM(revenue) AS revenue FROM uploaded_data GROUP BY region",
                        "row_count": 2,
                        "chart_config": {"type": "bar", "xKey": "region", "yKey": "revenue"},
                        "graph_data": [{"region": "US", "revenue": 300}, {"region": "EU", "revenue": 300}],
                        "llm_sample": {
                            "columns": ["region", "revenue"],
                            "sample_rows": [{"region": "US", "revenue": 300}],
                            "chart_sample": [{"region": "US", "revenue": 300}],
                        },
                        "stats": {"column_count": 2},
                    },
                ],
            )

            summaries = service.load_analysis_artifact_summaries(session_id=session_id, run_id=run_id)
            self.assertEqual(len(summaries), 2)
            by_probe = {item["probe_id"]: item for item in summaries}
            self.assertIn("probe_1", by_probe)
            self.assertIn("probe_2", by_probe)
            self.assertEqual(by_probe["probe_1"]["chart_hint"]["type"], "bar")
            self.assertEqual(by_probe["probe_2"]["columns"], ["region", "revenue"])
            self.assertTrue(by_probe["probe_1"]["sample_rows"])
        finally:
            os.unlink(tmp_path)
            if "uploaded" in locals() and "session_id" in uploaded:
                service.delete_session(uploaded["session_id"])


if __name__ == "__main__":
    unittest.main()
