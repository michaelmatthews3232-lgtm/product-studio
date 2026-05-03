# Soap Agent — Cozy/Rustic AI Product Photography

An AI agent that takes a buyer's soap photo + brief and produces professional cozy/rustic product photography for Etsy and Shopify sellers.

**Status:** Phase 0–2 scaffolded. Templates curated for cozy/rustic aesthetic. Brief parsing and QA stubbed but functional. Dashboard not built (intentionally — see build guide).

---

## Quick start

```bash
# 1. Set up Python environment
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API keys
cp .env.example .env
# then edit .env and fill in the three keys

# 4. Drop a test soap photo into inputs/
# (any bar of soap or small product, phone camera fine)

# 5. Smoke test — confirms Flux Kontext works for your product
python validate.py inputs/your-soap.jpg

# 6. Once validate.py outputs look good, run the full batch
python run.py inputs/your-soap.jpg
```

Outputs land in `output/<timestamp>/`.

---

## Project layout

```
soap-agent/
├── README.md              you are here
├── CLAUDE.md              context for Claude Code — read this in the terminal
├── .env.example           template; copy to .env and fill in
├── .gitignore
├── requirements.txt
├── templates.py           cozy/rustic scene prompts (the heart of the product)
├── prep.py                background removal via Photoroom
├── generate.py            Flux Kontext via Fal.ai
├── parse_brief.py         Claude-powered brief parser
├── qa.py                  Claude vision QA pass
├── pipeline.py            orchestrator that wires everything together
├── validate.py            Phase 1 smoke test — single template, single product
├── run.py                 full pipeline entry point
├── inputs/                drop reference product photos here
├── output/                generated outputs land here, organized by timestamp
└── docs/
    └── build-guide.md     full 7-phase build plan
```

---

## API keys you need

Three accounts, all pay-as-you-go with no minimums:

| Service | Used for | Approx cost |
|---|---|---|
| Fal.ai | Flux Kontext image generation | ~$0.04 per image |
| Photoroom | Background removal (optional) | ~$0.05 per call |
| Anthropic | Brief parsing + QA via Claude | ~$0.15 per order |

**Never commit `.env`.** Confirmed git-ignored — verify with `git status` before your first commit.

---

## Where to start

1. Read `CLAUDE.md` to orient Claude Code on the project.
2. Read `docs/build-guide.md` for the full 7-phase plan.
3. Run `validate.py` against one of your own bars of soap. If the output is great, you're ready to start tuning templates. If not, that's a Phase 1 problem — see the build guide.

---

## Working with Claude Code

Open this folder in VS Code, then run `claude` in the integrated terminal. Claude Code will pick up `CLAUDE.md` automatically and have all the context it needs to help you extend templates, debug API calls, build the dashboard, or anything else.

Useful first prompts to try:
- "Walk me through templates.py and explain the prompt structure"
- "Run validate.py against inputs/foo.jpg and tell me if the output is gig-quality"
- "Add a ninth cozy template for [specific scene idea]"
- "Help me port generate.py to Node so I can integrate it into a Next.js dashboard"
