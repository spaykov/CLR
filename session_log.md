# CLR Session Log

---

## Session 1 — 2026-06-03

### Summary
Explored the current state of the Cognitive Load Reducer (CLR) codebase. The project is a fully implemented FastAPI + Claude REST API with 7 endpoints covering the full cognitive load pipeline: message filtering, summarization, rewriting, bandwidth scoring, advising, needs prediction, and auto-decision handling. All core modules exist under `clr/core/`, Pydantic models under `clr/models/`, and 4 test modules with mocked Claude calls under `tests/`.

### What was discussed
- User asked about the practical use of the app in its current state.
- Explored all source files (excluding `.venv`) to understand what had been built.
- Identified that the core AI logic is complete and functional as a REST API.
- Identified gaps: no frontend/UI, no real-world integrations (email, Slack, notifications), no persistence/database, no authentication.

### Current state verdict
The backend intelligence is in place. The missing layer is connective tissue — integrations that feed real data in, and a UI that surfaces results to the user. In its current state it's usable only by developers sending manual JSON payloads.

### Summary of what each file does
  - filter.py — sends your message to Claude and asks "does this need the user's attention?"
  - rewriter.py — sends text to Claude and asks "simplify this to under 2 sentences"
  - summarizer.py — sends text to Claude and asks "give me a one-line summary"
  - advisor.py — sends your message list to Claude and asks "suggest 3–5 ways to reduce load"
  - predictor.py — sends messages to Claude and asks "what does this user actually need to know?"
  - decision_handler.py — sends a decision to Claude and asks "should I auto-handle this?"

### Recommended Claude Code skills for this project
- **`claude-api`** *(high priority)* — Every core module calls the Anthropic SDK; this skill handles prompt caching, API optimization, and model version migration. Prompt caching not yet used but would benefit batch operations.
- **`run`** *(high priority)* — For launching the FastAPI server and verifying behavior after changes.
- **`verify`** *(high priority)* — For confirming endpoints work correctly after adding features.
- **`code-review`** *(situational)* — Worth running before significant feature additions (e.g., database layer, auth).
- **`security-review`** *(situational)* — Becomes important once real integrations (email, Slack) are added and credentials/external data are involved.

### Summary of what each file does
  - filter.py — sends your message to Claude and asks "does this need the user's attention?"                                                                                                                                
  - rewriter.py — sends text to Claude and asks "simplify this to under 2 sentences"                                                                                                                                        
  - summarizer.py — sends text to Claude and asks "give me a one-line summary"                                                                                                                                              
  - advisor.py — sends your message list to Claude and asks "suggest 3–5 ways to reduce load"                                                                                                                               
  - predictor.py — sends messages to Claude and asks "what does this user actually need to know?"                                                                                                                           
  - decision_handler.py — sends a decision to Claude and asks "should I auto-handle this?"
---

## Session 2 — 2026-06-17

### Summary
Designed and built a full web UI for CLR, served directly by FastAPI (no npm, no build step). Also began a Gmail integration using OAuth2 — backend and UI are complete, but the Google Cloud credential setup is pending for next session.

### What was built

**Web UI (`ui/`)**
- `ui/templates/index.html` — single-page shell with 6 tabs: Dashboard, Inbox, Email, Notifications, Decisions, Tools, Insights
- `ui/static/js/api.js` — central fetch layer with `ApiError`, UUID helper, 30s timeouts
- `ui/static/js/app.js` — tab navigation, health-check dot, module init
- `ui/static/js/bandwidth.js` — bandwidth score ring (color-coded clear/moderate/overloaded), batch modal
- `ui/static/js/inbox.js` — single message form, priority-colored result cards with cognitive cost dots, sessionStorage history
- `ui/static/js/notifications.js` — notification filter form, KEPT/BLOCKED result cards
- `ui/static/js/decisions.js` — dynamic options form, confidence bar, auto-decided vs needs-input result
- `ui/static/js/tools.js` — Rewrite and Summarize utility cards with copy button
- `ui/static/js/insights.js` — listens for `batchComplete` custom event, renders bandwidth report, predicted needs, suggestions, processed messages accordion
- `ui/static/js/email.js` — Gmail OAuth2 connect/fetch flow
- `ui/static/css/custom.css` — panel fade-in animation

