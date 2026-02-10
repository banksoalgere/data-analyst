# Spreadsheet Data Analytics with AI

An intelligent data analytics platform that allows you to upload CSV/Excel files and ask questions in natural language. The AI automatically generates SQL queries, executes them, and creates visualizations.

## Architecture

### Backend (FastAPI + DuckDB + OpenAI)
- **Spreadsheet Upload**: Supports CSV and Excel formats in DuckDB sessions
- **AI SQL Generation**: Uses OpenAI to convert natural language to SQL
- **Strict LLM Contract**: Fails fast if the model response is invalid or unavailable (no heuristic fallback)
- **Safe Execution**: Validates read-only SQL and enforces row limits
- **Chart Config**: AI determines the best visualization type
- **Dataset Profiling**: Detects numeric/time/categorical fields and top correlations at upload time

### Frontend (Next.js + React + Recharts)
- **File Upload**: Drag-and-drop CSV/Excel interface
- **Data Preview**: Shows schema and sample data
- **Chat Interface**: Natural language query input
- **Dynamic Charts**: Renders line, bar, scatter, pie, and area charts
- **Privacy & Terms**: Dedicated pages for legal compliance
- **Premium Dark UI**: Refined aesthetic with custom scrollbars and glassmorphism

## Setup

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies with uv:
```bash
uv sync
```

3. Create `.env` file:
```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

4. Run the server:
```bash
uv run uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. **Upload File**: Go to `/dashboard` and drag-drop a CSV or Excel file
2. **View Preview**: See the data schema and first 5 rows
3. **Ask Questions**: Type natural language questions like:
   - "Show me revenue trends over time"
   - "What are the top 5 products by sales?"
   - "Compare conversion rates by region"
   - "Find the strongest correlations in this dataset"
4. **View Results**: Get AI-generated insights with interactive charts

## API Endpoints

### Backend Endpoints

- `POST /upload` - Upload CSV/Excel file
  - Returns: session_id, schema, preview, row_count, profile

- `POST /analyze` - Analyze data with natural language
  - Body: `{session_id, question, conversation_id?}`
  - Returns: `{insight, chart_config, data, sql, analysis_type, follow_up_questions, conversation_id}`

- `GET /session/{session_id}` - Get session info
- `GET /session/{session_id}/profile` - Get dataset profile info
- `DELETE /session/{session_id}` - Delete session
- `GET /health` - Health check

### Frontend API Routes

- `POST /api/upload` - Proxy to backend upload
- `POST /api/analyze` - Proxy to backend analyze

## Security Features

- **SQL Injection Protection**: Only SELECT queries allowed
- **Query Validation**: Rejects comments, multi-statement SQL, dangerous keywords, and IO functions
- **Row Limits**: Maximum 1000 rows per query
- **Session TTL**: Auto-cleanup after 1 hour
- **Session Cap**: LRU cleanup prevents unbounded in-memory growth
- **File Type Validation**: Accepts `.csv`, `.xls`, `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, `.xlsb`
- **File Size Validation**: Uploads are capped at 25MB

## Tech Stack

### Backend
- FastAPI - Web framework
- DuckDB - In-memory analytical database
- OpenAI - AI/LLM for SQL generation
- Pandas - Data manipulation
- Python 3.11+

### Frontend
- Next.js 16 - React framework
- TypeScript - Type safety
- Recharts - Data visualization
- React Dropzone - File uploads
- Tailwind CSS - Styling

## Example Questions

Try asking:
- "What's the average value by category?"
- "Show me trends over the last 6 months"
- "Which items have the highest correlation?"
- "Compare metrics across different segments"
- "What are the outliers in this dataset?"

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI app & endpoints
├── services/
│   ├── data_service.py  # DuckDB operations
│   └── ai_service.py    # OpenAI integration
└── pyproject.toml       # Dependencies

frontend/
├── app/
│   ├── dashboard/       # Main dashboard page
│   ├── privacy/         # Privacy Policy page
│   ├── terms/           # Terms of Service page
│   └── api/             # API route proxies
├── components/
│   ├── CSVUploader.tsx      # File upload
│   ├── DataPreview.tsx      # Schema/data preview
│   ├── DynamicChart.tsx     # Chart renderer
│   └── DataChatInterface.tsx # Chat interface
└── package.json
```

## Contributing

Feel free to submit issues or pull requests!

## License

MIT
