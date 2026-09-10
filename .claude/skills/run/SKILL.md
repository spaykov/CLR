---
description: Launch and drive the CLR FastAPI server for manual or automated testing.
---

# Run — Cognitive Load Reducer

## Prerequisites

The server requires Ollama running locally with `mistral-nemo` pulled. Start it with:

```bash
ollama serve
```

The virtual environment must be present (`.venv/`). If missing:

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
```

## Run

Launch the dev server in the background:

```bash
cd "D:/Code/Carter/2ndClaudeExperiment"
.venv/Scripts/python.exe main.py &> /tmp/clr.log &
SERVER_PID=$!
```

Wait for it to be ready, then verify:

```bash
for i in {1..20}; do
  curl -sf http://localhost:8000/api/v1/health && break
  sleep 1
done
# → {"status":"ok"}
```

## Auto-reload

`main.py` runs uvicorn with `reload=True` and `reload_includes=[".env", "*.html", "*.js", "*.css"]`,
so the running dev server restarts itself on changes to `.py`, `.env`,
`.html`, `.js`, or `.css` files (uvicorn's default only watches `.py`).
Anything outside that list, and the one-time interactive Gmail
app-password prompt at startup, still needs a manual stop/restart.

## Key endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | Health check (no API key needed) |
| POST | `/api/v1/summarize` | Summarize a block of text |
| POST | `/api/v1/rewrite` | Simplify text to plain language |
| POST | `/api/v1/filter/notification` | Evaluate a notification for importance |
| POST | `/api/v1/decide` | Auto-handle a low-stakes decision |
| POST | `/api/v1/process` | Full pipeline: filter → summarize → rewrite |
| POST | `/api/v1/process/batch` | Batch pipeline + bandwidth score + advisor |

Interactive docs: `http://localhost:8000/docs`

## Quick smoke test

```bash
# Health (no Ollama needed)
curl http://localhost:8000/api/v1/health

# Summarize (requires Ollama running)
curl -s -X POST http://localhost:8000/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Please review the attached 47-page quarterly compliance report by end of day."}'
```

## Environment variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `CLR_OLLAMA_BASE_URL` | No | `http://localhost:11434/v1` | Ollama endpoint |
| `CLR_MODEL` | No | `mistral-nemo` | Ollama model to use |
| `CLR_HOST` | No | `0.0.0.0` | Bind address |
| `CLR_PORT` | No | `8000` | Port |
| `CLR_LOG_LEVEL` | No | `info` | `debug` / `info` / `warn` / `error` |
| `CLR_AUTO_FETCH_ENABLED` | No | `true` | Background Gmail auto-fetch on/off |
| `CLR_AUTO_FETCH_INTERVAL_MINUTES` | No | `15` | Auto-fetch polling interval |

## Stop

```bash
kill $SERVER_PID
# or if PID is lost:
pkill -f "python.exe main.py"
```

Logs are at `/tmp/clr.log`.
