"""
Brief parsing: convert a buyer's free-text Fiverr message into a
structured JSON brief the rest of the pipeline can act on.

Routes to Claude Haiku via OpenRouter — ~5x cheaper than Sonnet
for straightforward text-to-JSON extraction.
"""

import json
from model_router import routed_text
from dotenv import load_dotenv

load_dotenv()

PARSE_PROMPT = """You are extracting a structured brief from a Fiverr buyer's message about cozy/rustic product photography for handmade soap.

Return ONLY valid JSON with these fields, no other text or markdown fences:

{{
  "product_type": "short string describing the soap (e.g. 'lavender oatmeal bar')",
  "num_images": integer (default 5 if not specified),
  "aesthetic_hint": one of "cozy_rustic" | "off_brand" | "unspecified",
  "requested_scenes": array of strings if buyer asked for specific scenes, else [],
  "special_requests": array of any unusual requirements (seasonal, color, props, etc),
  "deadline_hint": string or null,
  "notes": "short plain-language summary of what they want"
}}

If the buyer asks for an aesthetic that's clearly not cozy/rustic (e.g. cyberpunk, neon, ultra-modern minimalist), set aesthetic_hint to "off_brand" and flag in special_requests.

Buyer message:
---
{message}
---"""


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 1)[1] if "```" in text else text
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
        if text.rstrip().endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def parse_brief(buyer_message: str) -> dict:
    """
    Parse a buyer's free-text message into a structured brief.

    Args:
        buyer_message: the raw message from the buyer (Fiverr DM, email, etc.)

    Returns:
        dict with the structured brief fields described in PARSE_PROMPT
    """
    print("[parse] sending brief to Claude Haiku via OpenRouter...")
    raw_text = routed_text(
        task="parse",
        prompt=PARSE_PROMPT.format(message=buyer_message),
        max_tokens=600,
    )
    cleaned = _strip_code_fences(raw_text)

    try:
        brief = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model returned non-JSON: {e}\n"
            f"Raw response: {raw_text[:500]}"
        ) from e

    print(f"[parse] parsed brief: {brief.get('notes', '(no notes)')}")
    return brief


if __name__ == "__main__":
    sample = (
        "Hi! I run a small handmade soap shop on Etsy. I just launched a "
        "lavender oatmeal soap bar and I need 5 cozy farmhouse-style photos "
        "for my listing. Bonus if one of them has dried lavender in it. "
        "Thanks!"
    )
    result = parse_brief(sample)
    print(json.dumps(result, indent=2))
