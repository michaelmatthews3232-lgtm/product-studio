"""
Main entry point: run the full pipeline against a reference product image.

Usage:
    # Without a buyer brief (just generate the full template library)
    python run.py inputs/customer-soap.jpg

    # With a buyer brief (parses message, generates, runs QA)
    python run.py inputs/customer-soap.jpg --message "Hi, I need 5 cozy photos for my Etsy lavender soap..."

    # Skip QA (faster iteration when tuning templates)
    python run.py inputs/customer-soap.jpg --no-qa
"""

import sys
import argparse
from pipeline import run_full_pipeline
from templates import PRODUCT_TEMPLATES


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the cozy/rustic soap photography pipeline."
    )
    parser.add_argument(
        "reference",
        help="path to the buyer's product photo (e.g. inputs/customer-soap.jpg)",
    )
    parser.add_argument(
        "--message",
        default=None,
        help="optional buyer brief text; runs Claude brief parsing if provided",
    )
    parser.add_argument(
        "--variations",
        type=int,
        default=2,
        help="variations per template (default: 2)",
    )
    parser.add_argument(
        "--no-qa",
        action="store_true",
        help="skip the automated QA pass",
    )
    parser.add_argument(
        "--output-root",
        default="output",
        help="parent directory for outputs (default: output)",
    )
    parser.add_argument(
        "--product",
        default="soap",
        choices=list(PRODUCT_TEMPLATES.keys()),
        help="product type — selects the matching scene templates (default: soap)",
    )
    args = parser.parse_args()

    templates = PRODUCT_TEMPLATES[args.product]

    try:
        run_full_pipeline(
            reference_image=args.reference,
            output_root=args.output_root,
            buyer_message=args.message,
            variations_per_template=args.variations,
            skip_qa=args.no_qa,
            templates=templates,
            product=args.product,
        )
    except KeyboardInterrupt:
        print("\n[run] interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[run] FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
