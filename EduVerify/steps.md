# steps.md — EduVerify build order

> Read `agents.md` first. This file is the **order of work**: which prompt each team pastes, what it does, how to check it, and when teams must sync.
> Full prompt texts are in `prompts/team-a-frontend.md`, `prompts/team-b-backend.md`, `prompts/team-c-ai.md`.

Teams: **A = Frontend**, **B = Backend**, **C = AI / Data engine**.

---

## How to use a prompt (every team, every time)

1. `git pull --rebase origin main`, create branch `a/…`, `b/…` or `c/…`.
2. In Antigravity paste your team's **MASTER** prompt (once per workspace), then the next numbered prompt.
3. Agent workflow: **Brainstorm → Plan (checklist) → Work → Review**. If the skills exist: `/ce-brainstorm` → `/ce-plan` → `/ce-work` → `/caveman` (terse output). Use a Haiku-class model for research/reading docs, a Sonnet-class model for coding and review.
4. Agent finishes by running tests and printing the **localhost link**. Open it and do the "Check" step listed below.
5. Open a PR (Conventional Commit title, plan checklist in description). One reviewer from your team; contract files need the owner + one other team.
6. Squash-merge. If the step has a 🏷 tag, the lead tags `main`.

---

## Phase 0 — Project lead setup (30 min, before any team starts)

The lead (one person) does this on `main` so no team ever edits root files:

```bash
mkdir eduverify && cd eduverify && git init
mkdir -p frontend backend engine data/master data/demo docs demo reports/templates infra contracts/schemas prompts .github/workflows
cp <kit>/agents.md <kit>/steps.md <kit>/runthrough.md . && cp <kit>/prompts/*.md prompts/
```

`.gitattributes`
```
* text=auto eol=lf
*.xlsx binary
*.png binary
*.pdf binary
```

`.gitignore`
```
.env
.venv/
__pycache__/
*.pyc
node_modules/
dist/
.DS_Store
data/synthetic/
data/raw/
*.sqlite3
playwright-report/
test-results/
```

`.editorconfig` (2 spaces for TS/JSON/YAML, 4 for Python, LF, final newline).

`.github/CODEOWNERS`
```
/frontend/            @team-a
/docs/                @team-a
/demo/                @team-a
/reports/templates/   @team-a
/.github/workflows/frontend.yml @team-a
/backend/             @team-b
/infra/               @team-b
/render.yaml          @team-b
/docker-compose.yml   @team-b
/.env.example         @team-b
/contracts/openapi.yaml  @team-b
/contracts/schemas/      @team-b
/.github/workflows/backend.yml  @team-b
/.github/workflows/security.yml @team-b
/engine/              @team-c
/data/                @team-c
/contracts/rule_catalog.yaml     @team-c
/contracts/column_synonyms.yaml  @team-c
/.github/workflows/engine.yml    @team-c
/agents.md /steps.md /runthrough.md /prompts/ /.github/CODEOWNERS @lead
```

GitHub settings: protect `main` (PR required, CODEOWNERS review, squash only, linear history), create labels `contract-change`, `team-a`, `team-b`, `team-c`.

Then each team starts its prompt 0 **in parallel**.

---

## Sync points (integration milestones)

| Tag | Who creates it | Contents | Who waits for it |
|---|---|---|---|
| 🏷 `contracts-v0.1` | B (after B0) + C (after C0) | `openapi.yaml` v0.1, `schemas/`, `rule_catalog.yaml` v0.1, `column_synonyms.yaml` | A starts real types (`gen:api`), all teams code to it |
| 🏷 `data-v0.1` | C (after C1) | `data/master/*`, `data/demo/*` | B2 seeding |
| 🏷 `api-v0.1` | B (after B1) | Auth live | A1 switches login from MSW to real API |
| 🏷 `engine-v0.1` | C (after C2) | `suggest_mapping`, `validate_batch` signatures frozen, parser + first rules | B3 upload pipeline (Phase 4) |
| 🏷 `api-v0.5` | B (after B4) | Upload, review, lifecycle endpoints real | A2–A4 turn off mocks for those pages |
| 🏷 `engine-v0.5` | C (after C5) | dedup, drift, anomaly, reconciliation, rollover preview | B7 wires rollover; B bumps engine pin |
| 🏷 `api-v1.0` | B (after B6) | Credentials + verify | A6 |
| 🏷 `engine-v1.0` | C (after C6) | DQ comparison + exports | B7 wires dq-comparison |

