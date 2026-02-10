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


if __name__ == "__main__":
    unittest.main()
