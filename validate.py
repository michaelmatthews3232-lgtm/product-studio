"""
Phase 1 smoke test.

Run a single template against a single reference image, generate three
variations, and save them. Open them and judge honestly: would an Etsy
soap seller pay $10 for these?

If yes — proceed to Phase 2 (run.py for the full pipeline).
If no — the technology may not be ready for your specific product. Try
adjusting guidance_scale, try a different reference photo, or try the
prep.py background removal step first. See docs/build-guide.md Phase 1
for fallback options.
"""

import os
import sys
from datetime import datetime
import requests
from dotenv import load_dotenv

import fal_client

from templates import get_template

load_dotenv()

# The template used for the smoke test. Pick the one most likely to
# produce evaluable output. barnwood_lavender is the cleanest cozy
# composition with the most familiar staging.
SMOKE_TEMPLATE_NAME = "barnwood_lavender"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python validate.py <path-to-product-image>")
        print("Example: python validate.py inputs/test-soap.jpg")
        sys.exit(1)

    reference_path = sys.argv[1]
    if not os.path.exists(reference_path):
        print(f"ERROR: file not found: {reference_path}")
        sys.exit(1)

    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("ERROR: FAL_KEY not set in .env (see .env.example)")
        sys.exit(1)
    os.environ["FAL_KEY"] = fal_key

    template = get_template(SMOKE_TEMPLATE_NAME)
    print(f"\n=== Phase 1 smoke test ===")
    print(f"Template: {template['name']}")
    print(f"Reference: {reference_path}\n")

    print("[validate] uploading reference to Fal...")
    image_url = fal_client.upload_file(reference_path)
    print(f"[validate]   uploaded: {image_url}\n")

    print("[validate] generating 3 variations (this takes ~30-60s)...")
    result = fal_client.subscribe(
        "fal-ai/flux-pro/kontext",
        arguments={
            "prompt": template["prompt"],
            "image_url": image_url,
            "guidance_scale": 3.5,
            "num_images": 3,
            "output_format": "jpeg",
        },
        with_logs=True,
    )

    # Save outputs to a timestamped folder for easy review
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", f"validate_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[validate] saving outputs to {output_dir}/")
    for i, img in enumerate(result["images"]):
        filename = f"{template['name']}_v{i + 1}.jpg"
        filepath = os.path.join(output_dir, filename)
        response = requests.get(img["url"], timeout=60)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"[validate]   saved {filename}")
        print(f"             remote: {img['url']}")

    print(f"\n=== Smoke test complete ===")
    print(f"Open {output_dir}/ and review.")
    print()
    print("Honest evaluation:")
    print("  1. Does the soap look like YOUR soap (color, shape, label)?")
    print("  2. Does the scene look professionally photographed?")
    print("  3. Would an Etsy seller pay $10 for any of these images?")
    print()
    print("If yes to all three: proceed to `python run.py <reference>`")
    print("If no: see docs/build-guide.md Phase 1 for fallback options")


if __name__ == "__main__":
    main()
