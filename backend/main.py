import asyncio
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ai.main import AIClient
from models.api_models import (
    ActionApproveRequest,
    ActionDraftRequest,
    AnomalyLabRequest,
    AnalysisSprintRequest,
    AnalyzeRequest,
    CausalLabRequest,
    ChatRequest,
    ChatResponse,
    HypothesisRequest,
    RegressionLabRequest,
)
from services.ai_service import AIAnalystService
from services.analysis_runtime import AnalysisRuntime
from services.data_service import DataService, SUPPORTED_TABULAR_EXTENSIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_ANALYTICS_HISTORY_TURNS = 12

app = FastAPI(title="Chat with Database AI Analyst")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_client = AIClient()
data_service = DataService()
ai_analyst = AIAnalystService()
runtime = AnalysisRuntime(ai_analyst=ai_analyst, data_service=data_service)

conversations: dict[str, list[dict[str, str]]] = {}
analytics_conversations: dict[str, list[dict[str, str]]] = {}
session_hypotheses: dict[str, dict[str, Any]] = {}
session_action_workflows: dict[str, dict[str, dict[str, Any]]] = {}


def get_analytics_conversation_key(session_id: str, conversation_id: str) -> str:
    return f"{session_id}:{conversation_id}"


def _prepare_analytics_request(
    session_id: str,
    requested_conversation_id: str | None,
) -> tuple[dict[str, Any], str, list[dict[str, str]]]:
    session_info = data_service.get_session_info(session_id)
    conversation_id = requested_conversation_id or str(uuid.uuid4())
    conv_key = get_analytics_conversation_key(session_id, conversation_id)
    history = analytics_conversations.get(conv_key, [])
    return session_info, conversation_id, history


def _build_exploration_recap(exploration: Any) -> str:
    if not isinstance(exploration, dict):
        return ""

    probes = exploration.get("probes")
    primary_probe_id = exploration.get("primary_probe_id")
    if not isinstance(probes, list) or not probes:
        return ""

    recap_lines: list[str] = []
    for probe in probes[:5]:
        if not isinstance(probe, dict):
            continue
        probe_id = str(probe.get("probe_id", "")).strip() or "probe"
        prefix = "*" if probe_id == primary_probe_id else "-"
        recap_lines.append(
            f"{prefix} {probe_id}: {str(probe.get('question', '')).strip()} "
            f"(rows={probe.get('row_count', 'n/a')})"
        )
    return "\n".join(recap_lines)


def _build_assistant_context(analysis_result: dict[str, Any]) -> str:
    insight = str(analysis_result.get("insight", "")).strip()
    recap = _build_exploration_recap(analysis_result.get("exploration"))
    if not recap:
        return insight
    return f"{insight}\n\nExploration recap:\n{recap}"


def _store_analytics_turn(
    session_id: str,
    conversation_id: str,
    question: str,
    analysis_result: dict[str, Any],
    history: list[dict[str, str]],
) -> None:
    conv_key = get_analytics_conversation_key(session_id, conversation_id)
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": _build_assistant_context(analysis_result)})
    analytics_conversations[conv_key] = history[-MAX_ANALYTICS_HISTORY_TURNS:]


