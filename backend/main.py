import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ai.main import AIClient
from services.data_service import DataService
from services.data_service import SUPPORTED_TABULAR_EXTENSIONS
from services.ai_service import AIAnalystService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_ANALYTICS_HISTORY_TURNS = 12
MAX_VIZ_POINTS = 320
MAX_SCATTER_POINTS = 700
MAX_BAR_POINTS = 30
MAX_PIE_POINTS = 12
CHART_TYPES = {"line", "bar", "scatter", "pie", "area"}

app = FastAPI(title="Chat with Database AI Analyst")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
ai_client = AIClient()
data_service = DataService()
ai_analyst = AIAnalystService()

conversations = {}
analytics_conversations = {}


def get_analytics_conversation_key(session_id: str, conversation_id: str) -> str:
    return f"{session_id}:{conversation_id}"


def _is_numeric(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    try:
        float(str(value).replace(",", ""))
        return True
    except (TypeError, ValueError):
        return False


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _looks_temporal(value: Any) -> bool:
    if isinstance(value, (datetime,)):
        return True
    if not isinstance(value, str):
        return False
    raw = value.strip()
    if not raw:
        return False
    if any(token in raw for token in ("-", "/", ":")) and len(raw) >= 8:
        try:
            datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False
    return False


def _infer_chart_columns(data: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    if not data:
        return [], [], []

    sample = data[: min(200, len(data))]
    keys = list(sample[0].keys())
    numeric_keys: list[str] = []
    temporal_keys: list[str] = []
    categorical_keys: list[str] = []

    for key in keys:
        values = [row.get(key) for row in sample if row.get(key) is not None]
        if not values:
            continue

        numeric_ratio = sum(1 for value in values if _is_numeric(value)) / len(values)
        temporal_ratio = sum(1 for value in values if _looks_temporal(value)) / len(values)

        if numeric_ratio >= 0.8:
            numeric_keys.append(key)
        elif temporal_ratio >= 0.8:
            temporal_keys.append(key)
        else:
            categorical_keys.append(key)

    return numeric_keys, temporal_keys, categorical_keys


def _normalize_chart_config(
    data: list[dict[str, Any]],
    base_config: dict[str, Any],
) -> dict[str, Any]:
    if not data:
        return {"type": "bar", "xKey": "", "yKey": ""}

    keys = list(data[0].keys())
    numeric_keys, temporal_keys, categorical_keys = _infer_chart_columns(data)

    chart_type = base_config.get("type")
    if chart_type not in CHART_TYPES:
        chart_type = "bar"

    x_key = base_config.get("xKey")
    y_key = base_config.get("yKey")
    group_by = base_config.get("groupBy")

    if x_key not in keys:
        x_key = temporal_keys[0] if temporal_keys else (categorical_keys[0] if categorical_keys else keys[0])

    if y_key not in keys or y_key == x_key:
        if numeric_keys:
            candidate = numeric_keys[0]
            if candidate == x_key and len(numeric_keys) > 1:
                candidate = numeric_keys[1]
            y_key = candidate
        else:
            y_key = keys[1] if len(keys) > 1 else keys[0]

    if chart_type == "scatter":
        if len(numeric_keys) >= 2:
            x_key = numeric_keys[0]
            y_key = numeric_keys[1]
        else:
            chart_type = "bar"

    if chart_type in {"line", "area"} and temporal_keys and x_key not in temporal_keys:
        x_key = temporal_keys[0]

    normalized = {"type": chart_type, "xKey": x_key, "yKey": y_key}
    if isinstance(group_by, str) and group_by in keys and group_by not in {x_key, y_key}:
        normalized["groupBy"] = group_by
    return normalized


def _build_chart_options(
    data: list[dict[str, Any]],
    base_config: dict[str, Any],
    analysis_type: str,
) -> list[dict[str, Any]]:
    if not data:
        return [base_config]

    numeric_keys, temporal_keys, categorical_keys = _infer_chart_columns(data)
    base = _normalize_chart_config(data, base_config)
    options: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def add_option(option: dict[str, Any]):
        signature = (
            option.get("type"),
            option.get("xKey"),
            option.get("yKey"),
            option.get("groupBy"),
        )
        if signature in seen:
            return
        seen.add(signature)
        options.append(option)

    add_option(base)

    if temporal_keys and numeric_keys:
        add_option({"type": "line", "xKey": temporal_keys[0], "yKey": numeric_keys[0]})
        add_option({"type": "area", "xKey": temporal_keys[0], "yKey": numeric_keys[0]})

    if categorical_keys and numeric_keys:
        add_option({"type": "bar", "xKey": categorical_keys[0], "yKey": numeric_keys[0]})
        unique_values = len({str(row.get(categorical_keys[0])) for row in data if row.get(categorical_keys[0]) is not None})
        if unique_values <= MAX_PIE_POINTS:
            add_option({"type": "pie", "xKey": categorical_keys[0], "yKey": numeric_keys[0]})

    if len(numeric_keys) >= 2:
        add_option({"type": "scatter", "xKey": numeric_keys[0], "yKey": numeric_keys[1]})

    if analysis_type == "correlation":
        options.sort(key=lambda item: 0 if item["type"] == "scatter" else 1)
    elif analysis_type == "trend":
        options.sort(key=lambda item: 0 if item["type"] in {"line", "area"} else 1)

    return options[:4]


def _sample_evenly(data: list[dict[str, Any]], max_points: int) -> list[dict[str, Any]]:
    if len(data) <= max_points:
        return data
    step = max(1, len(data) // max_points)
    sampled = data[::step]
    if sampled[-1] is not data[-1]:
        sampled.append(data[-1])
    return sampled[:max_points]


def _aggregate_categories(
    data: list[dict[str, Any]],
    x_key: str,
    y_key: str,
    max_points: int,
) -> list[dict[str, Any]]:
    buckets: dict[str, float] = {}
    for row in data:
        x_value = row.get(x_key)
        numeric_value = _to_float(row.get(y_key))
        if x_value is None or numeric_value is None:
            continue
        label = str(x_value)
        buckets[label] = buckets.get(label, 0.0) + numeric_value

    ranked = sorted(buckets.items(), key=lambda pair: abs(pair[1]), reverse=True)
    if len(ranked) <= max_points:
        return [{x_key: key, y_key: value} for key, value in ranked]

    top = ranked[:max_points - 1]
    other_total = sum(value for _, value in ranked[max_points - 1:])
    result = [{x_key: key, y_key: value} for key, value in top]
    result.append({x_key: "Other", y_key: other_total})
    return result


def _optimize_data_for_chart(
    data: list[dict[str, Any]],
    chart_config: dict[str, Any],
) -> list[dict[str, Any]]:
    if not data:
        return data

    chart_type = chart_config.get("type")
    x_key = chart_config.get("xKey")
    y_key = chart_config.get("yKey")

    if not isinstance(x_key, str) or not isinstance(y_key, str):
        return _sample_evenly(data, MAX_VIZ_POINTS)

    if chart_type == "scatter":
        return _sample_evenly(data, MAX_SCATTER_POINTS)

    if chart_type in {"line", "area"}:
        return _sample_evenly(data, MAX_VIZ_POINTS)

    if chart_type == "bar":
        return _aggregate_categories(data, x_key, y_key, MAX_BAR_POINTS)

    if chart_type == "pie":
        return _aggregate_categories(data, x_key, y_key, MAX_PIE_POINTS)

    return _sample_evenly(data, MAX_VIZ_POINTS)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str | None = None


class AnalyzeRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from CSV upload")
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language question")
    conversation_id: str | None = Field(default=None, max_length=100)


@app.get("/")
async def root():
    return {"message": "Chat with Database AI Analyst API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV/Excel file and create a DuckDB session.
    Returns session_id, schema, preview, and row count
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required.")

        extension = os.path.splitext(file.filename)[1].lower()
        if extension not in SUPPORTED_TABULAR_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_TABULAR_EXTENSIONS))
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{extension}'. Supported types: {supported}",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size is {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.",
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=extension or ".tmp") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = data_service.upload_file(tmp_path)
            logger.info(f"File uploaded successfully: {file.filename}, session: {result['session_id']}")
            return result

        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_data(request: AnalyzeRequest):
    """
    Analyze data using natural language question
    Returns SQL query, data, chart config, and insight
    """
    try:
        logger.info(f"Analyzing question for session {request.session_id}: {request.question[:100]}...")

        session_info = data_service.get_session_info(request.session_id)
        conversation_id = request.conversation_id or str(uuid.uuid4())
        conv_key = get_analytics_conversation_key(request.session_id, conversation_id)
        history = analytics_conversations.get(conv_key, [])

        ai_response = ai_analyst.analyze_question(
            question=request.question,
            schema=session_info["schema"],
            table_name=session_info["table_name"],
            profile=session_info.get("profile"),
            conversation_history=history,
        )

        df = data_service.execute_query(
            session_id=request.session_id,
            sql=ai_response["sql"]
        )

        query_data = jsonable_encoder(df.to_dict("records"))
        chart_options = _build_chart_options(
            data=query_data,
            base_config=ai_response["chart_config"],
            analysis_type=ai_response.get("analysis_type", "other"),
        )
        chart_data = _optimize_data_for_chart(query_data, chart_options[0])
        enhanced_insight = ai_response["insight"] if query_data else "No data found matching your query."

        history.append({"role": "user", "content": request.question})
        history.append({"role": "assistant", "content": enhanced_insight})
        analytics_conversations[conv_key] = history[-MAX_ANALYTICS_HISTORY_TURNS:]

        return {
            "insight": enhanced_insight,
            "chart_config": chart_options[0],
            "chart_options": chart_options,
            "data": chart_data,
            "sql": ai_response["sql"],
            "row_count": len(query_data),
            "visualized_row_count": len(chart_data),
            "analysis_type": ai_response.get("analysis_type", "other"),
            "follow_up_questions": ai_response.get("follow_up_questions", []),
            "conversation_id": conversation_id,
        }

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    try:
        return data_service.get_session_info(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/session/{session_id}/profile")
async def get_session_profile(session_id: str):
    try:
        session_info = data_service.get_session_info(session_id)
        return {
            "session_id": session_id,
            "profile": session_info.get("profile", {}),
            "row_count": session_info.get("row_count"),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        data_service.delete_session(session_id)
        stale_keys = [key for key in analytics_conversations if key.startswith(f"{session_id}:")]
        for key in stale_keys:
            del analytics_conversations[key]
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return AI response (non-streaming).
    """
    try:
        logger.info(f"Received chat request: {request.message[:50]}...")

        # Get or create conversation context
        conversation_id = request.conversation_id or "default"
        context = conversations.get(conversation_id, [])

        # Send message to AI
        result = ai_client.send_message(context=context, message=request.message)

        # Update stored context
        conversations[conversation_id] = result["context"]

        return ChatResponse(
            message=result["message"],
            conversation_id=conversation_id
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Process a chat message and stream AI response using Server-Sent Events.
    """
    try:
        logger.info(f"Received streaming chat request: {request.message[:50]}...")

        # Get or create conversation context
        conversation_id = request.conversation_id or "default"
        context = conversations.get(conversation_id, [])

        async def event_generator():
            try:
                async for chunk in ai_client.stream_message(context=context, message=request.message):
                    yield f"data: {chunk}\n\n"

                    # Update stored context when done
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("done") and "context" in chunk_data:
                        conversations[conversation_id] = chunk_data["context"]
            except Exception as e:
                logger.error(f"Error in stream: {e}")
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    except Exception as e:
        logger.error(f"Error processing streaming chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
