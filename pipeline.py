"""
Pipeline orchestrator: wires brief parsing, generation, and QA together.

This is the function the dashboard (when it exists) and the CLI both call.
"""

import os
import json
import zipfile
from datetime import datetime
from typing import Optional

from parse_brief import parse_brief
from generate import generate_batch
from qa import qa_batch
from templates import COZY_RUSTIC_TEMPLATES


def run_full_pipeline(
    reference_image: str,
    output_root: str = "output",
    buyer_message: Optional[str] = None,
    variations_per_template: int = 2,
    skip_qa: bool = False,
    templates: Optional[list] = None,
    product: str = "soap",
) -> dict:
    """
    Run the full pipeline end-to-end.

    Args:
        reference_image: path to the buyer's product photo
        output_root: parent directory for all batch outputs
        buyer_message: optional free-text message; if provided, runs brief parsing
        variations_per_template: how many variations per scene
        skip_qa: skip the automated QA pass (useful for fast iteration on templates)
        product: product type key (soap, candle, staging) — used for QA scoring

    Returns:
        dict with keys: batch_id, output_dir, brief, generations, qa_results
    """
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(output_root, batch_id)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n=== Batch {batch_id} ===")
    print(f"Output: {output_dir}\n")

    # Stage 1: parse brief (optional)
    brief = None
    if buyer_message:
        brief = parse_brief(buyer_message)
        # Persist the brief alongside the outputs for reference
        with open(os.path.join(output_dir, "brief.json"), "w") as f:
            json.dump(brief, f, indent=2)

    # Stage 2: generate scenes
    generations = generate_batch(
        reference_image_path=reference_image,
        output_dir=output_dir,
        templates=templates if templates is not None else COZY_RUSTIC_TEMPLATES,
        variations_per_template=variations_per_template,
    )

    # Stage 3: automated QA
    qa_results = []
    if not skip_qa and generations:
        print()
        image_paths = [g["path"] for g in generations]
        qa_results = qa_batch(image_paths, product=product)

        # Merge QA scores back into the generation records
        path_to_score = {r["path"]: r for r in qa_results}
        for gen in generations:
            qa_record = path_to_score.get(gen["path"])
            if qa_record:
                gen["qa"] = qa_record.get("score")

    # Persist a manifest for the dashboard / Mike's review
    manifest = {
        "batch_id": batch_id,
        "output_dir": output_dir,
        "reference_image": reference_image,
        "brief": brief,
        "generations": generations,
    }
    with open(os.path.join(output_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # Zip the output folder for easy Fiverr delivery
    zip_path = output_dir + ".zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(output_dir):
            if fname.endswith(".jpg"):
                zf.write(os.path.join(output_dir, fname), fname)
    print(f"Delivery zip: {zip_path}")

    print(f"\n=== Batch {batch_id} complete ===")
    print(f"Outputs: {output_dir}")
    if not skip_qa and qa_results:
        passes = sum(
            1 for r in qa_results
            if r.get("score") and r["score"].get("pass")
        )
        print(f"QA: {passes}/{len(qa_results)} passed automated review")

    return manifest
