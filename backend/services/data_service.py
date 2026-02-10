from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from itertools import combinations
from typing import Any, Dict, Optional

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b("
    r"ATTACH|CALL|COMMENT|COPY|CREATE|DELETE|DETACH|DROP|EXEC|EXECUTE|"
    r"EXPORT|IMPORT|INSERT|INSTALL|LOAD|MERGE|PRAGMA|REPLACE|TRUNCATE|"
    r"UPDATE|VACUUM"
    r")\b",
    re.IGNORECASE,
)
FORBIDDEN_IO_PATTERN = re.compile(
    r"\b(read_csv|read_json|read_parquet|glob|httpfs)\b",
    re.IGNORECASE,
)
COMMENT_PATTERN = re.compile(r"(--|/\*)")
NUMERIC_TYPES = {
    "TINYINT",
    "SMALLINT",
    "INTEGER",
    "BIGINT",
    "HUGEINT",
    "UTINYINT",
    "USMALLINT",
    "UINTEGER",
    "UBIGINT",
    "UHUGEINT",
    "FLOAT",
    "DOUBLE",
    "DECIMAL",
    "REAL",
}
TEMPORAL_TYPE_KEYWORDS = {"DATE", "TIME", "TIMESTAMP"}
TEXT_TYPES = {"VARCHAR", "TEXT", "CHAR", "STRING", "UUID"}
SUPPORTED_EXCEL_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".xltx", ".xltm", ".xlsb"}
SUPPORTED_TABULAR_EXTENSIONS = {".csv", *SUPPORTED_EXCEL_EXTENSIONS}


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def normalize_sql(sql: str) -> str:
    query = sql.strip()
    if query.endswith(";"):
        query = query[:-1].strip()
    return query


def validate_sql(sql: str) -> bool:
    """Ensure query is read-only and single-statement."""
    query = normalize_sql(sql)
    query_upper = query.upper()

    if not query:
        return False

    if ";" in query:
        return False

    if COMMENT_PATTERN.search(query):
        return False

    if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        return False

    if FORBIDDEN_SQL_PATTERN.search(query_upper):
        return False

    if FORBIDDEN_IO_PATTERN.search(query_upper):
        return False

    return True


def _prepare_safe_query(sql: str, max_rows: int) -> str:
    query = normalize_sql(sql)
    return f"SELECT * FROM ({query}) AS safe_query LIMIT {int(max_rows)}"


def execute_safe_query(conn: duckdb.DuckDBPyConnection, sql: str, max_rows: int = 1000) -> pd.DataFrame:
    """Execute SQL query with safety limits."""
    if not validate_sql(sql):
        raise ValueError("Unsafe SQL query. Only single SELECT/CTE statements are allowed.")

    try:
        safe_query = _prepare_safe_query(sql, max_rows=max_rows)
        return conn.execute(safe_query).df()
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise ValueError(f"Query execution failed: {str(e)}")


