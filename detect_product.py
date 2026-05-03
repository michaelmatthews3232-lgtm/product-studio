"""
Auto-detect what type of product is in a photo.
Routes to Gemini Flash via OpenRouter — cheap vision, one-word reply.
"""

import os
import base64
from model_router import routed_vision
from dotenv import load_dotenv

load_dotenv()

DETECT_PROMPT = """Look at this image and identify what type of product or scene it shows.

Return ONLY one of these exact strings, nothing else:
- soap (bar soap, handmade soap, bath soap, any kind of soap bar)
- candle (jar candle, pillar candle, taper candle, wax melt, any candle)
- staging (empty room, unfurnished interior space, room with minimal or no furniture)
- jewelry (rings, necklaces, earrings, bracelets, pendants, any wearable accessory)
- unknown (cannot determine, or none of the above)

Reply with only the single word. No explanation, no punctuation."""


def detect_product_type(image_path: str) -> str:
    """
    Detect the product type in an image using Gemini Flash via OpenRouter.

    Args:
        image_path: local path to an image file (JPEG or PNG)

    Returns:
        one of: soap, candle, staging, jewelry, unknown
    """
    ext = os.path.splitext(image_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        media_type = "image/jpeg"
    elif ext == ".png":
        media_type = "image/png"
    elif ext == ".webp":
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"

    with open(image_path, "rb") as f:
        image_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    try:
        result = routed_vision(
            task="detect",
            image_b64=image_b64,
            media_type=media_type,
            prompt=DETECT_PROMPT,
            max_tokens=10,
        )
        result = result.strip().lower()
        valid = {"soap", "candle", "staging", "jewelry"}
        return result if result in valid else "unknown"
    except Exception as e:
        print(f"[detect] Error: {e}")
        return "unknown"
