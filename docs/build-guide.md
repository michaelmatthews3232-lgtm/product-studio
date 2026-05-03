# AI Soap Photography Agent — Build Guide

A complete step-by-step plan to go from zero to a working AI agent that produces professional soap product photos for Etsy/Shopify sellers, monetized via Fiverr.

**Total time estimate:** 15–25 hours of focused work, realistic across 3–4 weekends.

**End state:** You can take a buyer's product photos + brief, run a script, review outputs in a simple dashboard, and ship a batch of 5 polished product shots in under 30 minutes of active time.

---

## Phase 0 — Setup and accounts (1–2 hours)

### 0.1 Pick your aesthetic lane

Pick one. Don't try to offer all three from day one.

- **Clean / minimal** — white marble, neutral linens, soft daylight, lots of whitespace. Easiest to nail with AI. Broadest buyer appeal. **Recommended starting point.**
- **Cozy / rustic** — wood surfaces, dried botanicals, warm afternoon light, natural textures. Higher emotional appeal for handmade buyers, slightly harder to keep consistent.
- **Moody / luxe** — dark backgrounds, dramatic side lighting, gold or brass props. Premium positioning, smaller buyer pool, harder to make AI deliver consistently.

**Default to clean/minimal unless you have strong reason otherwise.**

### 0.2 Create accounts and grab API keys

You need three services. All offer pay-as-you-go with no minimum.

1. **Fal.ai** — for Flux Kontext (reference-conditioned image generation)
   - Sign up at fal.ai
   - Add $20 in credits to start
   - Get your API key from the dashboard
2. **Photoroom** — for product background removal
   - Sign up at photoroom.com/api
   - Free tier covers your testing; paid tier ~$0.05/call when you launch
3. **Anthropic** — for Claude (brief parsing + QA)
   - Sign up at console.anthropic.com
   - Add $10 in credits
   - Get API key
   - *(Alternative: OpenRouter at openrouter.ai if you want one key for multiple LLM providers. Same code pattern, just different base URL.)*

### 0.3 Set up secure key storage

This is non-negotiable. Never commit keys to git, never paste them in chat, never put them in client-side code.

Create a project folder and a `.env` file:

```bash
mkdir soap-agent
cd soap-agent
git init
touch .env .gitignore
```

In `.gitignore`:
```
.env
__pycache__/
*.pyc
.venv/
output/
inputs/
```

In `.env`:
```
FAL_KEY=your_fal_key_here
PHOTOROOM_KEY=your_photoroom_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

Confirm `.env` is git-ignored before your first commit. Run `git status` and verify `.env` doesn't show up.

### 0.4 Install Python and dependencies

You can do this on Mac or Windows — both work fine.

```bash
python3 -m venv .venv
source .venv/bin/activate    # Mac/Linux
# OR on Windows:
# .venv\Scripts\activate

pip install requests python-dotenv pillow anthropic fal-client colorthief
```

---

## Phase 1 — Validate the core technology (30 minutes)

Before building anything, prove that Flux Kontext can actually preserve your buyer's soap while restyling the scene. If this doesn't work, the whole plan needs rethinking.

### 1.1 Get a test soap image

Take a photo of any bar of soap you have at home. Phone camera is fine. Get reasonable lighting and a plain background. If you don't have soap, use any small bottled product — the test is whether the model preserves the actual product, not the category.

Save it as `inputs/test-soap.jpg`.

### 1.2 First Flux Kontext call

Create `validate.py`:

```python
import os
import fal_client
from dotenv import load_dotenv

load_dotenv()
os.environ["FAL_KEY"] = os.getenv("FAL_KEY")

# Upload your reference image
image_url = fal_client.upload_file("inputs/test-soap.jpg")
print(f"Reference uploaded: {image_url}")

# Generate a styled scene with the product preserved
result = fal_client.subscribe(
    "fal-ai/flux-pro/kontext",
    arguments={
        "prompt": "professional product photograph of this exact soap bar resting on a white marble surface, soft natural window light from the left, sprigs of dried lavender beside it, shallow depth of field, minimalist aesthetic, magazine-quality composition",
        "image_url": image_url,
        "guidance_scale": 3.5,
        "num_images": 3,
        "output_format": "jpeg",
    },
    with_logs=True,
)

