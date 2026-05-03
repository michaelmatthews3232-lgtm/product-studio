# CLAUDE.md

Persistent context for Claude Code working in this repo. Read this fully before responding to any task.

---

## What this project is

An AI agent that produces professional cozy/rustic product photography for handmade soap sellers, monetized through a Fiverr gig. The buyer sends their actual soap photos and a brief; the agent uses **Flux Kontext** (reference-conditioned image generation) to render the *real product* into styled cozy/rustic scenes. Mike reviews, approves, and delivers.

The Fiverr gig is the wedge. The medium-term play is converting this into a self-serve micro-SaaS for Etsy soap and skincare sellers, listed on Mike's existing platform Utility Haven.

---

## Aesthetic lock-in: cozy / rustic

This is **not negotiable** without an explicit decision conversation. Every scene template must read as cozy/rustic. The visual vocabulary:

- **Surfaces:** weathered barnwood, reclaimed oak, aged stone, cream linen, kraft paper, handmade ceramics, stoneware
- **Lighting:** warm afternoon side light, golden hour glow, soft window light through gauzy curtain — never harsh studio strobes, never cool fluorescent
- **Props:** dried lavender bunches tied with twine, fresh herb sprigs (rosemary, thyme, eucalyptus), dried orange slices, cinnamon sticks, jute rope, amber glass apothecary bottles
- **Color palette:** warm neutrals — cream, oat, sand, terracotta, sage, dusty rose, weathered brown, soft amber
- **Mood:** farmhouse kitchen, herbal apothecary, cottagecore, slow-living, handmade — never sterile, never modern minimalist, never neon

If a buyer asks for something outside this aesthetic (e.g., "I want neon cyberpunk soap photos"), the right answer is "I can't deliver that style — my gig is specifically cozy/rustic. Here's a referral to a seller who does that style." Don't try to twist the agent into doing styles it wasn't built for.

---

## Architecture

Six-stage deterministic pipeline. Not an "agent" in the LangChain sense — just a sequence of function calls with two LLM-powered steps.

```
intake → product_prep → scene_generation → automated_qa → human_approval → delivery
 (gray)    (teal AI)       (teal AI)         (teal AI)       (coral)        (gray)
```

| Stage | Module | Tool |
|---|---|---|
| Intake / brief parsing | `parse_brief.py` | Claude (text) |
| Product prep | `prep.py` | Photoroom API |
| Scene generation | `generate.py` | Fal.ai → Flux Kontext |
| Automated QA | `qa.py` | Claude (vision) |
| Human approval | (out of scope, dashboard later) | Mike |
| Delivery | (manual for now) | Mike emails buyer |

`pipeline.py` orchestrates the whole flow. `run.py` is the CLI entry point.

---

## File-by-file purpose

- **`templates.py`** — The product moat. Eight named cozy/rustic scene templates, each with a hand-tuned ~70-word prompt. This is where Mike's quality differentiation lives. Edits here are high-leverage; edits to `generate.py` are usually plumbing.
- **`prep.py`** — Photoroom background removal. Optional in the pipeline (Flux Kontext can work with original photos), but improves product preservation when input photos are messy.
- **`generate.py`** — Calls `fal-ai/flux-pro/kontext` with the reference image and template prompt. Returns N variations per template. Core function: `generate_batch(reference_image_path, output_dir, templates, variations_per_template)`.
- **`parse_brief.py`** — Sends buyer's free-text Fiverr message to Claude, returns structured JSON brief (product type, image count, special requests, etc.).
- **`qa.py`** — Sends each generated image to Claude vision, returns scored evaluation (product fidelity, composition, lighting, artifact-free) plus boolean `pass`.
- **`pipeline.py`** — `run_full_pipeline(buyer_message, reference_image, output_dir)` orchestrates parse → generate → QA. Returns brief + scored results.
- **`validate.py`** — Phase 1 smoke test. Single template, single product, three variations. Use this to confirm Flux Kontext works for any specific product before running full batches.
- **`run.py`** — Production entry point. Takes a reference image path, generates the full template library with QA scoring, writes everything to a timestamped output folder.

---

## Coding conventions

- **Python 3.10+** assumed. Don't write code that requires 3.12 features without flagging it.
- **Type hints on function signatures**, not on every local variable.
- **No global state.** Pass config explicitly. The one exception: `dotenv` loading at module import time in scripts.
- **Print statements over logging library.** This is a small CLI tool; `logging` is overkill. Use clear emoji-free prefixes: `[generate]`, `[qa]`, etc.
- **Errors propagate.** Don't `try/except` and silently swallow — the user wants to see what failed. Wrap only when you can add useful context.
- **Function naming:** verbs (`generate_batch`, `parse_brief`, `qa_image`), not nouns.
- **No unnecessary abstraction.** Don't introduce a `BaseModel` ABC for two implementations. Don't introduce a config class for three env vars. Resist Java instincts.

---

## API key handling — strict rules

