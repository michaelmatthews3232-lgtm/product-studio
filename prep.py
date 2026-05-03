"""
Product image prep: background removal via Photoroom API.

Optional in the pipeline — Flux Kontext can work with the original photo,
but a clean cutout often improves how well the model preserves the product.
Test both ways with your specific products.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def remove_background(image_path: str, output_path: str) -> str:
    """
    Remove background from a product image using Photoroom API.

    Args:
        image_path: path to the source image
        output_path: where to write the cutout (PNG with transparency)

    Returns:
        the output_path on success

    Raises:
        ValueError if PHOTOROOM_KEY is not set
        requests.HTTPError if the API call fails
    """
    api_key = os.getenv("PHOTOROOM_KEY")
    if not api_key:
        raise ValueError(
            "PHOTOROOM_KEY not set. Add it to .env "
            "(see .env.example for reference)."
        )

    url = "https://sdk.photoroom.com/v1/segment"
    headers = {"x-api-key": api_key}

    with open(image_path, "rb") as f:
        files = {"image_file": f}
        print(f"[prep] removing background from {image_path}...")
        response = requests.post(url, headers=headers, files=files, timeout=60)

    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"[prep] saved cutout to {output_path}")
    return output_path


if __name__ == "__main__":
    # Quick standalone test: python prep.py inputs/test-soap.jpg
    import sys
    if len(sys.argv) < 2:
        print("Usage: python prep.py <image-path>")
        sys.exit(1)

    src = sys.argv[1]
    dst = src.rsplit(".", 1)[0] + "_cutout.png"
    remove_background(src, dst)