for i, img in enumerate(result["images"]):
    print(f"Output {i+1}: {img['url']}")
```

Run it: `python validate.py`

Open the three output URLs. Honest evaluation:
- **Does the soap look like *your* soap?** (Same color, same shape, same swirls, same label?)
- **Does the scene look professionally photographed, not AI-generated?**
- **Would an Etsy seller pay $10 for this?**

If yes to all three: you have a working core. Continue.

If no: try adjusting `guidance_scale` (higher = more prompt adherence, lower = more reference adherence). Try Nano Banana via Fal as a backup. If neither works for your test product, the technology may not be ready for *your specific category* — pause and reassess.

**Verify current model names on Fal.ai** before assuming `fal-ai/flux-pro/kontext` is correct. Models churn; check the dashboard.

---

## Phase 2 — Minimum end-to-end script (2–4 hours)

Now build the smallest version of the full pipeline. No UI, no QA, no Firebase. Just a script that takes input and produces a folder of outputs.

### 2.1 Project structure

```
soap-agent/
├── .env
├── .gitignore
├── inputs/
│   └── test-soap.jpg
├── output/
├── templates.py
├── prep.py
├── generate.py
└── run.py
```

### 2.2 Define scene templates

In `templates.py`, encode 3 starter scenes for your aesthetic. These are your gig's product. Spend time on these.

```python
# Clean/minimal aesthetic — starter set of 3 templates
CLEAN_TEMPLATES = [
    {
        "name": "marble_morning",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "resting on a white carrara marble surface, soft natural window "
            "light from the upper left, single small sprig of fresh eucalyptus "
            "to the right, minimal composition, lots of negative space, "
            "shallow depth of field, soft realistic shadows, magazine quality"
        ),
    },
    {
        "name": "linen_flatlay",
        "prompt": (
            "overhead flat-lay product photograph of this exact bar of soap "
            "on rumpled cream linen fabric, soft diffused daylight, dried "
            "chamomile flowers scattered loosely, minimalist apothecary "
            "aesthetic, neutral color palette, professional editorial styling"
        ),
    },
    {
        "name": "white_pedestal",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "centered on a small white ceramic pedestal, plain off-white "
            "background, soft studio lighting, clean editorial styling, "
            "single soft shadow, minimal and luxurious"
        ),
    },
]
```

### 2.3 Background removal (optional but recommended)

In `prep.py`:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def remove_background(image_path: str, output_path: str) -> str:
    """Remove background from product image using Photoroom API."""
    url = "https://sdk.photoroom.com/v1/segment"
    headers = {"x-api-key": os.getenv("PHOTOROOM_KEY")}

    with open(image_path, "rb") as f:
        files = {"image_file": f}
        response = requests.post(url, headers=headers, files=files)

    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path
```

You don't strictly need this for Flux Kontext — it can work with the original photo. But a clean cutout often improves how well the model preserves the product. Test both ways.

### 2.4 Generation logic

In `generate.py`:

```python
import os
import fal_client
import requests
from dotenv import load_dotenv
from templates import CLEAN_TEMPLATES

load_dotenv()
os.environ["FAL_KEY"] = os.getenv("FAL_KEY")

def generate_batch(reference_image_path: str, output_dir: str,
                   templates=CLEAN_TEMPLATES, variations_per_template: int = 2):
    """Generate scene variations for a product."""
    os.makedirs(output_dir, exist_ok=True)
    image_url = fal_client.upload_file(reference_image_path)

    results = []
    for template in templates:
        result = fal_client.subscribe(
            "fal-ai/flux-pro/kontext",
            arguments={
                "prompt": template["prompt"],
                "image_url": image_url,
                "guidance_scale": 3.5,
                "num_images": variations_per_template,
                "output_format": "jpeg",
            },
            with_logs=False,
        )

        for i, img in enumerate(result["images"]):
            filename = f"{template['name']}_v{i+1}.jpg"
            filepath = os.path.join(output_dir, filename)
            response = requests.get(img["url"])
            with open(filepath, "wb") as f:
                f.write(response.content)
            results.append({
                "template": template["name"],
                "variation": i + 1,
                "path": filepath,
            })
            print(f"  saved {filename}")

    return results
```