@app.get("/")
async def root():
    return {"message": "Chat with Database AI Analyst API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
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
            logger.info("File uploaded successfully: %s, session: %s", file.filename, result["session_id"])
            return result
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading file: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_data(request: AnalyzeRequest):
    try:
        logger.info("Analyzing question for session %s: %s...", request.session_id, request.question[:100])

        session_info, conversation_id, history = _prepare_analytics_request(
            session_id=request.session_id,
            requested_conversation_id=request.conversation_id,
        )

        analysis_result = runtime.run_analysis(
            session_id=request.session_id,
            session_info=session_info,
            question=request.question,
            conversation_history=history,
            sprint_mode=False,
        )

        _store_analytics_turn(
            session_id=request.session_id,
            conversation_id=conversation_id,
            question=request.question,
            analysis_result=analysis_result,
            history=history,
        )

        return {**analysis_result, "conversation_id": conversation_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error analyzing data: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/stream")
async def analyze_data_stream(request: AnalyzeRequest):
    queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    async def producer():
        try:
            logger.info("Streaming analysis for session %s: %s...", request.session_id, request.question[:100])

            session_info, conversation_id, history = _prepare_analytics_request(
                session_id=request.session_id,
                requested_conversation_id=request.conversation_id,
            )

            def on_progress(event: dict[str, Any]):
                payload = {"type": "progress", **event}
                loop.call_soon_threadsafe(queue.put_nowait, payload)

            analysis_result = await asyncio.to_thread(
                runtime.run_analysis,
                request.session_id,
                session_info,
                request.question,
                history,
                False,
                on_progress,
            )

            _store_analytics_turn(
                session_id=request.session_id,
                conversation_id=conversation_id,
                question=request.question,
                analysis_result=analysis_result,
                history=history,
            )

            loop.call_soon_threadsafe(
                queue.put_nowait,
                {
                    "type": "result",
                    "done": True,
                    "conversation_id": conversation_id,
                    "payload": analysis_result,
                },
            )
        except ValueError as e:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"type": "error", "detail": str(e), "status": 400, "done": True},
            )
        except Exception as e:
            logger.error("Error streaming data analysis: %s", e)
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"type": "error", "detail": str(e), "status": 500, "done": True},
            )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    producer_task = asyncio.create_task(producer())

    async def event_generator():
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield f"data: {json.dumps(item, default=str)}\n\n"
        finally:
            if not producer_task.done():
                producer_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/hypotheses")
