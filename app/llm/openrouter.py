import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def call_openrouter(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    settings = get_settings()
    if not settings.llm_enabled or not settings.openrouter_api_key:
        return None

    models = [settings.openrouter_model, settings.openrouter_fallback_model]
    for model in models:
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": settings.openrouter_app_url,
                        "X-Title": settings.openrouter_app_name,
                    },
                    json={
                        "model": model,
                        "temperature": 0,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as exc:
            logger.warning("OpenRouter call failed for model %s: %s", model, exc)
            continue
    return None