Teams bump their engine pin whenever a new engine tag lands. Rules grow behind a frozen API, so a bump never breaks the backend.
| 🏷 `rc-1` | Lead | All teams' last prompts merged | Full `runthrough.md` rehearsal, Render deploy (B8) |

**Daily 10-minute sync:** each team states: merged yesterday, next prompt, blocked on which tag. Contract-change PRs reviewed first.

---

## Phase plan at a glance

| Phase | Team A — Frontend | Team B — Backend | Team C — AI/Data | Sync at end |
|---|---|---|---|---|
| 1 | A0 Scaffold + mocks + i18n | B0 Scaffold + OpenAPI + Render/infra | C0 Engine scaffold + catalog + synonyms | `contracts-v0.1` |
| 2 | A1 Login + RBAC routing | **B1 AUTH** | C1 Master + synthetic data | `api-v0.1`, `data-v0.1` |
| 3 | A2 Upload + column mapping | B2 DB + master + mock registry | C2 Parser + smart mapping + minimal validate_batch | `engine-v0.1` |
| 4 | A3 Review workspace | B3 Upload pipeline + SSE + commit | C3 Explainable rule engine | — |
| 5 | A4 Lifecycle/transfers/aggregates/webhooks UI | B4 Review, lifecycle, transfers, reconciliation | C4 Fuzzy dedup | `api-v0.5` |
| 6 | A5 AICTE console | B5 Consent + audit + PII | C5 Anomaly + drift + reconciliation | `engine-v0.5` |
| 7 | A6 Student wallet + verifier + certificate | B6 SD-JWT VC + verify + QR | C6 Before/after DQ report | `api-v1.0`, `engine-v1.0` |
| 8 | A7 Reports + docs + demo + E2E | B7 Webhooks + notifications + dashboards + reports API | C7 Hardening + perf | — |
| 9 | Bug-fix + a11y | B8 Hardening + Render deploy | Support + eval numbers | `rc-1` |

Teams never block each other inside a phase: A uses MSW mocks, B uses Team C's tagged engine or a stub, C uses its own dev harness.

---

## Team C — AI / Data (prompts in `prompts/team-c-ai.md`)

| Step | What the prompt does | Done-check | Localhost |
|---|---|---|---|
| **C0** Scaffold | Creates `eduverify_engine` package, Pydantic models for BatchReport/Issue (incl. reason, evidence, suggested_fix, priority, bucket), masking helpers, `rule_catalog.yaml` (V001–V035, versioned), `column_synonyms.yaml`, dev harness, CI. | `GET /catalog` lists 35 rules; pytest green | http://localhost:8100/docs |
| **C1** Master + synthetic data | Produces master tables (LGD states/districts, institutions, DABs, programs, academic years, enums) and a deterministic generator for registry, intake, declared totals, central snapshot, history, transfers, plus 4 demo batches with seeded defects and ground truth. | Same seed → same hash; batch_1 has 0 errors | http://localhost:8100/docs → POST /validate |
| **C2** Parser + mapping | String-only reading (keeps leading zeros), encoding detection, Indian date policy (never MM/DD), Excel-mangled ID detection, name normalisation, smart column mapping (synonyms → fuzzy → value sniffing) with confidence, and a minimal `validate_batch` so Team B can start the pipeline. 🏷 `engine-v0.1` | PRN/DOB/Dept map ≥ 0.9; "03/04/2026" = 3 Apr | http://localhost:8100/docs → POST /map |
| **C3** Rule engine | One function per rule, metadata from the catalog, explainable issues with evidence and safe suggested fixes, priority + confidence buckets, Deequ-style metrics and quality score. Precision/recall vs ground truth. | Recall ≥ 0.95 deterministic rules; every issue has reason + evidence | http://localhost:8100/docs → POST /validate batch_2 |
| **C4** Dedup | Blocking + Jaro-Winkler/token-set/phonetic comparison, per-field match explanation, thresholds 0.92 / 0.75, intra and cross-institution, transfer-aware (no false V010 for approved transfers). | "Rahul S. Sharma" ≈ "Rahul Sharma" found; twins not auto-flagged | http://localhost:8100/docs → POST /validate batch_3 |
| **C5** Monitoring intelligence | Batch profiles, schema drift (V028–V030), anomaly detection (z-score + IsolationForest, V020), reconciliation vs declared totals (V022), rollover preview (V034). | batch_4 shows drift + NRI spike | http://localhost:8100/docs → POST /validate batch_4 |
| **C6** DQ report | Before/after comparison, XLSX/JSON export, evaluation script with precision/recall/runtime → `data/eval/RESULTS.md`. Version 1.0. | XLSX opens with all sheets | http://localhost:8100/report/demo.xlsx |
| **C7** Hardening | 50k-row performance within 512 MB, property/fuzz tests, docs, clean `pip install ./engine`. | < 60 s, < 400 MB | http://localhost:8100/healthz |