class DataService:
    """Service for managing CSV uploads, profiling, and DuckDB sessions."""

    def __init__(self, session_ttl_minutes: int = 60, max_sessions: int = 100):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_ttl = timedelta(minutes=session_ttl_minutes)
        self.max_sessions = max_sessions

    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_accessed_at"] > self.session_ttl
        ]
        for sid in expired:
            try:
                self.sessions[sid]["connection"].close()
            except Exception:
                pass
            del self.sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def _enforce_session_cap(self):
        if len(self.sessions) < self.max_sessions:
            return

        oldest_id = min(
            self.sessions.keys(),
            key=lambda sid: self.sessions[sid]["last_accessed_at"],
        )
        self.delete_session(oldest_id)
        logger.info("Deleted least-recently used session to enforce max_sessions cap")

    def _is_numeric(self, column_type: str) -> bool:
        normalized = (column_type or "").upper()
        return any(normalized.startswith(dtype) for dtype in NUMERIC_TYPES)

    def _is_temporal(self, column_type: str) -> bool:
        normalized = (column_type or "").upper()
        return any(keyword in normalized for keyword in TEMPORAL_TYPE_KEYWORDS)

    def _is_textual(self, column_type: str) -> bool:
        normalized = (column_type or "").upper()
        return any(token in normalized for token in TEXT_TYPES)

    def _build_profile(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        schema: list[dict[str, Any]],
        row_count: int,
    ) -> dict[str, Any]:
        numeric_columns = [col["column_name"] for col in schema if self._is_numeric(col["column_type"])]
        temporal_columns = [col["column_name"] for col in schema if self._is_temporal(col["column_type"])]
        categorical_columns = [
            col["column_name"] for col in schema
            if self._is_textual(col["column_type"]) or (
                not self._is_numeric(col["column_type"]) and not self._is_temporal(col["column_type"])
            )
        ]

        top_correlations: list[dict[str, Any]] = []
        limited_numeric = numeric_columns[:6]
        if len(limited_numeric) >= 2:
            for left_col, right_col in combinations(limited_numeric, 2):
                left_quoted = quote_identifier(left_col)
                right_quoted = quote_identifier(right_col)
                sql = f"""
                    SELECT corr(TRY_CAST({left_quoted} AS DOUBLE), TRY_CAST({right_quoted} AS DOUBLE)) AS corr_value
                    FROM {quote_identifier(table_name)}
                """
                corr_value = conn.execute(sql).fetchone()[0]
                if corr_value is None:
                    continue
                strength = abs(float(corr_value))
                if strength < 0.3:
                    continue
                top_correlations.append(
                    {
                        "column_x": left_col,
                        "column_y": right_col,
                        "correlation": round(float(corr_value), 4),
                    }
                )

        top_correlations.sort(key=lambda item: abs(item["correlation"]), reverse=True)
        top_correlations = top_correlations[:5]

        recommended_questions = [
            "Give me an overview of this dataset and key metrics.",
        ]
        if temporal_columns and numeric_columns:
            recommended_questions.append(
                f"Show the trend of {numeric_columns[0]} over {temporal_columns[0]}."
            )
        if categorical_columns and numeric_columns:
            recommended_questions.append(
                f"Compare {numeric_columns[0]} by {categorical_columns[0]}."
            )
        if top_correlations:
            pair = top_correlations[0]
            recommended_questions.append(
                f"Explain the relationship between {pair['column_x']} and {pair['column_y']}."
            )
        elif len(numeric_columns) >= 2:
            recommended_questions.append(
                f"Find correlations between {numeric_columns[0]} and other numeric columns."
            )

        return {
            "row_count": row_count,
            "column_count": len(schema),
            "numeric_columns": numeric_columns,
            "temporal_columns": temporal_columns,
            "categorical_columns": categorical_columns,
            "top_correlations": top_correlations,
            "recommended_questions": recommended_questions[:6],
        }

    def _normalize_column_names(self, columns: list[Any]) -> list[str]:
        normalized: list[str] = []
        seen: dict[str, int] = {}

        for index, raw_name in enumerate(columns):
            base = str(raw_name).strip() if raw_name is not None else ""
            if not base:
                base = f"column_{index + 1}"
            count = seen.get(base, 0)
            seen[base] = count + 1
            normalized.append(base if count == 0 else f"{base}_{count + 1}")

        return normalized

    def _load_tabular_file(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        file_path: str,
    ) -> None:
        extension = os.path.splitext(file_path)[1].lower()
        table_identifier = quote_identifier(table_name)

        if extension == ".csv":
            escaped_path = file_path.replace("'", "''")
            conn.execute(f"""
                CREATE TABLE {table_identifier} AS
                SELECT * FROM read_csv_auto('{escaped_path}', header=true, sample_size=-1)
            """)
            return

        if extension in SUPPORTED_EXCEL_EXTENSIONS:
            try:
                dataframe = pd.read_excel(file_path, sheet_name=0)
            except Exception as exc:
                raise ValueError(f"Failed to read Excel file: {exc}") from exc

            if dataframe is None:
                raise ValueError("Failed to read the first worksheet from Excel file.")

            dataframe = dataframe.dropna(how="all")
            dataframe.columns = self._normalize_column_names(list(dataframe.columns))

            conn.register("uploaded_frame", dataframe)
            conn.execute(
                f"CREATE TABLE {table_identifier} AS SELECT * FROM uploaded_frame"
            )
            conn.unregister("uploaded_frame")
            return

        raise ValueError(
            f"Unsupported file type '{extension}'. Supported types: {', '.join(sorted(SUPPORTED_TABULAR_EXTENSIONS))}"
        )

    def _ensure_analysis_tables(self, conn: duckdb.DuckDBPyConnection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                run_id VARCHAR PRIMARY KEY,
                question VARCHAR,
                analysis_goal VARCHAR,
                probe_count INTEGER,
                created_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_probe_artifacts (
                artifact_id VARCHAR PRIMARY KEY,
                run_id VARCHAR,
                probe_id VARCHAR,
                question VARCHAR,
                analysis_type VARCHAR,
                rationale VARCHAR,
                sql TEXT,
                row_count INTEGER,
                chart_type VARCHAR,
                x_key VARCHAR,
                y_key VARCHAR,
                graph_data_json TEXT,
                llm_sample_json TEXT,
                stats_json TEXT,
                created_at TIMESTAMP
            )
            """
        )

    @staticmethod
    def _safe_json_loads(raw: Any, fallback: Any) -> Any:
        if not isinstance(raw, str) or not raw:
            return fallback
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return fallback

    def _get_session_connection(self, session_id: str) -> duckdb.DuckDBPyConnection:
        self._cleanup_expired_sessions()
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found or expired")
        self.sessions[session_id]["last_accessed_at"] = datetime.now()
        return self.sessions[session_id]["connection"]

    def upload_file(self, file_path: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload CSV/Excel and create DuckDB table.

        Args:
            file_path: Path to CSV file
            session_id: Optional existing session ID, creates new if None

        Returns:
            Dict with session_id, schema, preview, and row_count.
        """
        self._cleanup_expired_sessions()
        self._enforce_session_cap()

        if session_id is None:
            session_id = str(uuid.uuid4())

        try:
            conn = duckdb.connect(":memory:")
            conn.execute("SET threads TO 2")
            conn.execute("SET memory_limit = '1GB'")

            table_name = "uploaded_data"
            self._load_tabular_file(conn, table_name, file_path)
            self._ensure_analysis_tables(conn)

            schema_df = conn.execute(f"DESCRIBE {quote_identifier(table_name)}").df()
            schema = schema_df.to_dict("records")

            preview_df = conn.execute(f"SELECT * FROM {quote_identifier(table_name)} LIMIT 10").df()
            preview = preview_df.to_dict("records")

            row_count = conn.execute(
                f"SELECT COUNT(*) as count FROM {quote_identifier(table_name)}"
            ).fetchone()[0]
            if row_count == 0:
                raise ValueError("Uploaded CSV has no rows.")

            profile = self._build_profile(conn, table_name, schema, row_count)
            now = datetime.now()

            self.sessions[session_id] = {
                "connection": conn,
                "table_name": table_name,
                "schema": schema,
                "profile": profile,
                "row_count": row_count,
                "created_at": now,
                "last_accessed_at": now,
            }

            logger.info(f"Created session {session_id} with {row_count} rows")

            return {
                "session_id": session_id,
                "schema": schema,
                "preview": preview,
                "row_count": row_count,
                "profile": profile,
            }

        except Exception as e:
            logger.error(f"Error uploading CSV: {e}")
            raise ValueError(f"Failed to process CSV file: {str(e)}")

    def upload_csv(self, file_path: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Backward-compatible wrapper for legacy callers.
        """
        return self.upload_file(file_path=file_path, session_id=session_id)

    def execute_query(self, session_id: str, sql: str, max_rows: int = 1000) -> pd.DataFrame:
        """
        Execute SQL query for a session

        Args:
            session_id: Session identifier
            sql: SQL query to execute
            max_rows: Maximum rows to return

        Returns:
            DataFrame with query results
        """
        conn = self._get_session_connection(session_id)
        return execute_safe_query(conn, sql, max_rows)

    def persist_analysis_artifacts(
        self,
        session_id: str,
        run_id: str,
        question: str,
        analysis_goal: str,
        artifacts: list[dict[str, Any]],
    ) -> None:
        if not run_id.strip():
            raise ValueError("run_id is required for analysis artifacts.")
        if not artifacts:
            return

        conn = self._get_session_connection(session_id)
        self._ensure_analysis_tables(conn)
        created_at = datetime.now()

        conn.execute("DELETE FROM analysis_probe_artifacts WHERE run_id = ?", [run_id])
        conn.execute("DELETE FROM analysis_runs WHERE run_id = ?", [run_id])
        conn.execute(
            """
            INSERT INTO analysis_runs (run_id, question, analysis_goal, probe_count, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [run_id, question.strip(), analysis_goal.strip(), len(artifacts), created_at],
        )

        insert_sql = """
            INSERT INTO analysis_probe_artifacts (
                artifact_id,
                run_id,
                probe_id,
                question,
                analysis_type,
                rationale,
                sql,
                row_count,
                chart_type,
                x_key,
                y_key,
                graph_data_json,
                llm_sample_json,
                stats_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for artifact in artifacts:
            probe_id = str(artifact.get("probe_id", "")).strip()
            if not probe_id:
                continue
            chart_config = artifact.get("chart_config")
            chart_type = chart_config.get("type") if isinstance(chart_config, dict) else None
            x_key = chart_config.get("xKey") if isinstance(chart_config, dict) else None
            y_key = chart_config.get("yKey") if isinstance(chart_config, dict) else None

            conn.execute(
                insert_sql,
                [
                    str(uuid.uuid4()),
                    run_id,
                    probe_id,
                    str(artifact.get("question", "")).strip(),
                    str(artifact.get("analysis_type", "")).strip(),
                    str(artifact.get("rationale", "")).strip(),
                    str(artifact.get("sql", "")).strip(),
                    int(artifact.get("row_count") or 0),
                    chart_type,
                    x_key,
                    y_key,
                    json.dumps(artifact.get("graph_data", []), default=str),
                    json.dumps(artifact.get("llm_sample", {}), default=str),
                    json.dumps(artifact.get("stats", {}), default=str),
                    created_at,
                ],
            )

    def load_analysis_artifact_summaries(self, session_id: str, run_id: str) -> list[dict[str, Any]]:
        if not run_id.strip():
            return []

        conn = self._get_session_connection(session_id)
        self._ensure_analysis_tables(conn)
        records = conn.execute(
            """
            SELECT
                probe_id,
                question,
                analysis_type,
                rationale,
                sql,
                row_count,
                chart_type,
                x_key,
                y_key,
                llm_sample_json,
                stats_json
            FROM analysis_probe_artifacts
            WHERE run_id = ?
            ORDER BY probe_id ASC
            """,
            [run_id],
        ).fetchall()

        summaries: list[dict[str, Any]] = []
        for (
            probe_id,
            question,
            analysis_type,
            rationale,
            sql,
            row_count,
            chart_type,
            x_key,
            y_key,
            llm_sample_json,
            stats_json,
        ) in records:
            llm_sample = self._safe_json_loads(llm_sample_json, {})
            stats = self._safe_json_loads(stats_json, {})

            summary = {
                "probe_id": probe_id,
                "question": question,
                "analysis_type": analysis_type,
                "rationale": rationale,
                "sql": sql,
                "row_count": int(row_count or 0),
                "chart_hint": {
                    "type": chart_type or "bar",
                    "xKey": x_key or "",
                    "yKey": y_key or "",
                },
                "stats": stats if isinstance(stats, dict) else {},
            }

            if isinstance(llm_sample, dict):
                columns = llm_sample.get("columns", [])
                sample_rows = llm_sample.get("sample_rows", [])
                chart_sample = llm_sample.get("chart_sample", [])
                summary["columns"] = columns if isinstance(columns, list) else []
                summary["sample_rows"] = sample_rows if isinstance(sample_rows, list) else []
                summary["chart_sample"] = chart_sample if isinstance(chart_sample, list) else []
            else:
                summary["columns"] = []
                summary["sample_rows"] = []
                summary["chart_sample"] = []
            summaries.append(summary)

        return summaries

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session metadata."""
        self._cleanup_expired_sessions()
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found or expired")

        session = self.sessions[session_id]
        session["last_accessed_at"] = datetime.now()
        return {
            "session_id": session_id,
            "table_name": session["table_name"],
            "schema": session["schema"],
            "profile": session["profile"],
            "row_count": session["row_count"],
            "created_at": session["created_at"].isoformat(),
            "last_accessed_at": session["last_accessed_at"].isoformat(),
        }

    def delete_session(self, session_id: str):
        """Manually delete a session."""
        if session_id in self.sessions:
            try:
                self.sessions[session_id]["connection"].close()
            except Exception:
                pass
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id}")