### 2.5 Orchestrator

In `run.py`:

```python
import sys
from generate import generate_batch

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <path-to-product-image>")
        sys.exit(1)

    reference = sys.argv[1]
    print(f"Generating batch from {reference}...")
    results = generate_batch(reference, output_dir="output")
    print(f"\nDone. {len(results)} images saved to ./output/")
```

### 2.6 Test the pipeline

```bash
python run.py inputs/test-soap.jpg
```

Open `./output/` and review all 6 images. You should see 3 scenes × 2 variations each. Quality check honestly. If outputs look amateur, the issue is almost always the prompt — refine the templates before moving on.

**Spend real time here.** This phase is where the gig's quality is born. Iterate the templates until you'd genuinely pay $10 each for these images.

---

## Phase 3 — Scene template library (2–3 hours)

You shipped 3 templates. Now expand to 6–8 and verify consistency across multiple test products.

### 3.1 Add more scenes

Add to `templates.py`. For clean/minimal, target scenes like:

- `marble_morning` — marble + eucalyptus (already done)
- `linen_flatlay` — linen flat-lay (already done)
- `white_pedestal` — pedestal shot (already done)
- `wood_minimal` — pale wood plank with single dried flower
- `bath_corner` — corner of a clean tub with soap and folded white towel
- `paper_wrap` — soap partially unwrapped from kraft paper, on plain surface
- `stacked_set` — three identical bars stacked, top-down
- `botanical_garnish` — soap with a small herb sprig matching the scent

Each prompt should be ~50–80 words and follow the same structure: "professional product photograph of this exact bar of soap [scene description] [lighting] [styling props] [aesthetic descriptors]."

### 3.2 Test consistency across products

Round up 3–4 different soap-shaped products from your house (real soap if you have it, otherwise small bars of anything). Run each through the full template library.

Look for:
- Are all 8 scenes recognizably *your aesthetic* across different products?
- Do the same templates produce reliably good output, or are some templates flaky?
- Does the model warp the product shape on certain templates?

Cull or rewrite templates that fail consistently. You'd rather have 5 reliable templates than 8 hit-or-miss ones.

### 3.3 Add the style anchor for batch consistency

When generating 5 images for one buyer, you want them to feel like one shoot — same general lighting temperature, same color grading. Two ways to enforce this:

- **Same seed family** — use a fixed seed offset across the batch (e.g. seed 1000 for image 1, 1001 for image 2, etc.). Modify `generate.py` to accept a `seed_base` parameter and pass it to Fal.
- **Reference style image** — pre-generate one "style anchor" image for each aesthetic that captures the lighting and mood. Some Flux variants accept a style reference. Test this once your templates are tuned.

Don't over-engineer this in Phase 3. A consistent prompt structure plus same time-of-day descriptors ("soft morning light") gets you 80% of the way.

---

## Phase 4 — Brief parsing and automated QA (2–3 hours)

Now add the LLM brain at the front and back of the pipeline.

### 4.1 Brief parsing

When a Fiverr buyer messages you, they'll write something like:

> "Hi, I have a small candle and soap shop on Etsy. I want photos of my new lavender oatmeal soap bar. I want bright, clean photos for my website. Need 5 different shots if possible. Here's an image of the soap."

You want an LLM to convert that into a structured brief.

In `parse_brief.py`:

```python
import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PARSE_PROMPT = """You are extracting a structured brief from a Fiverr buyer's message
about product photography. Return ONLY valid JSON, no other text.

Required fields:
- product_type: short string (e.g. "lavender oatmeal soap bar")
- num_images: integer (default 5 if not specified)
- aesthetic_hint: one of "clean", "cozy", "moody", or "unspecified"
- requested_scenes: array of strings if buyer specified scenes, else []
- special_requests: array of any unusual requirements
- notes: short summary in plain language

Buyer message:
---
{message}
---"""

def parse_brief(buyer_message: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-5",  # verify current model name
        max_tokens=500,
        messages=[{"role": "user", "content": PARSE_PROMPT.format(message=buyer_message)}],
    )
    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
```

