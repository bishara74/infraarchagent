# Codex task — Phase 9h: Usable setup — accounts, provider keys, models, thinking mode, persistence, DB tooling

Fresh session. Read `AGENTS.md`, `docs/design-deviations.md` (D-40 to D-49),
the latest `docs/IMPLEMENTATION_LOG.md` entries, the supervisor's checkpoint-4
audit (`docs/reviews/checkpoint4-audit.md`), `backend/app/core/config.py`,
the LLM adapters (`backend/app/llm/`), the Phase 9g session auth (D-49,
`deps.py`, sessions table), the review decision records (D-47), the DB models
and migrations, `docker-compose.yml`, and the frontend API client, login
gate, stores and settings. Phases 0–9g are complete.

## Why this phase exists

The supervisor asked for: database inspection with pgAdmin, API-key
management with keys **encrypted in the database**, the LLM API protocol
(OpenAI-compatible), model list/selection, a clear description of the agent
harness's tool calls, and client-side data persistence. After seeing the
Phase 9g login he added (verbatim): *"model selection is needed and thinking
mode, etc. This isnt very user friendly as API keys are a pain to obtain …
the committee will see it."*

So this phase is about a **usable first-run experience**: a normal user must
not need to know or paste a backend `API_KEY`, must be guided to obtain one
provider key, and must be able to pick models and thinking mode per agent
from the UI. Security properties from 9g (HttpOnly cookie, hashed sessions,
CSRF checks) stay unchanged.

## Rules

No real LLM calls (mocked HTTP only), no `.env` reads or edits, no push. The
author authorises **one** dependency if not already locked: `cryptography`
(AES-GCM); check the lockfile first and report. Password hashing must use the
standard library (`hashlib.scrypt`) — no other new dependencies or downloads,
except the pgAdmin image reference in compose (the author pulls it). One
commit per section, prefix `phase9h:`, requirement IDs, implementation-log
entries with real test counts. Plan mode first: report section 0 before code
changes. Strict readiness, blocking criteria and the 9g label rules are
unchanged.

## 0. Investigate (report first)

Current secret handling (LLM key and `API_KEY` from `.env`, canaries,
`SecretStr`); how adapters build requests (chat-completions format,
`response_format`, `reasoning` / effort, usage); where models and reasoning
effort are configured per role; what `/models` on OpenRouter returns that is
useful (e.g. `supported_parameters` such as `reasoning`,
`structured_outputs`/`response_format`, context length, pricing) — from
documentation in the repo or mocked fixtures only; what the frontend stores
today; DB roles; and how the 9g login screen and session flow work.

## 1. User accounts instead of a shared key in the browser

- Table `users`: id, username (unique, case-insensitive), password hash
  (`hashlib.scrypt` with per-user salt and stored parameters), role
  (`admin` | `reviewer`), created_at, last_login_at, disabled_at.
- **First-run setup:** if no user exists, the UI shows "Create admin
  account" (username + password, minimum length, confirmation). Allowed only
  from 127.0.0.1 or with the configured `API_KEY` (so a fresh exposed
  instance cannot be claimed by a stranger); document this.
- Login with username + password → the existing 9g session cookie (sessions
  now reference a user). Same rate limit, constant-time behaviour, generic
  errors, CSRF/Origin checks, idle/absolute expiry.
- Admin can create/disable reviewer accounts and reset passwords in a small
  UI page; users can change their own password.
- **Review decisions record the authenticated user** (id + username)
  instead of a self-declared name when a user session exists; keep the D-47
  "self-declared (shared-key authentication)" path only for header/API-key
  and local-mode decisions. Migration keeps historical decision records
  untouched.
- `API_KEY` stays for scripts, the benchmark and first-run bootstrap; the
  browser never needs it after setup. Local open mode (9g) unchanged.
- Tests: setup only once and only from allowed origins, password hashing
  parameters, wrong password, disabled user, role checks, session ↔ user
  binding, decision provenance (user vs. self-declared), canaries.

## 2. Provider credentials, encrypted in the database, entered in the UI

- Table `provider_credentials`: id, provider, label, base_url, ciphertext,
  nonce, key_version, last4, created_by, created_at, last_used_at,
  revoked_at. AES-256-GCM with a master key from `CREDENTIAL_ENCRYPTION_KEY`
  (env only, base64 32 bytes, never stored in the DB); associated data binds
  provider + id; key-version field; `make rotate-credential-key` script.
