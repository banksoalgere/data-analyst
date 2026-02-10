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
    AnalysisSprintRequest,
    AnalyzeRequest,
    CausalLabRequest,
    ChatRequest,
    ChatResponse,
    HypothesisRequest,
)
from services.ai_service import AIAnalystService
from services.analysis_runtime import AnalysisRuntime
from services.data_service import DataService, SUPPORTED_TABULAR_EXTENSIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
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

        session_info = data_service.get_session_info(request.session_id)
        conversation_id = request.conversation_id or str(uuid.uuid4())
        conv_key = get_analytics_conversation_key(request.session_id, conversation_id)
        history = analytics_conversations.get(conv_key, [])

        analysis_result = runtime.run_analysis(
            session_id=request.session_id,
            session_info=session_info,
            question=request.question,
            conversation_history=history,
            sprint_mode=False,
        )

        history.append({"role": "user", "content": request.question})
        history.append({"role": "assistant", "content": analysis_result["insight"]})
        analytics_conversations[conv_key] = history[-MAX_ANALYTICS_HISTORY_TURNS:]

        return {**analysis_result, "conversation_id": conversation_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error analyzing data: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


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
