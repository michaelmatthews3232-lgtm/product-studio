"""
Automated QA: send each generated image to Claude vision and score it.

This is your safety net, not your final filter. Mike still reviews
every batch manually before delivery. The QA pass catches the obvious
failures (warped products, garbled labels, AI artifacts) so that the
human review focuses on subtle quality choices.
"""

import os
import json
import base64
from model_router import qa_client, qa_model
from dotenv import load_dotenv

load_dotenv()

QA_PROMPTS = {
    "soap": """You are reviewing an AI-generated cozy/rustic product photograph of a soap bar for a paying client. Score strictly.

Return ONLY valid JSON, no markdown fences:
{
  "product_fidelity": integer 1-10 (does the soap look real, coherent, undistorted?),
  "composition": integer 1-10 (professional photography composition?),
  "lighting": integer 1-10 (realistic, cozy/rustic appropriate lighting?),
  "aesthetic_match": integer 1-10 (genuinely reads as cozy/rustic?),
  "artifact_free": integer 1-10 (no warped shapes or garbled label text?),
  "pass": boolean (true ONLY if all scores 7+ and no dealbreakers),
  "issues": array of short problem strings (empty if none),
  "best_use": one of "hero_shot" | "secondary_shot" | "do_not_ship"
}
Be strict. If the soap looks warped, wrong color, or has garbled text, pass = false.""",

    "candle": """You are reviewing an AI-generated cozy/rustic product photograph of a candle for a paying client. Score strictly.

Return ONLY valid JSON, no markdown fences:
{
  "product_fidelity": integer 1-10 (does the candle look real and undistorted?),
  "composition": integer 1-10 (professional photography composition?),
  "lighting": integer 1-10 (realistic flame glow and ambient light?),
  "aesthetic_match": integer 1-10 (genuinely reads as cozy/rustic?),
  "artifact_free": integer 1-10 (no warped shapes or AI weirdness?),
  "pass": boolean (true ONLY if all scores 7+ and no dealbreakers),
  "issues": array of short problem strings (empty if none),
  "best_use": one of "hero_shot" | "secondary_shot" | "do_not_ship"
}
Be strict. If the candle or flame looks unnatural, pass = false.""",

    "staging": """You are reviewing an AI-generated virtual room staging image for a real estate or interior design client. Score strictly.

Return ONLY valid JSON, no markdown fences:
{
  "realism": integer 1-10 (does the room look like a real professionally staged space?),
  "composition": integer 1-10 (good camera angle, balanced furniture layout?),
  "lighting": integer 1-10 (natural, realistic lighting consistent with the room?),
  "style_consistency": integer 1-10 (does the furniture and decor match a coherent interior style?),
  "artifact_free": integer 1-10 (no floating objects, warped walls, or AI weirdness?),
  "pass": boolean (true ONLY if all scores 7+ and no dealbreakers),
  "issues": array of short problem strings (empty if none),
  "best_use": one of "hero_shot" | "secondary_shot" | "do_not_ship"
}
Be strict. If furniture looks fake, walls are warped, or the room feels uncanny, pass = false.""",

    "default": """You are reviewing an AI-generated product image for a paying client. Score strictly.

Return ONLY valid JSON, no markdown fences:
{
  "product_fidelity": integer 1-10 (does the subject look real and undistorted?),
  "composition": integer 1-10 (professional composition?),
  "lighting": integer 1-10 (realistic lighting?),
  "aesthetic_match": integer 1-10 (matches the intended style?),
  "artifact_free": integer 1-10 (no AI artifacts or weirdness?),
  "pass": boolean (true ONLY if all scores 7+ and no dealbreakers),
  "issues": array of short problem strings (empty if none),
  "best_use": one of "hero_shot" | "secondary_shot" | "do_not_ship"
}"""
}


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 1)[1] if "```" in text else text
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
        if text.rstrip().endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def qa_image(image_path: str, product: str = "soap") -> dict:
    """
    Score a single generated image.

    Args:
        image_path: local path to a JPEG
        product: product type key matching QA_PROMPTS (soap, candle, staging)

    Returns:
        dict with QA fields described in the product-specific prompt
    """
    prompt = QA_PROMPTS.get(product, QA_PROMPTS["default"])

    with open(image_path, "rb") as f:
        image_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    client = qa_client()
    response = client.messages.create(
        model=qa_model(),
        max_tokens=600,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )

    raw_text = response.content[0].text
    cleaned = _strip_code_fences(raw_text)

    try:
        score = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude QA returned non-JSON: {e}\n"
            f"Raw response: {raw_text[:500]}"
        ) from e

    return score


def qa_batch(image_paths: list[str], product: str = "soap") -> list[dict]:
    """Score a list of images. Returns list of {path, score} dicts."""
    results = []
    for i, path in enumerate(image_paths):
        print(f"[qa] {i + 1}/{len(image_paths)}: {os.path.basename(path)}")
        try:
            score = qa_image(path, product=product)
            verdict = "PASS" if score.get("pass") else "FAIL"
            issues = score.get("issues", [])
            issues_str = f" — {', '.join(issues)}" if issues else ""
            print(f"[qa]   {verdict}{issues_str}")
            results.append({"path": path, "score": score})
        except Exception as e:
            print(f"[qa]   ERROR: {e}")
            results.append({"path": path, "score": None, "error": str(e)})
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python qa.py <image-path>")
        sys.exit(1)
    score = qa_image(sys.argv[1])
    print(json.dumps(score, indent=2))