async def generate_hypotheses(request: HypothesisRequest):
    try:
        session_info = data_service.get_session_info(request.session_id)
        cached = session_hypotheses.get(request.session_id)

        if cached and not request.refresh and len(cached.get("hypotheses", [])) == request.count:
            return {
                "session_id": request.session_id,
                "hypotheses": cached["hypotheses"],
                "rationale_summary": cached["rationale_summary"],
                "cached": True,
            }

        generated = ai_analyst.generate_hypotheses(
            schema=session_info["schema"],
            profile=session_info.get("profile"),
            table_name=session_info["table_name"],
            count=request.count,
        )
        session_hypotheses[request.session_id] = generated

        return {
            "session_id": request.session_id,
            "hypotheses": generated["hypotheses"],
            "rationale_summary": generated["rationale_summary"],
            "cached": False,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error generating hypotheses: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis/sprint")
async def run_analysis_sprint(request: AnalysisSprintRequest):
    try:
        session_info = data_service.get_session_info(request.session_id)
        questions = request.questions or session_hypotheses.get(request.session_id, {}).get("hypotheses")

        if not questions:
            generated = ai_analyst.generate_hypotheses(
                schema=session_info["schema"],
                profile=session_info.get("profile"),
                table_name=session_info["table_name"],
                count=request.max_questions,
            )
            session_hypotheses[request.session_id] = generated
            questions = generated["hypotheses"]

        cleaned_questions = []
        seen = set()
        for question in questions:
            if not isinstance(question, str):
                continue
            candidate = question.strip()
            if not candidate:
                continue
            key = candidate.lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned_questions.append(candidate)

        cleaned_questions = cleaned_questions[: request.max_questions]
        if not cleaned_questions:
            raise HTTPException(status_code=400, detail="No valid questions provided for sprint run.")

        results = []
        failures = []
        for question in cleaned_questions:
            try:
                result = runtime.run_analysis(
                    session_id=request.session_id,
                    session_info=session_info,
                    question=question,
                    conversation_history=[],
                    sprint_mode=True,
                )
                results.append(result)
            except Exception as e:
                failures.append({"question": question, "error": str(e)})

        if not results:
            raise HTTPException(status_code=500, detail="All sprint analyses failed.")

        confidence_values = [item["trust"]["confidence_score"] for item in results if item.get("trust")]
        average_confidence = (sum(confidence_values) / len(confidence_values)) if confidence_values else 0.0

        return {
            "session_id": request.session_id,
            "question_count": len(cleaned_questions),
            "completed_count": len(results),
            "failed_count": len(failures),
            "average_confidence_score": round(average_confidence, 2),
            "results": results,
            "failures": failures,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error running analysis sprint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/causal-lab")
async def run_causal_lab(request: CausalLabRequest):
    try:
        session_info = data_service.get_session_info(request.session_id)
        table_name = session_info["table_name"]
        df = data_service.execute_query(
            session_id=request.session_id,
            sql=f"SELECT * FROM {table_name}",
            max_rows=8000,
        )
        if df.empty:
            raise HTTPException(status_code=400, detail="No rows available for causal analysis.")

        return runtime.build_causal_lab_result(
            data_frame=df,
            target_metric=request.target_metric,
            max_drivers=request.max_drivers,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error running causal lab: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/regression")
async def run_regression_lab(request: RegressionLabRequest):
    try:
        session_info = data_service.get_session_info(request.session_id)
        table_name = session_info["table_name"]
        df = data_service.execute_query(
            session_id=request.session_id,
            sql=f"SELECT * FROM {table_name}",
            max_rows=request.max_rows,
        )
        if df.empty:
            raise HTTPException(status_code=400, detail="No rows available for regression analysis.")

        return runtime.build_regression_result(
            data_frame=df,
            target_column=request.target_column,
            feature_columns=request.feature_columns,
            test_fraction=request.test_fraction,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error running regression lab: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/anomalies")
async def run_anomaly_lab(request: AnomalyLabRequest):
    try:
        session_info = data_service.get_session_info(request.session_id)
        table_name = session_info["table_name"]
        df = data_service.execute_query(
            session_id=request.session_id,
            sql=f"SELECT * FROM {table_name}",
            max_rows=request.max_rows,
        )
        if df.empty:
            raise HTTPException(status_code=400, detail="No rows available for anomaly detection.")

        return runtime.detect_anomalies(
            data_frame=df,
            metric_column=request.metric_column,
            group_by=request.group_by,
            z_threshold=request.z_threshold,
            max_results=request.max_results,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error running anomaly lab: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/actions/draft")
async def draft_actions(request: ActionDraftRequest):
    try:
        data_service.get_session_info(request.session_id)
        drafts = ai_analyst.draft_actions(
            question=request.question,
            insight=request.insight,
            sql=request.sql,
            analysis_type=request.analysis_type,
            trust=request.trust,
        )

        stored_actions = session_action_workflows.setdefault(request.session_id, {})
        created = []
        for action in drafts:
            action_id = str(uuid.uuid4())
            record = {
                "action_id": action_id,
                "type": action["type"],
                "title": action["title"],
                "description": action["description"],
                "payload": action["payload"],
                "status": "pending_approval",
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
            stored_actions[action_id] = record
            created.append(record)

        return {"session_id": request.session_id, "actions": created}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error drafting actions: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/actions/approve")
async def approve_action(request: ActionApproveRequest):
    try:
        actions = session_action_workflows.get(request.session_id, {})
        if request.action_id not in actions:
            raise HTTPException(status_code=404, detail="Action not found for session.")

        action = actions[request.action_id]
        if action.get("status") == "executed":
            return {"session_id": request.session_id, "action": action}

        execution = runtime.execute_action(action)
        action["status"] = "executed"
        action["approved_at"] = datetime.utcnow().isoformat() + "Z"
        action["execution"] = execution
        actions[request.action_id] = action

        return {"session_id": request.session_id, "action": action}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error approving action: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
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
    try:
        data_service.delete_session(session_id)
        stale_keys = [key for key in analytics_conversations if key.startswith(f"{session_id}:")]
        for key in stale_keys:
            del analytics_conversations[key]
        session_hypotheses.pop(session_id, None)
        session_action_workflows.pop(session_id, None)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error("Error deleting session: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        conversation_id = request.conversation_id or "default"
        context = conversations.get(conversation_id, [])
        result = ai_client.send_message(context=context, message=request.message)
        conversations[conversation_id] = result["context"]

        return ChatResponse(
            message=result["message"],
            conversation_id=conversation_id,
        )
    except Exception as e:
        logger.error("Error processing chat request: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        conversation_id = request.conversation_id or "default"
        context = conversations.get(conversation_id, [])

        async def event_generator():
            try:
                async for chunk in ai_client.stream_message(context=context, message=request.message):
                    yield f"data: {chunk}\n\n"
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("done") and "context" in chunk_data:
                        conversations[conversation_id] = chunk_data["context"]
            except Exception as e:
                logger.error("Error in stream: %s", e)
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error("Error processing streaming chat request: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
