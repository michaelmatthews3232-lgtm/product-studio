"""
Scene generation via Flux Kontext on Fal.ai.

This is the heart of the agent. Flux Kontext takes a reference image
(the buyer's actual soap) and a scene prompt, and renders the real
product into a styled scene. This reference-conditioning is what
prevents the agent from hallucinating fake soap that doesn't match
what the buyer sells.
"""

import os
import requests
from typing import Optional
import fal_client
from dotenv import load_dotenv

from templates import COZY_RUSTIC_TEMPLATES

load_dotenv()

# Fal.ai's client picks this up from the env automatically.
# Verify the model identifier on fal.ai dashboard before production —
# model paths drift over time.
FLUX_KONTEXT_MODEL = "fal-ai/flux-pro/kontext"


def _ensure_fal_key() -> None:
    """Fal client reads from FAL_KEY env var. Surface a clear error if missing."""
    if not os.getenv("FAL_KEY"):
        raise ValueError(
            "FAL_KEY not set. Add it to .env (see .env.example)."
        )
    # fal_client reads this from env at call time
    os.environ["FAL_KEY"] = os.getenv("FAL_KEY")


def generate_one(
    reference_image_url: str,
    prompt: str,
    num_images: int = 2,
    guidance_scale: float = 3.5,
    seed: Optional[int] = None,
) -> list[dict]:
    """
    Generate N variations for a single template prompt.

    Args:
        reference_image_url: a Fal-hosted URL (returned from fal_client.upload_file)
        prompt: the full scene prompt
        num_images: variations to generate (cost scales linearly)
        guidance_scale: higher = more prompt adherence, lower = more reference adherence.
            3.5 is a sensible default for product photography. Try 2.5–4.5 range.
        seed: optional fixed seed for reproducibility / batch consistency

    Returns:
        list of dicts with at least 'url' key (the hosted output image URL)
    """
    _ensure_fal_key()

    arguments = {
        "prompt": prompt,
        "image_url": reference_image_url,
        "guidance_scale": guidance_scale,
        "num_images": num_images,
        "output_format": "jpeg",
    }
    if seed is not None:
        arguments["seed"] = seed

    result = fal_client.subscribe(
        FLUX_KONTEXT_MODEL,
        arguments=arguments,
        with_logs=False,
    )
    return result["images"]


def generate_batch(
    reference_image_path: str,
    output_dir: str,
    templates: Optional[list[dict]] = None,
    variations_per_template: int = 2,
    guidance_scale: float = 3.5,
    seed_base: Optional[int] = None,
) -> list[dict]:
    """
    Run the full template library against a single product reference.

    Args:
        reference_image_path: local path to the buyer's product photo
        output_dir: directory to write outputs (will be created if missing)
        templates: defaults to COZY_RUSTIC_TEMPLATES; pass a subset to filter
        variations_per_template: how many variations per scene
        guidance_scale: passed to Flux Kontext
        seed_base: if set, each template gets a deterministic seed offset for
            batch consistency. None = random seeds, more variety but less coherent.

    Returns:
        list of result dicts with 'template', 'variation', 'path', 'remote_url'
    """
    _ensure_fal_key()

    if templates is None:
        templates = COZY_RUSTIC_TEMPLATES

    os.makedirs(output_dir, exist_ok=True)

    print(f"[generate] uploading reference: {reference_image_path}")
    reference_url = fal_client.upload_file(reference_image_path)

    results: list[dict] = []
    for t_idx, template in enumerate(templates):
        seed = (seed_base + t_idx * 100) if seed_base is not None else None
        print(
            f"[generate] template {t_idx + 1}/{len(templates)}: "
            f"{template['name']} (seed={seed})"
        )

        try:
            images = generate_one(
                reference_image_url=reference_url,
                prompt=template["prompt"],
                num_images=variations_per_template,
                guidance_scale=guidance_scale,
                seed=seed,
            )
        except Exception as e:
            print(f"[generate]   FAILED: {e}")
            continue

        for v_idx, img in enumerate(images):
            filename = f"{template['name']}_v{v_idx + 1}.jpg"
            filepath = os.path.join(output_dir, filename)
            try:
                response = requests.get(img["url"], timeout=60)
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"[generate]   saved {filename}")
                results.append({
                    "template": template["name"],
                    "variation": v_idx + 1,
                    "path": filepath,
                    "remote_url": img["url"],
                })
            except Exception as e:
                print(f"[generate]   download failed for v{v_idx + 1}: {e}")

    print(f"[generate] done — {len(results)} images saved to {output_dir}")
    return results
