"""
Model router — centralizes all AI model selection.

Tasks are routed to the cheapest model that can handle them reliably.
Swap any model string here without touching the modules that use it.

Routing logic:
  detect   → Gemini Flash 1.5 via OpenRouter  (vision, one-word reply, ~30x cheaper than Sonnet)
  parse    → Claude Haiku via OpenRouter       (text, structured JSON, ~5x cheaper than Sonnet)
  qa       → Claude Sonnet direct (Anthropic)  (vision + scoring, quality matters, no routing overhead)
"""

import os
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Model identifiers ────────────────────────────────────────────────────────

MODELS = {
    "detect": "anthropic/claude-haiku-3",
    "parse":  "anthropic/claude-haiku-3",
    "qa":     "claude-sonnet-4-5",  # called direct via Anthropic SDK
}

# ── Clients ──────────────────────────────────────────────────────────────────

def _openrouter_client() -> OpenAI:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError(
            "OPENROUTER_API_KEY not set. Add it to .env (see .env.example)."
        )
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
        default_headers={
            "HTTP-Referer": "https://github.com/product-studio",
            "X-Title": "Product Studio",
        },
    )


def _anthropic_client() -> Anthropic:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Add it to .env (see .env.example)."
        )
    return Anthropic(api_key=key)


# ── Public helpers ───────────────────────────────────────────────────────────

def routed_text(task: str, prompt: str, max_tokens: int = 1024) -> str:
    """
    Send a text-only prompt via OpenRouter for the given task.

    Args:
        task:       key in MODELS ("parse", etc.)
        prompt:     the full user message
        max_tokens: response length cap

    Returns:
        model response as a plain string
    """
    model = MODELS[task]
    client = _openrouter_client()
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def routed_vision(task: str, image_b64: str, media_type: str, prompt: str, max_tokens: int = 64) -> str:
    """
    Send an image + text prompt via OpenRouter for the given task.

    Args:
        task:       key in MODELS ("detect", etc.)
        image_b64:  base64-encoded image data
        media_type: MIME type (e.g. "image/jpeg")
        prompt:     the text part of the prompt
        max_tokens: response length cap

    Returns:
        model response as a plain string
    """
    model = MODELS[task]
    client = _openrouter_client()
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{image_b64}",
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return response.choices[0].message.content


def qa_client() -> Anthropic:
    """Return the Anthropic client used for QA scoring (bypasses OpenRouter)."""
    return _anthropic_client()


def qa_model() -> str:
    """Return the model name used for QA scoring."""
    return MODELS["qa"]
