from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from ai.main import AIClient
from services.data_service import DataService
from services.ai_service import AIAnalystService
import logging
import tempfile
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Store conversation contexts (in production, use a proper database)
conversations = {}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str | None = None


class AnalyzeRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from CSV upload")
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language question")


@app.get("/")
async def root():
    return {"message": "Chat with Database AI Analyst API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file and create a DuckDB session
    Returns session_id, schema, preview, and row count
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Process CSV with data service
            result = data_service.upload_csv(tmp_path)
            logger.info(f"CSV uploaded successfully: {file.filename}, session: {result['session_id']}")
            return result

        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass

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

        # Get session info
        session_info = data_service.get_session_info(request.session_id)

        # Generate SQL and chart config using AI
        ai_response = ai_analyst.analyze_question(
            question=request.question,
            schema=session_info["schema"]
        )

        # Execute SQL query
        df = data_service.execute_query(
            session_id=request.session_id,
            sql=ai_response["sql"]
        )

        # Convert to JSON-serializable format
        data = df.to_dict('records')

        # Optionally enhance insight with actual data
        if len(data) > 0:
            enhanced_insight = ai_analyst.generate_insight_from_data(
                question=request.question,
                data=data,
                sql_query=ai_response["sql"]
            )
        else:
            enhanced_insight = "No data found matching your query."

        return {
            "insight": enhanced_insight,
            "chart_config": ai_response["chart_config"],
            "data": data,
            "sql": ai_response["sql"],
            "row_count": len(data)
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


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        data_service.delete_session(session_id)
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
                    import json
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
