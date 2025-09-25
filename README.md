
# NEkropol Projector (skeleton)

Entertainment-only **Projector** agent skeleton using **FastAPI + LangGraph** with an **OpenAI** wrapper and **Hypercorn** as the ASGI runner.



```bash
# 1) Create and activate venv (pick one)
python -m venv .venv && source .venv/bin/activate
# or use uv
# pip install uv && uv venv && source .venv/bin/activate

# Check out if you agree to install deps from 'pyproject.toml'
# if you are unfamiliar with next command
# 2) Install deps
pip install -e .

# 3) Configure environment
cp .env.example .env
# edit .env with your OPENAI_API_KEY (and optional base url, model names, etc.)

# 4) Run
hypercorn -k uvloop app.main:app
# or prod-ish
# hypercorn app.main:app --bind 0.0.0.0:8000 --workers 2
```

Then:
- `GET /health` — health check.
- `POST /chat` — main entry. Provide `{ "message": "...", "image_url": "..." }` (image_url optional).
- `POST /chat/continue` - entry for continuing some unfinished chat, for example, if photo is unclear  

## Why Hypercorn?

Hypercorn plays nice with uvloop and could later host guardrails/middleware enforcing output policies.

## Rough Flow

1. **Router** classifies the message into one of:
   - `PERSON_PHOTO` (image-based projection, checked by [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet))
   - `PERSON_METADATA` (name/creds/nickname; later we’ll enable search)
   - `CASUAL` (hi/hello/weather/etc. — handled by a cheap local path)
   - `OUT_OF_SCOPE` (heavy/forbidden asks → canned NEkropol reply)
2. **LangGraph** stitches: `classify → branch handler → Projector prompt (if needed)`
3. **OpenAI wrapper** centralizes model calls (easy to swap providers later).
4. **Trace** is returned to the client so you can stream/visualize agent steps later.

## OpenAI setup + budgeting

- Create an account at OpenAI and add billing. Set a **hard monthly limit** and a **soft usage alert** in the Usage page.
- Put your key in `.env`:
  ```env
  OPENAI_API_KEY=sk-...redacted...
  OPENAI_BASE_URL=   # optional; set if using a proxy gateway
  OPENAI_MODEL_GPT=gpt-4o-mini   # cheap/vision-capable default
  OPENAI_MODEL_CHEAP=gpt-4o-mini # same by default
  ```
- For research, load a small pre-paid balance and raise it slowly. Start with \$10–\$25.

## Project structure

```
projector/
  app/
    main.py                # FastAPI app, routes
    settings.py            # typed settings via pydantic-settings
    deps/
      openai_client.py     # OpenAI wrapper
    routers/
      health.py
      chat.py
  agents/
    base.py                # LangGraph state & assembly
    router.py              # message classifier
    projector_agent.py     # projector branch logic
    prompts/
      projector_system.md  # entertainment-only system prompt
      project_prompt.md    # put your global project_prompt.md here (foundation)
  tools/
    *                      # There was idea for a lot of tools
    *                      # But sadly I don't have time for their implementation
    *                      # If you're curious you can play around
  schemas/
    types.py               # Pydantic models
  .env.example
  pyproject.toml
  README.md
  .gitignore
```

## Next steps (roadmap)

- **Guardrails:** moderation/regex/policy assertions before returning.
- **Search tool:** add Bing/SerpAPI + caching layer.
- **Streaming:** SSE/WebSocket with step-by-step progress events.
- **Image upload:** multipart/form-data and local object-store.
- **Local embeddings:** small on-disk KB for casual Q&A.
- **Tracing/metrics:** Prometheus counters, request ids, timing.
- **Auth & quotas:** per-user rate limits and usage budgets.
- **Sandboxed python:** separate process + time+mem limits.
- **Sandboxed rust:** separate process + time+mem limits.

This project uses the YuNet model from OpenCV Zoo (Apache License 2.0). My own glue code is under MIT.