from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import httpx

from app.config import settings
from app.memory import load_history, save_history
from app.prompt import build_system_prompt

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = build_system_prompt()


async def stream_chat(
    message: str,
    session_id: str,
) -> AsyncIterator[str]:
    """Stream a chat response from OpenRouter.

    Loads conversation history from GCS, appends the new user message,
    calls OpenRouter with streaming enabled, yields chunks, and saves
    the updated history when done.
    """
    if not settings.openrouter_api_key:
        logger.error("OPENROUTER_API_KEY is not set.")
        yield "Set OPENROUTER_API_KEY and restart."
        return

    # Load existing conversation history.
    history = load_history(session_id)
    history.append({"role": "user", "content": message})

    # Build the full messages array for the LLM.
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(history)

    payload = {
        "model": settings.chat_model,
        "max_tokens": settings.max_output_tokens,
        "stream": True,
        "messages": messages,
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.app_referer,
        "X-Title": settings.app_title,
    }

    assistant_text = ""

    async with (
        httpx.AsyncClient(timeout=60.0) as client,
        client.stream(
            "POST",
            settings.openrouter_base_url,
            headers=headers,
            json=payload,
        ) as response,
    ):
        if response.status_code != 200:
            body = await response.aread()
            logger.error(
                "OpenRouter error %s: %s",
                response.status_code,
                body[:500],
            )
            yield "I'm having trouble connecting to my brain right now. Please try again."
            return

        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue

            data = line[6:]  # Strip "data: " prefix.
            if data == "[DONE]":
                break

            try:
                chunk = json.loads(data)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    assistant_text += content
                    yield content
            except (json.JSONDecodeError, IndexError, KeyError):
                continue

    # Save the updated conversation history.
    if assistant_text:
        history.append({"role": "assistant", "content": assistant_text})
        save_history(session_id, history)
