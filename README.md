# CLR — Cognitive Load Reducer

An AI-powered "cognitive firewall" that sits between you and the flood of notifications, emails, and micro-decisions of modern life. It filters out noise, rewrites messages into plain language, summarizes what matters, and scores how much mental bandwidth your inbox is actually costing you.

## What it does

- **Filters** incoming messages and notifications, dropping low-value noise
- **Rewrites** messages into simpler, shorter language
- **Summarizes** content so you don't have to read the whole thing
- **Predicts** what you actually need to know or do next
- **Auto-handles** low-stakes decisions instead of surfacing them
- **Scores** your current "mental bandwidth" load (0–100)
- **Suggests** concrete ways to reduce cognitive load right now

A Gmail inbox integration runs real email through the full pipeline (filter → summarize → rewrite → bandwidth score) so you can see the effect on actual messages, not just demo data.

## Tech stack

- Python 3 / FastAPI
- Local LLM via an OpenAI-compatible endpoint (Ollama, model configurable)
- Vanilla JS + Tailwind for the UI (no build step)

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env           # then edit as needed
```

Required: an OpenAI-compatible chat endpoint running locally (e.g. [Ollama](https://ollama.com)) with the model set in `.env` (`CLR_MODEL`, default `mistral-nemo`).

### Gmail integration (optional)

The Email tab fetches your inbox over IMAP (read-only) using a Gmail **app password** — no Google Cloud project or OAuth setup required.

1. Enable 2-Step Verification on your Google account
2. Generate an app password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. In Gmail, go to **Settings → Forwarding and POP/IMAP** and enable IMAP access
4. Set `CLR_GMAIL_ADDRESS` in `.env`
5. Run `python main.py` — it will prompt for the app password at the terminal (never written to disk)

Once configured, CLR fetches new mail automatically in the background (every 15 minutes by default) — the Fetch Emails button in the Email tab still works for an on-demand check. Tune this with `CLR_AUTO_FETCH_ENABLED` (`true`/`false`) and `CLR_AUTO_FETCH_INTERVAL_MINUTES` in `.env`.

## Running

```bash
python main.py
```

Then open `http://localhost:8000`.

## Testing

```bash
pytest
```