- If `CREDENTIAL_ENCRYPTION_KEY` is missing: the UI explains how to create
  one (one command), and credential storage is disabled with a clear message
  — never fall back to plaintext.
- UI (admin): "LLM provider" settings page with a **guided setup**: short
  explanation of what a provider key is, a direct link to where to create an
  OpenRouter key, paste field, **Test** button (calls `/models` or `/key`,
  shows OK / invalid / no credit), label, revoke. Shows last4 only.
- API (authenticated, admin): create, list (metadata + last4), test,
  revoke, select default. Plaintext is never returned, logged, put in events,
  archives or errors; decrypted only in memory for a call.
- Precedence: selected DB credential → `.env` LLM key (fallback) → none
  (UI prompts setup). Document it.
- Tests: round trip, wrong master key, tampered ciphertext/AAD, revoked key,
  rotation, missing master key, no plaintext anywhere (canaries), DB holds
  only ciphertext.

## 3. Model selection and thinking mode per agent

- Backend endpoint listing models from the provider (`GET {base_url}/models`),
  cached with TTL, using the selected credential; works offline from a
  configured static list. For each model expose: id, name, context length,
  pricing, and capability flags derived from `supported_parameters`
  (structured output, reasoning). Models without structured-output support
  are shown but marked unsuitable for Generator/Fixer roles.
- Per-run selection for **Architect, Generators, Fixer**: model and
  **thinking mode** (`off`, `low`, `medium`, `high`, mapped to the existing
  reasoning settings; disabled for models without reasoning support).
  Defaults from settings; the UI shows the defaults and an estimated cost
  range from the pricing fields where possible.
- Validate selections server-side against the list and capabilities; record
  model + thinking mode per role in the run, events, archive and benchmark
  environment.
- UI: a settings panel on the new-request page (collapsed by default, with
  "use defaults"), plus an admin defaults page.
- Tests with mocked `/models` responses: capability filtering, invalid
  selections, thinking mode on a non-reasoning model rejected, offline mode,
  recording in run/archive.

## 4. Client-side persistence

- `localStorage` (try/catch, versioned schema): prompt draft, selected
  models/thinking modes, recent run list (id, title, time, status), UI
  preferences, last received SSE `seq` per run so a reload resumes without
  gaps or duplicates.
- Never store passwords, API keys or provider credentials in the browser.
- A "Recent runs" view that reopens runs from the stored list (and the
  server's run list for the logged-in user where available).
- Tests (Vitest + one Playwright reload/resume test).

## 5. pgAdmin and a read-only role

- Compose service `pgadmin` under a `tools` profile, bound to 127.0.0.1,
  credentials from `.env` placeholders (`.env.example` updated), plus a
  pre-configured server entry.
- Migration adding a read-only DB role (SELECT only) for inspection.
- README: `make db-tools`, how to view runs/packages/events/users, and what
  the encrypted credential column and password hashes look like.

## 6. Agent harness tool-call documentation

`docs/agent-tools.md`: for every agent, each tool invocation (Checkov, Trivy,
terraform init/validate/fmt, helm, ansible, promtool, schema index,
deterministic repairs, templates, LLM calls), who decides to call it
(harness vs model), inputs, outputs, limits and failure handling; a Mermaid
sequence diagram. State explicitly that the LLMs do not call tools themselves
(harness-driven tool use) and what native function calling would change.

## 7. UX pass for the committee demo

- One consistent settings/navigation structure (New request, Recent runs,
  Settings: Provider, Models, Users, Account).
- Empty states and errors that tell the user what to do next (no provider
  key → link to setup; no credit → explain; invalid model → choose another).
- Keyboard accessible, readable at 1280×800; no new UI framework.
- Playwright flow: first-run setup → add provider key (mocked) → choose
  models/thinking → submit → review with authenticated name.

## 8. Docs and finish

D-50 (accounts), D-51 (encrypted provider credentials), D-52 (model and
thinking-mode selection), D-53 (client persistence), README (first-run
guide with screenshots placeholders), thesis follow-ups. Finish with
`make lint`, `make test`, `make frontend-test`, `make test-e2e`,
`make secret-scan`, `make bench-stub` (real counts). Summary in the
`AGENTS.md` §10 format, starting with the section 0 findings.
