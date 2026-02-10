# Data Analyst

Turn raw spreadsheets into decision-ready analysis in minutes.

**Data Analyst** is a chat-first analytics app for CSV/Excel data. Upload a file, ask business questions in plain English, and get streaming answers backed by executable SQL, interactive charts, confidence scoring, and action drafts your team can use immediately.

## Why This Project Is Useful

- Faster time-to-insight: from upload to meaningful analysis without writing SQL by hand.
- Explainable answers: every response is grounded in generated SQL and provenance metadata.
- Better than one-shot chat: runs multi-probe exploration before synthesizing conclusions.
- Built for execution: drafts downstream artifacts (SQL view, dbt model, Jira payload, Slack summary).
- Safe by default: query layer is restricted to read-only single `SELECT`/`CTE` statements.

## What You Get

- Spreadsheet upload with schema detection and profiling (`.csv`, `.xlsx`, `.xls`, `.xlsm`, `.xltx`, `.xltm`, `.xlsb`)
- Real-time analysis streaming with progress events over SSE
- Multi-step probe planning (up to 5 probes per question)
- Probe artifact persistence in DuckDB session tables
- Trust layer with confidence score, limitations, and provenance
- Follow-up question generation for iterative exploration
- Heuristic causal lab for likely drivers of a target metric
- Batch/sprint mode to run many hypotheses in one request

## Product Walkthrough (60 Seconds)

1. Upload a dataset in the dashboard.
2. Review auto-generated profile and suggested questions.
3. Ask a question in chat.
4. Watch plan/probe/synthesis progress stream in real time.
5. Inspect charts, SQL, trust signals, and follow-up prompts.
6. Draft an action artifact and approve it to produce a dry-run deliverable.

## Architecture

### Backend (`/backend`)

- `main.py`: FastAPI routes, upload lifecycle, analysis/chat streaming endpoints
- `services/data_service.py`: file ingestion, DuckDB session management, SQL safety validation
- `services/ai_service.py`: LLM prompting, exploration planning, synthesis, strict JSON normalization
- `services/analysis_runtime.py`: orchestration for probes, chart prep, trust scoring, and synthesis
- `services/runtime/*`: charting, trust runtime, causal runtime, action runtime

### Frontend (`/frontend`)

- `app/dashboard/page.tsx`: upload, summary, and chat workflow
- `components/CSVUploader.tsx`: drag-and-drop spreadsheet upload
- `components/DataChatInterface.tsx`: streaming chat UX and action workflow controls
- `components/data-chat/*`: assistant rendering, trust/exploration/action panels
- `app/api/*`: Next.js proxy routes that forward to backend services

## Quick Start

### Prerequisites

- Python `>=3.11`
- Node.js `>=18` (Next.js 16 app)
- [uv](https://docs.astral.sh/uv/) for Python dependency management
- OpenAI API key

### 1) Run Backend

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

### 2) Run Frontend

```bash
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open [http://127.0.0.1:3000/dashboard](http://127.0.0.1:3000/dashboard)

## API Highlights

### Core endpoints

- `POST /upload`: ingest spreadsheet, return `session_id`, schema, preview, profile
- `POST /analyze`: synchronous analysis result
- `POST /analyze/stream`: streaming analysis events + final result
- `POST /hypotheses`: generate candidate questions for exploration
- `POST /analysis/sprint`: run multiple questions in one pass
- `POST /causal-lab`: heuristic driver analysis for a target metric
- `POST /actions/draft`: create action artifacts from insights
- `POST /actions/approve`: execute action in dry-run mode and return artifact

### Stream event contract (`POST /analyze/stream`)

- Progress events (`type: "progress"`):
  - `phase: "plan_ready"` with `analysis_goal`, `probe_count`
  - `phase: "probe_started"` with `probe_id`, `question`
  - `phase: "probe_completed"` with `probe_id`, `row_count`
  - `phase: "synthesis_completed"` with `primary_probe_id`
- Final result event (`type: "result"`):
  - `conversation_id`
  - `payload` (analysis object matching `/analyze`)
- Error event (`type: "error"`):
  - `detail`
  - `status`

## Configuration

### Backend

- `OPENAI_API_KEY` (required)

### Frontend

- `BACKEND_URL` (optional, default: `http://localhost:8000`)

## Development

### Backend tests

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -p "test_*.py"
```

### Frontend lint

```bash
cd frontend
npm run lint
```

## Trust, Safety, and Scope

- SQL execution is intentionally restricted to read-only query patterns.
- Session data is scoped in in-memory-managed DuckDB session state.
- Causal lab output is heuristic and observational, not proof of causality.
- Action approvals currently return dry-run artifacts (no direct external side effects).

## Tech Stack

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS, Recharts
- **Backend:** FastAPI, DuckDB, Pandas, Pydantic
- **AI:** OpenAI `chat.completions` (`gpt-5`)

## License

MIT
