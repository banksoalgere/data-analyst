import openai
import os
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any, AsyncGenerator
import json

logging.basicConfig(level=logging.INFO)

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logging.warning("No api key set")

class AIClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=api_key)

    def send_message(self, context: Optional[list] = None, message: str = "") -> Dict[str, Any]:
        """A function to send messages using the OpenAI Responses API (non-streaming)"""
        try:
            logging.info("Sending message to OpenAI client")
            if context is None:
                context = []

            # Add the new user message to context
            new_context = {"role": "user", "content": message}
            context.append(new_context)

            # Make the API call using Responses API
            response = self.client.responses.create(
                model="gpt-4o-mini",
                input=context,
            )

            # Extract the assistant's reply from response.output
            assistant_message = ""
            if response.output and len(response.output) > 0:
                # Get the first output message
                output_message = response.output[0]
                if hasattr(output_message, 'content') and len(output_message.content) > 0:
                    # Get the text from the first content part
                    content_part = output_message.content[0]
                    if hasattr(content_part, 'text'):
                        assistant_message = content_part.text

            # Add assistant's reply to context
            context.append({"role": "assistant", "content": assistant_message})

            return {
                "message": assistant_message,
                "context": context
            }
        except Exception as e:
            logging.error(f"Failed to send user message to OpenAI API: {e}")
            raise

    async def stream_message(self, context: Optional[list] = None, message: str = "") -> AsyncGenerator[str, None]:
        """Stream messages using the OpenAI Responses API with streaming enabled"""
        try:
            logging.info("Streaming message to OpenAI client")
            if context is None:
                context = []

            # Add the new user message to context
            new_context = {"role": "user", "content": message}
            context.append(new_context)

            # Make the streaming API call
            stream = self.client.responses.create(
                model="gpt-4o-mini",
                input=context,
                stream=True,
            )

            full_response = ""
            for event in stream:
                # Handle ResponseTextDeltaEvent which has the actual text content
                if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                    if hasattr(event, 'delta'):
                        content = event.delta
                        full_response += content
                        yield json.dumps({"content": content, "done": False}) + "\n"

            # Send final message with full context update
            context.append({"role": "assistant", "content": full_response})
            yield json.dumps({"content": "", "done": True, "context": context}) + "\n"

        except Exception as e:
            logging.error(f"Failed to stream message to OpenAI API: {e}")
            import traceback
            logging.error(traceback.format_exc())
            yield json.dumps({"error": str(e), "done": True}) + "\n"