**Backend changes**
- `main.py` — mounts `/static`, serves `index.html` via `FileResponse`
- `clr/core/email_fetcher.py` — Gmail REST API via `google-api-python-client`, token stored in `gmail_token.json`
- `clr/api/routes.py` — added `POST /email/fetch`, `GET /email/auth/url`, `GET /email/auth/callback`, `GET /email/auth/status`
- `requirements.txt` — added `jinja2`, `python-multipart`, `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`
- `.gitignore` — created; excludes `.env`, `credentials.json`, `gmail_token.json`

### Current state
The UI is fully working and served at `http://localhost:8000/`. The Gmail Email tab is wired up end-to-end but waiting on one manual step.

### Blocked / next session

**Gmail OAuth2 setup (user needs to do this once):**
1. Go to **console.cloud.google.com** → create a project
2. Enable **Gmail API**
3. Create OAuth credentials: **Web application** type, add redirect URI `http://localhost:8000/api/v1/email/auth/callback`
4. Download the JSON → rename to `credentials.json` → place in project root
5. Restart server → Email tab → **Connect Gmail** → approve Google pop-up

Once `credentials.json` is in place, the Email tab becomes fully functional: fetches the last N inbox emails, runs them through the full filter/summarize/rewrite pipeline, and populates the bandwidth score and Insights panel.

### Known issue resolved
FastAPI's `Jinja2Templates.TemplateResponse` threw `TypeError: unhashable type: 'dict'` due to a Jinja2 LRU cache bug with the installed version. Fixed by switching to `FileResponse` and hardcoding `/static/` paths in the HTML directly.

---

## Session 3 — 2026-06-24

### Summary
Replaced the pending Gmail OAuth2/GCP integration with POP3 + app-password auth (no Google Cloud project needed), got it working end-to-end against the real inbox, then put the project under version control for the first time and pushed it to GitHub.

### What was built
- `clr/core/email_fetcher.py` — rewritten to use `poplib.POP3_SSL` against `pop.gmail.com:995` instead of the Gmail REST API; parses raw MIME via the stdlib `email` module
- `clr/config.py` — added `gmail_address` / `gmail_app_password` settings (`CLR_GMAIL_ADDRESS` in `.env`; password is **not** read from `.env`)
- `main.py` — prompts for the Gmail app password via hidden `getpass` input at server startup (held in memory only, propagated to the uvicorn `--reload` worker via `os.environ`)
- `clr/api/routes.py` — removed `/email/auth/url` and `/email/auth/callback`; replaced `/email/auth/status` with `/email/status` (`{"configured": bool}`)
- `ui/templates/index.html`, `ui/static/js/email.js` — "Connect Gmail" OAuth flow replaced with a "Check Connection" button and app-password setup instructions
- Removed `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib` from `requirements.txt` and uninstalled from `.venv`
- `README.md` — written from scratch (previously a placeholder containing `123`)

### Debugging the live connection
First few attempts failed with Gmail POP3 auth errors, in order:
1. `-ERR [AUTH] Username and password not accepted` — 2-Step Verification wasn't enabled yet (required for app passwords to exist at all)
2. Same error again — had pasted an app password generated for a *different* Google account by mistake
3. `-ERR [SYS/PERM] Your account is not enabled for POP access` — POP was off in Gmail Settings → Forwarding and POP/IMAP
4. After enabling POP: success. `/api/v1/email/fetch` pulled real inbox messages and ran them through the full filter → summarize → rewrite → bandwidth → predict → suggest pipeline correctly.

### Version control
- Repo had never been a git repo. Ran `git init`, added `.idea/` and `.claude/settings.local.json` to `.gitignore` (IDE/local-only state), made the root commit.
- Remote `https://github.com/spaykov/CLR.git` already existed with one unrelated commit (a placeholder README containing `123`) on `main`. Merged with `--allow-unrelated-histories` rather than force-pushing, to avoid destroying the existing remote history.
- Push initially failed (`403`) because Windows had a cached git credential for an unrelated GitHub account (`test-S6`); cleared it via `cmdkey /delete` and the retry succeeded.
- Pushed the merge, then a follow-up commit replacing the placeholder README with a real one.

