"""Quick OpenRouter connectivity check."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.llm.openrouter import call_openrouter
from app.llm.prompts import SYSTEM_PROMPT


async def main() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    print(f"Model: {settings.openrouter_model}")
    print(f"LLM enabled: {settings.llm_enabled}")
    print(f"API key configured: {bool(settings.openrouter_api_key)}")

    prompt = (
        '{"instruction":"Return JSON with agent_summary, recommended_next_action, customer_reply",'
        '"drafts":{"agent_summary":"Test","recommended_next_action":"Review",'
        '"customer_reply":"Thank you for contacting us."}}'
    )
    result = await call_openrouter(SYSTEM_PROMPT, prompt)
    if result:
        print("OpenRouter connection: SUCCESS")
        print("Response keys:", list(result.keys()))
    else:
        print("OpenRouter connection: FAILED — check key, model, or quota")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