This project handles three API keys. Mike has been burned before by accidentally exposing keys in chat (the Anti-Vision incident). Strict rules:

1. **Never read or write `.env` directly in chat output.** When showing config, always reference `.env.example` or use placeholder text like `<YOUR_KEY>`.
2. **Never paste a real key into a code change.** If a snippet needs a key, use `os.getenv("FAL_KEY")`.
3. **`.env` is git-ignored.** If asked to commit, verify `.gitignore` includes `.env` first.
4. **If you ever see a real key in the conversation context, flag it immediately and recommend rotating.** Don't just acknowledge — say "rotate this key now at <provider dashboard URL>."

---

## Build phase status

Tracking progress against `docs/build-guide.md`:

- [x] **Phase 0** — Setup, accounts, key storage scaffolded
- [x] **Phase 1** — `validate.py` ready (Mike must run it with his own product photo)
- [x] **Phase 2** — Minimum end-to-end pipeline scaffolded
- [x] **Phase 3** — 8 cozy/rustic templates curated (Mike to refine after testing)
- [x] **Phase 4** — Brief parser and QA pass scaffolded
- [ ] **Phase 5** — Dashboard (deferred until first ~5 orders, per build guide)
- [ ] **Phase 6** — Fiverr gig setup, disclosure, portfolio
- [ ] **Phase 7** — First 10 orders, iteration

When Mike asks "what's next?", default to whichever phase has the earliest unchecked box.

---

## Common tasks Mike will ask for

**"Run validate.py and tell me if the output is good"**
- Execute `python validate.py inputs/<file>` if running locally
- Open the three output URLs / files
- Score honestly: product fidelity (does it look like *his* soap?), composition, lighting realism, artifact-free
- Flag specific issues with concrete recommendations: "increase guidance_scale to 4.0" or "the label is being warped — try removing background first via prep.py"

**"Add a new template for [scene]"**
- Add to `templates.py` following the existing prompt structure
- ~60–80 words per prompt
- Always start with `"professional product photograph of this exact bar of soap..."` to anchor the model on preservation
- Always end with cozy/rustic mood descriptors
- Test it before committing

**"The output looks like generic AI slop"**
- This is almost always a prompt problem, not a code problem
- Check whether the prompt is over-specifying (too many props confuse the model) or under-specifying (vague mood adjectives)
- Try removing one or two props and adding one specific lighting descriptor

**"Help me port this to Node for the Next.js dashboard"**
- Fal.ai has a JS SDK with an identical API surface
- Anthropic SDK exists for both Python and Node
- Photoroom is plain HTTP, works the same in both
- Don't recommend rewriting unless Mike explicitly wants the dashboard backend in the same runtime — Python pipeline + Node dashboard with HTTP between them is a fine architecture

**"Set up Firebase for output storage"**
- Mike already uses Firebase across his projects. Use `firebase-admin` Python SDK.
- Outputs go to a bucket like `soap-agent/{batch_id}/{template_name}_v{n}.jpg`
- Generate a signed URL for delivery, with reasonable expiry (7 days)

---

## Things to NOT do

- **Don't recommend LangChain, CrewAI, AutoGen, or any agent framework.** This is a six-step deterministic pipeline. An agent framework adds latency, cost, and debug complexity for zero benefit.
- **Don't recommend running models locally** (Ollama, ComfyUI, local Flux) unless Mike specifically asks. Hosted APIs are faster, more reliable, and the cost difference is meaningless at this scale.
- **Don't suggest building the dashboard before order #5.** This is in the build guide for a reason — premature UI optimization is the most common pitfall here.
- **Don't suggest running the full pipeline before `validate.py` passes.** Phase 1 is a real gate, not a formality.
- **Don't drift the aesthetic.** If Mike says "let's also do clean/minimal," push back: that's a separate gig with separate templates, not a feature add.
- **Don't add tests yet.** At this scale, the pipeline IS the test. Add tests when there's a dashboard with real users.

---

## Verification reminders

Some external facts in this codebase will drift over time. Re-verify when relevant:

- **Fal.ai model identifier** for Flux Kontext (currently `fal-ai/flux-pro/kontext`) — check fal.ai dashboard
- **Anthropic model identifier** for Sonnet (currently `claude-sonnet-4-5`) — check console.anthropic.com/docs/models
- **Fiverr's AI disclosure policy** — read current rules at fiverr.com before listing
- **Photoroom API endpoint** — verify at photoroom.com/api/docs

Don't assume these are current; check before any production push.

---

## Mike's context (for tone calibration)

- Experienced full-stack developer; works on Mac and Windows
- Day job: Fraud & Wire Risk Analyst at Fidelity, pivoting to Product Manager
- Has shipped multiple apps: Body Compass, Utility Haven, Noctly, Candor
- Comfortable with Python, Node, React/React Native, Firebase, Vercel
- Time-constrained; values directness over hand-holding
- Has been burned by exposed API keys before — extra cautious around credentials
- Treats projects as compounding assets, not one-offs — design choices that benefit a future SaaS pivot are valuable