## Team B — Backend (prompts in `prompts/team-b-backend.md`)

| Step | What the prompt does | Done-check | Localhost |
|---|---|---|---|
| **B0** Scaffold + contract | Writes `openapi.yaml` v0.1 for every endpoint group first, JSON schemas, FastAPI skeleton with `/healthz`, settings, logging with PII filter, docker-compose (db, mailpit), `render.yaml` Blueprint, CI + security workflows. | Spec validates; `/healthz` ok | http://localhost:8000/healthz · http://localhost:8000/docs |
| **B1** 🔐 **AUTH** | Users, argon2id passwords, login → 15-min access JWT + rotating refresh cookie with reuse detection, lockout + rate limit, optional TOTP for admins, institution API keys (hashed, scoped), RBAC dependencies for all 7 roles, hash-chained audit of security events, seed users, security headers. | Role × endpoint matrix test green; refresh reuse revokes family | http://localhost:8000/docs → login → Authorize → `/v1/auth/me` |
| **B2** Data model | All tables, field encryption, master data + demo seeding, mock APAAR registry adapter, Excel template generator (APAAR as Text, dropdowns, Hindi instructions). | Template downloads; seed idempotent | http://localhost:8000/v1/templates/student-upload.xlsx |
| **B3** Upload pipeline | Upload with idempotency, mapping confirm, resumable validation jobs calling the engine, SSE events, issues API, commit with lock + version check, corrections create new record versions. | Concurrent commit → one 409; batch_1 commits | http://localhost:8000/docs → POST /v1/batches |
| **B4** Review + lifecycle | Issue decisions (approval required), revalidate + score delta, duplicate resolution, lifecycle transitions, transfer request/approve/override, aggregate-only submissions, reconciliation + coverage, rollover (stubbed until `engine-v0.5`). | Approved transfer → no V010 | http://localhost:8000/docs → GET /v1/duplicates |
| **B5** Privacy + audit | Consent ledger with effects on credentials and PII, audit chain verify endpoint, masking rules per role, retention job, THREAT_MODEL.md. | Tampered row detected | http://localhost:8000/docs → GET /v1/audit/verify-chain |
| **B6** Credentials | Ed25519 issuer keys, did:web, trust list, SD-JWT VC issue with holder `cnf`, status list (revoked/superseded/suspended), nonce + verify, QR, certificate PDF. | Issue → present subset → VALID; correction → SUPERSEDED | http://localhost:8000/.well-known/did.json |
| **B7** Integration + analytics | Webhook registration + HMAC delivery + retries, notifications outbox (Mailpit), bulk export, dashboard endpoints, report jobs (PDF/XLSX), and finishes rollover + before/after comparison on the new engine tags. | Email visible in Mailpit; webhook test delivers | http://localhost:8000/docs · http://localhost:8025 |
| **B8** Ship | Schemathesis full run, bandit/pip-audit/ZAP, indexes + perf, env separation, migration strategy, backup/restore, Render deploy + smoke script. | Smoke script passes on Render URL | http://localhost:8000/healthz → Render URL |

