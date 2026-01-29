from fastapi import FastAPI
from .models import aiRequest
from ai import AIClient

app = FastAPI()
ai_request = AIClient()

@app.post("/aichat")
async def send_ai_request(request: aiRequest):
    response = ai_request.send_message(context=None, message=request.message)
    return {"ai_conversation" : response}