*(Note: verify the current Sonnet model identifier in Anthropic's docs at the time you build. Model names update.)*

### 4.2 Automated QA

After generation, send each output back to a vision LLM with the buyer's brief and ask: does this image meet the brief and pass quality standards?

In `qa.py`:

```python
import os
import base64
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

QA_PROMPT = """You are reviewing AI-generated product photography. Score this image
1-10 on these criteria and respond ONLY in JSON:

- product_fidelity: does the soap look like a real, coherent product?
- composition: professional photography composition?
- lighting: realistic, professional lighting?
- artifact_free: any AI weirdness, warped shapes, garbled text on label?

Also include:
- pass: boolean, true if this image is deliverable to a paying buyer
- issues: array of short strings describing any problems

Return ONLY JSON."""

def qa_image(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data,
                }},
                {"type": "text", "text": QA_PROMPT},
            ],
        }],
    )

    import json
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
```

### 4.3 Wire it into `run.py`

```python
from parse_brief import parse_brief
from qa import qa_image
from generate import generate_batch

def run_full_pipeline(buyer_message: str, reference_image: str, output_dir: str):
    print("Parsing brief...")
    brief = parse_brief(buyer_message)
    print(f"  Brief: {brief['notes']}")

    print("Generating batch...")
    results = generate_batch(reference_image, output_dir)

    print("QA pass...")
    for r in results:
        score = qa_image(r["path"])
        r["qa"] = score
        verdict = "PASS" if score["pass"] else "FAIL"
        print(f"  {r['template']} v{r['variation']}: {verdict}")
        if not score["pass"]:
            print(f"    issues: {', '.join(score['issues'])}")

    return brief, results
```

The QA pass is your safety net, not your final filter. You still review every batch yourself before delivery.

---

## Phase 5 — Approval dashboard (4–6 hours)

Now build the simplest possible web UI to review batches and approve outputs. This is what you'll use during actual orders.

### 5.1 Stack

- **Next.js** (App Router) deployed to Vercel
- **Firebase Storage** for output images
- **Firebase Firestore** for batch metadata
- **Tailwind** for styling

You're already on this stack from your other projects.

### 5.2 Minimum dashboard features

The MVP dashboard has exactly these screens:

- **New Batch** — paste buyer message, upload reference image, hit Generate. Server runs the pipeline, stores outputs in Firebase Storage, creates a Firestore doc with metadata.
- **Batch Review** — grid of all generated images for that batch. Each tile shows the image, QA score, and three buttons: Approve, Reject, Regenerate. Approve marks for delivery; Reject hides; Regenerate triggers a new variation of that template.
- **Delivery Bundle** — once you've approved 5 (or however many the buyer ordered), one button packages them as a zip with consistent filenames (`product_name_01.jpg`, etc.) and gives you a download link.

That's it. Don't add user auth, don't add multi-user support, don't add billing tracking. You can run this locally for the first 20 orders and not need any of that.

### 5.3 Backend handler

The Next.js API route receives the brief and reference, kicks off the Python pipeline (or a Node port — your call), and writes results to Firebase. If you want to keep the Python pipeline as-is, expose it as a small FastAPI service deployed somewhere like Fly.io or Railway. If you want everything in Node, port `generate.py` to use the Fal.ai Node SDK — it's a 1:1 mapping.

For your first 5 orders, *don't even build the dashboard*. Just run the Python script locally, eyeball outputs in Finder/Explorer, and email the buyer the good ones. Build the dashboard once you've actually shipped a few orders and know what friction matters.

---

## Phase 6 — Fiverr launch (2–3 hours)

Now sell.

### 6.1 Read Fiverr's AI disclosure rules

Fiverr requires you to disclose AI-generated work in your gig description and tags. Skipping this gets gigs removed. Read their current AI content policy before listing — rules update.

### 6.2 Gig setup

- **Title:** "I will create AI product photos for your Etsy soap or skincare shop"
- **Category:** Graphics & Design > Product Photography (or AI Artists if Fiverr's structure has changed — pick the closest match)
- **Tags:** ai product photography, soap photography, etsy product photos, skincare photography, ai mockup
- **Description structure:**
  - One-line hook ("Professional AI-generated product photos for handmade soap and skincare brands")
  - Who it's for (Etsy sellers, indie skincare brands, small soap makers)
  - What they get (X high-res images, Y scene variations, branded for your shop)
  - Disclosure ("Images are AI-generated using your product photos as the source — your actual products, restyled into professional scenes")
  - Process (send product photos → I create scenes → revisions included → final files delivered)
  - Why you (consistency across batches, [your aesthetic style], fast turnaround)

### 6.3 Gig images — eat your own dog food

Use your agent to create the gig portfolio. Run 3–5 of your favorite soap photos through the pipeline, pick the best 8 outputs, and make those your gig portfolio images. This is your most important sales asset. Spend an afternoon getting it right.

### 6.4 Pricing tiers

Start *slightly* below market to land first reviews, then raise.

| Tier | Price | What |
|------|-------|------|
| Basic | $35 | 3 images, 1 scene type, 1 revision |
| Standard | $75 | 5 images, 3 scene types, 2 revisions |
| Premium | $150 | 10 images, 5 scene types, unlimited revisions, 24h delivery |

After 10 reviews, raise basic to $50, standard to $100, premium to $200. Sellers with strong reviews can charge meaningfully more than new sellers.

### 6.5 First-week routine

- Reply to messages within 1 hour during business hours (Fiverr's algorithm rewards response time heavily)
- Take any order under $50 even if it's barely worth it — you're buying reviews, not revenue, in week one
- After delivery, politely ask for a review: "If you were happy with the work, a quick review really helps small sellers like me — no pressure either way"

---

## Phase 7 — First 10 orders and iterate (ongoing)

The first 10 orders teach you everything the build process couldn't.

Things to track for each order:
- Buyer's actual brief vs. what your parser extracted (gaps reveal prompt improvements)
- How many images you had to regenerate before you got 5 approvable ones (lower is better; high regen rate means template tuning needed)
- Time from order receipt to delivery (target: under 6 hours active, under 24h elapsed)
- Buyer feedback verbatim (themes will emerge — they want X, you assumed Y)

Things to build next based on what you learn:
- More scene templates if buyers consistently ask for one you don't have
- Batch-level brand color extraction (extract a 3-color palette from the buyer's existing shop and bias scenes toward it)
- A "rebrand" upsell — same product, multiple aesthetics, for sellers refreshing their entire shop
- Monthly retainer offering — "I'll do all your new product photos for $300/mo, up to 6 products" — this is where this category quietly becomes good money

---

## What this becomes (the bigger play)

After ~30–50 orders, you'll have:
- A tuned template library that produces consistent professional output
- A working dashboard with Firebase persistence
- Real customer feedback on what styles convert
- A small portfolio of public Fiverr reviews

That's the foundation for the actual product. Take the agent, wrap it in a self-serve UI ("upload your product → pick a style pack → get 10 scenes for $19/month"), and list it on Utility Haven or as a standalone micro-SaaS. The Fiverr gig becomes the proof point and acquisition channel; the SaaS is the scalable business.

The gig is the wedge. The agent is the product.

---

## Quick reference — what to build in what order

1. ✅ Pick aesthetic, create accounts, set up keys (Phase 0)
2. ✅ Run `validate.py` with one test image — confirm Flux Kontext works (Phase 1)
3. ✅ Build minimum end-to-end Python script with 3 hardcoded templates (Phase 2)
4. ✅ Expand to 6–8 templates, test across multiple products (Phase 3)
5. ✅ Add Claude brief parser and QA pass (Phase 4)
6. ⏸️ *Skip the dashboard for first 5 orders — just run the script locally*
7. ✅ Set up Fiverr gig, write disclosure, generate portfolio images with the agent (Phase 6)
8. ✅ Take first orders, learn, iterate (Phase 7)
9. ✅ Build the dashboard once you know what friction actually matters (Phase 5)
10. ✅ After ~30 orders, decide whether to scale on Fiverr or pivot to SaaS

Don't skip ahead. Each phase produces something that informs the next.
