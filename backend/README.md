# Backend

FastAPI service for:
- file upload + profiling
- SQL-safe query execution on DuckDB sessions
- multi-probe AI analysis and synthesis
- streaming analysis events over SSE

## Run

```bash
uv sync
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Test

```bash
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

## Key Routes

- `POST /upload`
- `POST /analyze`
- `POST /analyze/stream`
- `POST /analysis/sprint`
- `POST /hypotheses`
- `POST /causal-lab`
- `POST /ml/regression`
- `POST /ml/anomalies`

See the project root `README.md` for full API details and streaming event contracts.
