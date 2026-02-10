## Backend

FastAPI service for CSV/Excel upload, profiling, and AI-driven analytics.

### Key behavior

- Uploads CSV/Excel files into DuckDB in-memory sessions.
- Builds dataset profile metadata (column types, candidate correlations, starter questions).
- Runs strict read-only SQL validation before query execution.
- Uses OpenAI for SQL + insight generation.
- Returns explicit errors if LLM output is invalid (no heuristic fallback).

### Run

```bash
uv sync
uv run uvicorn main:app --reload --port 8000
```

### Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```
