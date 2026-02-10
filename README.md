# Data Analyst

Chat-driven analytics for CSV/Excel datasets using FastAPI, DuckDB, Next.js, and OpenAI.

Upload a dataset, ask complex questions in plain English, and get:
- multi-probe SQL exploration
- trust-scored insights
- interactive charts
- optional action drafts (SQL view, dbt model, Jira ticket, Slack summary)

## What Is Implemented

- Streaming analysis pipeline (`/analyze/stream`) with progress events
- Multi-step exploration with up to 5 probes per question
- Probe artifact persistence in session DuckDB tables
- Compact randomized probe samples fed back into synthesis (context-safe)
- Primary-probe quality guard to avoid weak single-row summaries dominating results
- Safe SQL execution (read-only SELECT/CTE only)

## Architecture

### Backend (`/backend`)

- `main.py`
  - FastAPI routes
  - chat + analysis streaming
  - in-memory conversation/session state
- `services/data_service.py`
  - upload + schema/profile generation
  - SQL validation/execution
  - probe artifact persistence/retrieval
- `services/ai_service.py`
  - LLM prompting + strict JSON normalization
  - exploration planning + synthesis
- `services/analysis_runtime.py`
  - orchestration for probe execution, chart prep, trust layer, synthesis
- `services/runtime/*`
  - charting, trust scoring, causal lab, action runtime

### Frontend (`/frontend`)

- `app/dashboard/page.tsx`
  - upload + preview + analysis UI
- `components/DataChatInterface.tsx`
  - streaming analyze UX, follow-ups, action workflows
- `components/data-chat/*`
  - assistant message rendering, trust/exploration/action panels
- `lib/analyze-stream.ts`
  - SSE frame parsing + progress formatting helpers
- `app/api/*`
  - Next.js proxy routes to backend

## Quick Start

### 1) Backend

```bash
cd backend
uv sync
echo "OPENAI_API_KEY=your_key_here" > .env
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Health check:
```bash
curl http://127.0.0.1:8000/health
```

### 2) Frontend

```bash
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open:
- [http://127.0.0.1:3000/dashboard](http://127.0.0.1:3000/dashboard)

## API Overview

### Core Analysis Routes (Backend)

- `POST /upload`
  - upload CSV/Excel; returns `session_id`, schema, preview, profile
- `POST /analyze`
  - non-streaming analysis response
- `POST /analyze/stream`
  - SSE stream with progress + final result
- `POST /analysis/sprint`
  - run multiple questions in sequence
- `POST /hypotheses`
  - generate candidate exploration questions
- `POST /causal-lab`
  - heuristic causal-driver style exploration

### SSE Event Contract (`/analyze/stream`)

`type: "progress"` events:
- `phase: "plan_ready"` + `probe_count` + `analysis_goal`
- `phase: "probe_started"` + `probe_id` + `question`
- `phase: "probe_completed"` + `probe_id` + `row_count`
- `phase: "synthesis_completed"` + `primary_probe_id`

`type: "result"` event:
- `conversation_id`
- `payload` (same shape as `/analyze` result)

`type: "error"` event:
- `detail`
- `status`

## Configuration

### Backend

- `OPENAI_API_KEY` (required)

### Frontend

- `BACKEND_URL` (optional, defaults to `http://localhost:8000`)

## Development Commands

### Backend

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

### Frontend

```bash
cd frontend
npm run lint
```

## Notes on Model Usage

- The backend uses `chat.completions` with `gpt-5`.
- `temperature` is intentionally omitted for compatibility with newer model constraints.

## Cleanup Performed

- Removed unused legacy scaffold:
  - old `backend/api/*` package
  - unused debug script `backend/test_responses.py`
  - unused frontend component `frontend/components/ChatInterface.tsx`
- Refactored backend analysis conversation handling into shared helper functions.
- Extracted frontend stream parsing/formatting into `frontend/lib/analyze-stream.ts`.

## License

MIT
