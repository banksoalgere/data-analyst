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


MODEL_NAME = "gpt-5"


class AIClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=api_key)

    @staticmethod
    def _coerce_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if content is None:
            return ""
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                elif hasattr(item, "text") and isinstance(item.text, str):
                    parts.append(item.text)
            return "\n".join(part for part in parts if part).strip()
        if isinstance(content, dict):
            text = content.get("text")
            if isinstance(text, str):
                return text
            return json.dumps(content, default=str)
        return str(content)

    def _build_chat_messages(self, context: list[dict[str, Any]]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for item in context:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            if role not in {"system", "user", "assistant"}:
                continue

            content = self._coerce_content(item.get("content"))
            if not content.strip():
                continue
            messages.append({"role": role, "content": content})
        return messages

    @staticmethod
    def _extract_stream_delta(delta_content: Any) -> str:
        if isinstance(delta_content, str):
            return delta_content
        if isinstance(delta_content, list):
            parts: list[str] = []
            for part in delta_content:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str):
                        parts.append(text)
                elif hasattr(part, "text") and isinstance(part.text, str):
                    parts.append(part.text)
            return "".join(parts)
        return ""

    def send_message(self, context: Optional[list] = None, message: str = "") -> Dict[str, Any]:
        """Send a chat message using Chat Completions (non-streaming)."""
        try:
            logging.info("Sending message to OpenAI client")
            if context is None:
                context = []

            # Add the new user message to context
            new_context = {"role": "user", "content": message}
            context.append(new_context)

            # Make the API call using Chat Completions
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=self._build_chat_messages(context),
            )

            assistant_message = self._coerce_content(response.choices[0].message.content)

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
        """Stream chat messages using Chat Completions."""
        try:
            logging.info("Streaming message to OpenAI client")
            if context is None:
                context = []

            # Add the new user message to context
            new_context = {"role": "user", "content": message}
            context.append(new_context)

            # Make the streaming API call
            stream = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=self._build_chat_messages(context),
                stream=True,
            )

            full_response = ""
            for chunk in stream:
                choices = getattr(chunk, "choices", [])
                if not choices:
                    continue

                delta = getattr(choices[0], "delta", None)
                if not delta:
                    continue

                content = self._extract_stream_delta(getattr(delta, "content", None))
                if not content:
                    continue

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