### Testing
- `POST /api/v1/email/fetch` against the live inbox — confirmed correct filtering of promotional email (Temu, inventr.io), accurate bandwidth score (100/"clear" for an all-low-value batch).
- `POST /api/v1/process/batch` with hand-crafted synthetic messages (urgent outage, meeting reminder, promo, low-stakes decision) — confirmed priority/cognitive-cost/filtering logic correctly distinguishes a critical actionable item (bandwidth score dropped to 9/"overloaded") from noise.
- Confirmed there is no server-side persistence layer — every fetch/process call is stateless; nothing is stored in a database or file.

### Current state
Gmail integration is fully working via app password. Project is version-controlled and pushed to `github.com/spaykov/CLR` (`main` branch).

### Blocked / next session
**Plan a security feature pass.** Flagged this session: there is no server-side persistence layer at all (every `/email/fetch` or `/process` call is stateless, nothing written to a database or file) — that's one candidate, but it should be scoped as part of a broader review of what security work remains, not fixed in isolation. Before writing code, draft a plan covering at least:
- Persistence layer for fetched/processed messages (what's stored, where, for how long, and whether raw email bodies should be retained at all)
- Whether `/api/v1/*` endpoints need auth now that real Gmail content flows through them (currently anyone on localhost can hit `/email/fetch`)
- Anything else `security-review` or `code-review --high` surfaces once Gmail integration + persistence are in scope

---

## Session 4 — 2026-08-19

### Summary
Implemented all three approved security-plan items except prompt-injection mitigation (persistence had already been built — found `clr/core/storage.py` + `tests/test_storage.py` on disk, untracked, at session start): API-key auth for `/api/v1/*`, then at the user's request exposed the server to the LAN, then — after the user pushed back on the key being visible to anyone who loads the page — replaced the static-key-in-page-source model with a real login/session-cookie flow.

### What was built
- `clr/config.py` — `api_key: str = ""` (`CLR_API_KEY`); default `host` tightened `0.0.0.0` → `127.0.0.1` (later reopened for this session, see below)
- `clr/api/auth.py` (new) — `require_api_key` dependency, no-op when `CLR_API_KEY` unset, same optional pattern as `gmail_app_password`
- `clr/api/routes.py` — split into `router` (all endpoints, key-gated) and `public_router` (`/health` only, exempt for monitoring)
- `tests/test_auth.py` (new) — 5 tests: no-op unset, 401 missing/wrong key, 200 correct key, `/health` always exempt
- LAN exposure (user chose "LAN only" over "public internet" when asked): `.env` set to `CLR_HOST=0.0.0.0` + a real generated `CLR_API_KEY`; `main.py` now **fails fast at startup** if host is non-loopback and the key is empty, so this can't silently regress to unauthenticated+exposed
- Frontend wired to send the key: `main.py`'s `index()` now does server-side string substitution into a `<meta name="clr-api-key">` tag (avoiding the Jinja2 `TemplateResponse` bug noted in Session 2) instead of a raw `FileResponse`; `api.js` reads it into an exported `authHeaders` and attaches it on every request
- Found and fixed 2 raw `fetch()` calls that bypassed `api.js` and would have silently 401'd once auth was live: `app.js`'s `/version` poll and `email.js`'s `/email/status` + `/email/fetch` calls

**Login/session layer (added after the key-in-page-source design was questioned):**
- `clr/core/sessions.py` (new) — in-memory `{token: expiry}` store, `create_session()`/`is_valid()`/`destroy()`, 12h TTL. Lost on process restart (including `--reload` picking up a code change) — acceptable for a single-process local/LAN tool, documented in the module.
- `clr/api/auth.py` — `require_api_key` now accepts *either* `X-API-Key` header (scripts/curl, `secrets.compare_digest`) *or* a valid `clr_session` cookie (browser), so existing programmatic access still works unchanged.
- `clr/api/routes.py` — added `POST /auth/login` (checks password against `CLR_API_KEY`, sets an `HttpOnly`/`SameSite=Lax` session cookie), `POST /auth/logout`, `GET /auth/status`. All on `public_router` since they must be reachable pre-auth.
- `main.py`'s `index()` — no longer embeds the key at all; instead checks the request's session cookie and serves `ui/templates/login.html` (new) if not authenticated, `index.html` if authenticated.
- `ui/static/js/{api,app,email}.js` — dropped the `<meta>`-tag key entirely; all `fetch()` calls now use `credentials: "same-origin"` so the cookie rides along automatically; a 401 anywhere triggers `window.location.reload()`, which bounces to the login page. Added a "Sign out" button in the header (hidden unless `auth_required`).
- `tests/test_auth.py` — 7 new tests covering login (wrong/right password, key-not-configured), logout invalidation, `/auth/status`, and that `/` serves the login page vs. the app correctly.

**Split login password from API key** (same session, right after — user noticed both were the same secret and asked for them to be independent):
- `clr/config.py` — new `login_password: str = ""` (`CLR_LOGIN_PASSWORD`), distinct from `api_key`
- `clr/api/auth.py` — `require_api_key` now gates on `api_key OR login_password` being set (either alone turns auth on); header check still only matches `api_key`, cookie check unchanged
- `clr/api/routes.py` — `/auth/login` and `/auth/status` now check/reflect `login_password`, not `api_key`
- `main.py` — index-page login gate now keys off `login_password` alone (so an `api_key`-only setup, e.g. "scripts only, no browser access", doesn't gate the SPA it can't authenticate to); LAN-exposure fail-fast check now requires *either* secret to be set, not specifically `api_key`
- `.env` — `CLR_API_KEY` kept as the existing random token (scripts); added `CLR_LOGIN_PASSWORD=pebble-cactus-amber-marble-84`, a generated 4-word+digits passphrase (user chose "memorable passphrase" over a raw token or picking their own) for typing into the login screen by hand
- `tests/test_auth.py` — updated existing tests to target the right secret, added 3 new ones proving the two are independent (API key doesn't work as login password, api_key-alone doesn't gate the SPA, login_password-alone is sufficient for session auth)

### Current state
Server running, bound to `0.0.0.0:8000`, reachable at `http://192.168.68.119:8000/` from the LAN. Loading that URL prompts for `CLR_LOGIN_PASSWORD` (currently `pebble-cactus-amber-marble-84`); `CLR_API_KEY` (`i3A43A3BVI-hwSqWqVNnNysmSlG9u2hzqvrvZzh99rI`) is the separate secret for `X-API-Key`/scripts and is not accepted at the login screen. Neither secret is ever sent to the browser as plaintext — only the resulting session cookie is, for the login path. Full end-to-end curl verification of both paths passed (see conversation). 42/42 tests passing.

**Gmail account note:** while testing, three genuine Google security alerts showed up in fetched mail ("Unauthorized App Password Created," "suspicious app password was removed," "Unexpected app password created") — almost certainly triggered by our own repeated app-password generation/testing this session (POP3→IMAP switch, auth-failure debugging), not an actual compromise, but flagged to the user to verify at `myaccount.google.com/security`.

**Insights/History became read-only-only when the user actually looked at it** (screenshot: "Processed Messages (9)," no way to act on any of it) — added, same session:
- `clr/core/storage.py` — `delete_processed(id)`, `clear_history()`
- `clr/api/routes.py` — `DELETE /history/{id}`, `DELETE /history` (both auth-gated)
- `ui/static/js/api.js` — `del()` helper, `deleteHistoryItem()`, `clearHistory()`
- `ui/static/js/insights.js` — rewrote `loadHistory()`: fetches up to 200 rows, client-side search (source/summary/filter_reason) + priority filter + kept/filtered filter, click-to-expand row detail, per-row delete, "Clear all" with a `confirm()` gate (destructive/irreversible)
- `ui/templates/index.html` — added the search/filter toolbar + "Clear all" button to the History card
- `tests/test_storage.py` + new `tests/test_history_routes.py` — 7 new tests. 49/49 passing.

**New finding while rewriting `insights.js`, fixed same session:** the old code interpolated message content (subjects, summaries, filter reasons — all attacker-reachable via email) directly into `innerHTML` with no escaping. A crafted email subject could execute JS in the user's authenticated session (stored XSS). Fixed app-wide, not just in `insights.js`:
- `ui/static/js/dom.js` (new) — single shared `escapeHtml()`, used everywhere instead of each file rolling its own
- `insights.js` — switched to the shared helper
- `inbox.js` — escaped source, category, summary, simplified, filter reason, suggested action, raw content
- `notifications.js` — escaped app name, title, simplified body, reason
- `decisions.js` — found while sweeping the rest of `ui/static/js/*.js` for the same pattern (not originally asked, same bug class): escaped the LLM's decision/reasoning text
- Confirmed already safe, no changes needed: `tools.js`, `bandwidth.js` (`.textContent` only), `email.js` (only static strings passed to `innerHTML`)

This closes item 1 from the previous entry's list.

### Blocked / next session
**Security work still open, roughly in priority order:**
1. **Prompt-injection mitigation** (item 3 from the original approved plan, never implemented) — add "treat content as untrusted data" instructions to the prompts in `filter.py`/`predictor.py`/`summarizer.py`/`rewriter.py`, plus a regex backstop in `safety.py` mirroring the existing emergency-detection pattern. Distinct from the now-fixed rendering issue: this is about the LLM's behavior, not the browser's.
2. **Rate limiting** on `/api/v1/*` — nothing currently stops a key/session holder from hammering `/process/batch` or `/email/fetch`, both of which drive Ollama load and (for email) real inbox access. Also no throttling on `/auth/login` itself (low urgency: 26 bits from the passphrase is enough to make guessing impractical over a network with no bulk-attempt tooling in play, but worth a basic attempt-limit for defense in depth).
3. **Secrets hygiene / rotation** — both `CLR_API_KEY` and `CLR_LOGIN_PASSWORD` are plaintext in `.env` (gitignored). Fine single-user; if this grows beyond one person/device, move to per-user credentials and add a rotation path.
4. **Transport security** — everything is plain HTTP on the LAN, including the session cookie and any Gmail content in transit. The session cookie is `HttpOnly` but not `Secure` (can't be, over plain HTTP). Low risk on a trusted home network, worth a TLS pass before trusting this on a less controlled network.
5. Re-run `security-review` / `code-review --high` now that auth + LAN exposure + login are all in place, since together they meaningfully change the threat model from the original assessment.

**Product/UX work flagged by the user (2026-08-19), not yet implemented:**
6. **Expand-to-view on "Processed Messages" cards** — the ephemeral batch-result accordion in Insights (populated by the `batchComplete` event, right after a fetch/batch run) shows only a one-line summary per message, no click-to-expand. History rows already got this (session 4, same day) — the batch cards should get the same treatment. Actually easier here: the batch response has `msg.original.content` available client-side (unlike History, which deliberately excludes raw content for PII reasons — see storage.py), so expansion can show the true original text, not just what's in storage. Remember to run new interpolated fields through `escapeHtml()` (`ui/static/js/dom.js`).
7. **Deleted history entries reappear on the next email fetch — root cause identified, not fixed:** `clr/core/email_fetcher.py:78` assigns every fetched email `id=str(uuid.uuid4())` — a fresh random ID on *every* fetch, not a stable identifier tied to the email itself. So re-fetching the same email (still within the "hours to look back" window) doesn't recognize it as the same message — it inserts a *new* row with a new ID via `storage.save_processed`'s `INSERT OR REPLACE`. A deleted entry isn't literally coming back; a new row representing the same underlying email is being created. Fix: derive a stable id from the email's `Message-ID` header (present on virtually all real email, fall back to a hash of from+date+subject if missing) so `INSERT OR REPLACE` naturally dedupes across fetches. **Open product question once that's fixed:** should a user-initiated delete be a true tombstone (permanently suppress that email even if fetched again), or just "remove from the list, it can come back if refetched"? These are different guarantees — worth deciding explicitly, not assuming.
8. **Manual "Fetch Emails" click vs. periodic automatic polling** — user asked whether this should be automatic instead. Worth weighing before building: needs a background scheduler (e.g. APScheduler, or a simple asyncio loop task started alongside uvicorn), interacts directly with the not-yet-built rate-limiting item (2, above) since it'd hit Gmail/Ollama on a schedule instead of on demand, and the Gmail app password would need to stay resident in memory for the server's whole lifetime (already true today, just more load-bearing if fetches are unattended). Get user's cadence preference (e.g. every 15/30/60 min) before implementing.
9. **Frontend storage strategy** — user asked about moving to `localStorage`. Currently `inbox.js` and `notifications.js` cache their own result cards in `sessionStorage` (cleared when the tab closes), which is separate from and redundant with the real backend persistence in `storage.py`/History. Worth a deliberate decision next session: (a) switch those two from `sessionStorage` to `localStorage` for cross-session persistence, (b) drop the client-side cache entirely and have Inbox/Notifications read from `GET /history` like Insights already does (single source of truth, but loses the category split — History doesn't currently distinguish "from Inbox" vs "from Notifications" vs "from Email"), or (c) leave as-is. Don't just pick (a) by default without discussing — (b) is probably architecturally cleaner given History already exists.

---

## Session 5 — 2026-08-26

### Summary
Fixed item 7 from the previous entry: message-id instability causing deleted history rows to reappear on refetch, plus the open product question (delete = tombstone vs. delete = can recur). User chose **tombstone**: a deleted message must never reappear, even if the same email is fetched again later.

### What was built
- `clr/core/email_fetcher.py` — replaced `id=str(uuid.uuid4())` (fresh random id every fetch) with `_stable_id()`: sha256 of the email's `Message-ID` header, or (rare senders that omit it) a composite of `from|date|subject`. Same email now produces the same id across fetches. Note: this can theoretically collide for two genuinely different emails from the same sender at the identical timestamp with an identical subject and no `Message-ID` — accepted as a rare edge case, strictly better than the fully-random scheme it replaces.
- `clr/core/storage.py` — new `deleted_message_ids` table (id + `deleted_at`), independent of and outliving rows in `processed_messages`. `delete_processed()` now tombstones the id when a row was actually deleted; `clear_history()` tombstones every id it clears. New `get_deleted_ids(ids)` for bulk membership checks. Deliberately *not* enforced inside `save_processed()` itself — see below.
- `clr/api/routes.py` — `/email/fetch` now calls `storage.get_deleted_ids()` on the fetched batch and filters tombstoned messages out **before** running them through the (paid/local-LLM) filter→summarize→rewrite pipeline, so a previously-deleted email is neither resurrected nor reprocessed for nothing. Response now separates `fetched` (raw count from Gmail) from the processed count, plus a new `skipped_deleted` field.
- `ui/static/js/email.js` — status message updated to show fetched vs. processed counts and call out skipped-as-deleted emails, since `fetched` and `processed.length` can now legitimately differ.
- `tests/test_storage.py` — 5 new tests for tombstone-on-delete, tombstone-on-clear, `get_deleted_ids` membership, and documenting that `save_processed()` itself does not block resurrection (that's enforced one layer up, in the route).
- `tests/test_email_fetcher.py` (new) — 4 tests proving `_stable_id` is deterministic per `Message-ID`, differs across distinct `Message-ID`s, and falls back sanely when the header is absent.
- 58/58 tests passing (was 49; +9 here).

### Design note
Tombstone enforcement lives in the `/email/fetch` route, not in `storage.save_processed()`. This was deliberate: `save_processed()` is also called from `/process/batch`, a general-purpose endpoint for arbitrary user-submitted messages, where re-submitting a previously-deleted id is a legitimate, intentional action rather than an accidental resurrection. Baking a global block into `save_processed()` would conflate the two use cases.

### Known limitation
Existing history rows created before this fix still have the old random-UUID ids, so they won't dedupe against a refetch of the same underlying email — the fix only prevents *new* duplication going forward. Not retroactively fixable without re-deriving ids from stored raw email data, which isn't persisted (see `storage.py`'s comment on why raw content is excluded).

### Blocked / next session
Renumber remaining open items from the previous entry (now: prompt-injection mitigation, rate limiting, secrets hygiene, transport security, re-run security-review, batch-card expand-to-view, manual-vs-automatic email fetch, frontend storage strategy) — item 7 (dedup) is now closed.