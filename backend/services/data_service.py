import duckdb
import pandas as pd
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def validate_sql(sql: str) -> bool:
    """Ensure query is safe - only allow SELECT statements"""
    sql_upper = sql.upper().strip()

    # Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        return False

    # Blacklist dangerous keywords
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
                 'EXEC', 'EXECUTE', 'TRUNCATE', 'REPLACE']
    if any(keyword in sql_upper for keyword in dangerous):
        return False

    # Check for file operations
    if 'COPY' in sql_upper or 'INTO OUTFILE' in sql_upper:
        return False

    return True


def execute_safe_query(conn: duckdb.DuckDBPyConnection, sql: str, max_rows: int = 1000) -> pd.DataFrame:
    """Execute SQL query with safety limits"""
    if not validate_sql(sql):
        raise ValueError("Unsafe SQL query - only SELECT statements are allowed")

    # Add LIMIT if not present
    if 'LIMIT' not in sql.upper():
        sql = f"{sql} LIMIT {max_rows}"

    try:
        return conn.execute(sql).df()
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise ValueError(f"Query execution failed: {str(e)}")


class DataService:
    """Service for managing CSV uploads and DuckDB operations"""

    def __init__(self, session_ttl_minutes: int = 60):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_ttl = timedelta(minutes=session_ttl_minutes)

    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session['created_at'] > self.session_ttl
        ]
        for sid in expired:
            try:
                self.sessions[sid]['connection'].close()
            except:
                pass
            del self.sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def upload_csv(self, file_path: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload CSV and create DuckDB table

        Args:
            file_path: Path to CSV file
            session_id: Optional existing session ID, creates new if None

        Returns:
            Dict with session_id, schema, preview, and row_count
        """
        self._cleanup_expired_sessions()

        if session_id is None:
            session_id = str(uuid.uuid4())

        try:
            # Create in-memory DuckDB connection
            conn = duckdb.connect(':memory:')

            # Load CSV directly into DuckDB
            table_name = "uploaded_data"
            conn.execute(f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('{file_path}', header=true)
            """)

            # Get schema
            schema_df = conn.execute(f"DESCRIBE {table_name}").df()
            schema = schema_df.to_dict('records')

            # Get preview
            preview_df = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").df()
            preview = preview_df.to_dict('records')

            # Get row count
            row_count = conn.execute(f"SELECT COUNT(*) as count FROM {table_name}").fetchone()[0]

            # Store session
            self.sessions[session_id] = {
                "connection": conn,
                "table_name": table_name,
                "schema": schema,
                "created_at": datetime.now()
            }

            logger.info(f"Created session {session_id} with {row_count} rows")

            return {
                "session_id": session_id,
                "schema": schema,
                "preview": preview,
                "row_count": row_count
            }

        except Exception as e:
            logger.error(f"Error uploading CSV: {e}")
            raise ValueError(f"Failed to process CSV file: {str(e)}")

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
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found or expired")

        conn = self.sessions[session_id]["connection"]
        return execute_safe_query(conn, sql, max_rows)

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session metadata"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found or expired")

        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "schema": session["schema"],
            "created_at": session["created_at"].isoformat()
        }

    def delete_session(self, session_id: str):
        """Manually delete a session"""
        if session_id in self.sessions:
            try:
                self.sessions[session_id]['connection'].close()
            except:
                pass
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id}")