## Team A — Frontend (prompts in `prompts/team-a-frontend.md`)

| Step | What the prompt does | Done-check | Localhost |
|---|---|---|---|
| **A0** Scaffold | Vite + React + TS + Tailwind + shadcn, generated API types, MSW mocks with realistic BatchReport, bilingual shell, shared badges (priority, bucket, masked value, score gauge), CI. | Shell + Hindi toggle; build passes | http://localhost:5173 |
| **A1** Login | Login with lockout/MFA states, in-memory tokens + refresh, role guards and home redirects, API-key and user settings. | Token not in localStorage | http://localhost:5173/login |
| **A2** Upload wizard | Template download, dropzone, column-mapping confirm with confidence, SSE progress with polling fallback, result summary with intake, reconciliation and drift. | batch_2 maps PRN/DOB/Dept | http://localhost:5173/institution/upload |
| **A3** Review workspace | Priority-sorted issue queue with buckets, explainable issue drawer (reason, evidence, suggested fix), approve/propose flow, duplicate side-by-side, re-validate and before/after report, guarded commit. | Score improves after fix | http://localhost:5173/institution/batches/demo-2/review |
| **A4** Institution ops | Student lifecycle timeline + allowed transitions, transfers in/out, aggregate-only form, webhooks settings, institution dashboard. | Only allowed transitions shown | http://localhost:5173/institution/transfers |
| **A5** AICTE console | KPIs, official-boundary map with tile fallback, leaderboards, quota breakdown, cross-dupe queue, anomaly/drift feed, reconciliation, audit chain badge, rollover wizard. | Live ticker updates on commit | http://localhost:5173/aicte |
| **A6** Trust UIs | Student consent + WebCrypto holder key + selective-share builder + QR; verifier scan/paste result; DAB issuance; certificate/report HTML templates. | Shared 2 fields → verifier shows only 2 | http://localhost:5173/student · http://localhost:5173/verify |
| **A7** Finish | Report builder, literature review, architecture + user guide, demo script + pitch outline, Playwright E2E, accessibility pass. | E2E green | http://localhost:5173/reports |

---

## Running everything locally (after Phase 1)

```bash
cp .env.example .env
docker compose up -d db mailpit
pip install -r backend/requirements.txt && pip install -e "./engine[dev]"
cd backend && alembic upgrade head && python -m app.seed --if-empty && uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm ci && npm run gen:api && npm run dev
```

Links: app http://localhost:5173 · API http://localhost:8000/docs · mail http://localhost:8025 · engine harness http://localhost:8100/docs (Team C only).

---

## Deploying to Render (B8, but works from Phase 1)

1. Push `main` to GitHub. In Render: **New → Blueprint** → pick the repo (`render.yaml` at root).
2. Fill `sync:false` secrets: `JWT_SECRET`, `FERNET_KEY`, `ISSUER_KEYS_JSON`, `PEPPER`, `SEED_PASSWORD`, `SMTP_*`.
3. Set `CORS_ORIGINS` and `FRONTEND_URL` on the API to the static site URL; set `VITE_API_URL` on the static site to the API URL; redeploy the static site (Vite bakes env at build time).
4. Check `https://<api>.onrender.com/healthz`, then run `infra/smoke.sh https://<api>.onrender.com`.
5. Before the demo: wake the API (free instances sleep after 15 min), confirm the free DB has not passed 30 days.

**Why this won't break on Render:** port from `$PORT`, migrations in start command, no local disk, no Redis, engine installed from repo path, splink optional, Python pinned, SPA rewrite configured, secrets from env.

---

## Final rehearsal (rc-1)

Walk through `runthrough.md` end-to-end on the Render URL with all 7 roles. Any step that fails becomes a bug for the owning team. Record a backup video of the demo.
