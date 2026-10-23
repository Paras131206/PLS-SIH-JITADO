# Team B — Backend · Antigravity prompts

> Owns ONLY: `backend/`, `contracts/openapi.yaml`, `contracts/schemas/`, `infra/`, `render.yaml`, `docker-compose.yml`, `.env.example`, `.github/workflows/backend.yml`, `.github/workflows/security.yml`.
> Paste **B-MASTER** once, then B0 … B8 in order. **B1 is the Auth prompt.** Each prompt ends with a localhost link.
> Research/doc reading → fast model (Haiku-class). Coding/review → strong model (Sonnet-class).

---

## B-MASTER (paste first, once)

```
You are the Team B (Backend) agent for EduVerify. Read agents.md, then steps.md, then this file. They are binding.
You write ONLY to: backend/, contracts/openapi.yaml, contracts/schemas/, infra/, render.yaml, docker-compose.yml, .env.example, .github/workflows/backend.yml, .github/workflows/security.yml.
Never edit engine/, data/, frontend/, docs/. You consume Team C's package with `pip install ./engine` and its data from data/master and data/demo (pinned to their tags).
Product: FastAPI backend = AICTE Central Repository + trust layer.
Stack: Python 3.11, FastAPI, SQLAlchemy 2 (typed ORM), Alembic, Pydantic v2 + pydantic-settings, psycopg 3 (Postgres 16) with SQLite for tests, PyJWT, argon2-cffi, cryptography (Ed25519, AES-GCM/Fernet), sd-jwt (OpenWallet Foundation, wrapped in app/vc/sdjwt.py), qrcode, WeasyPrint, slowapi, sse-starlette, httpx, pytest, schemathesis, ruff, bandit.
Structure: app/main.py, app/config.py, app/db.py, app/models/<area>.py, app/schemas/<area>.py, app/routers/<feature>.py (one file per feature, registered in app/routers/__init__.py — append one sorted line), app/services/<area>.py, app/security/, app/vc/, app/jobs/, app/seed.py, alembic/.
Rules:
- contracts/openapi.yaml is the source of truth; update it IN THE SAME PR as the endpoint, bump info.version. Schemathesis test must pass.
- Every endpoint declares roles with Depends(require_roles(...)); every PII read, verification and state change writes an audit row.
- Never log raw APAAR/PII (use eduverify_engine.masking).
- Render-safe (agents.md §3): bind $PORT, DATABASE_URL rewrite, no local-disk persistence, no Redis, env-based keys, CORS from CORS_ORIGINS.
- One Alembic migration per PR.
Workflow per prompt: brainstorm (3 bullets) → plan checklist → implement → pytest + ruff → review your own diff. If /ce-brainstorm, /ce-plan, /ce-work, /caveman skills exist, use them in that order. Keep output terse.
At the end of every prompt: run tests, start the API (`docker compose up -d db mailpit && uvicorn app.main:app --reload --port 8000 --app-dir backend`) and print the localhost link plus a one-line "what to click".
```

---

## B0 — Scaffold, contract-first OpenAPI, local + Render infra

```
Task B0. Scaffold the backend and publish the API contract FIRST (Team A mocks it).
1. contracts/openapi.yaml v0.1.0 (OpenAPI 3.1): all endpoint groups with request/response schemas, even if not implemented yet:
   auth (login, refresh, logout, me, password change), users, api-keys, master (states, districts, institutions, programs, academic-years, enums, DABs), templates, batches (create, list, get, mapping get/confirm, report, issues, commit, supersede, events SSE), issues (decide), corrections, duplicates (list, resolve), students (get, put, transitions), transfers, aggregates, declared-totals, reconciliation, rollover, consent, credentials (issue, list, revoke, presentation nonce), verify, .well-known/did.json, status-lists, webhooks, notifications, reports, audit (list, verify-chain), dashboards (aicte summary, institution summary, map, leaderboards, anomalies feed).
   Use component schemas mirroring agents.md §5; copy engine/schema_out/batch_report.json into contracts/schemas/batch_report.json; write contracts/schemas/enums.json (all enums from agents.md §5.1) and student_record.json, credential.json.
2. backend/: pyproject or requirements.txt + requirements.lock, .python-version (3.11.9), app/main.py with GET /healthz {status, version, engine_version, db}, app/config.py (pydantic-settings: ENV, DATABASE_URL with postgres:// rewrite, JWT_SECRET, FERNET_KEY, ISSUER_KEYS_JSON, CORS_ORIGINS, SMTP_*, PUBLIC_BASE_URL, FRONTEND_URL), CORS, request-id middleware, JSON logging with PII filter.
3. docker-compose.yml: db (postgres:16), mailpit (8025/1025), backend (8000), frontend (5173, build from frontend/ if present else skipped via profile). .env.example with every variable.
4. render.yaml (repo root Blueprint, plan: free explicitly):
   - web service eduverify-api: runtime python, rootDir: . , buildCommand: pip install -r backend/requirements.txt && pip install ./engine, startCommand: cd backend && alembic upgrade head && python -m app.seed --if-empty && uvicorn app.main:app --host 0.0.0.0 --port $PORT, healthCheckPath: /healthz, envVars incl. PYTHON_VERSION=3.11.9, DATABASE_URL fromDatabase, secrets with sync:false.
   - static site eduverify-web: rootDir frontend, buildCommand npm ci && npm run build, staticPublishPath dist, routes rewrite /* → /index.html, env VITE_API_URL.
   - database eduverify-db (free, postgres 16).
5. .github/workflows/backend.yml (paths backend/** contracts/openapi.yaml contracts/schemas/**): ruff, pytest, schemathesis. security.yml: bandit -r backend engine, pip-audit, npm audit --audit-level=high (frontend), ZAP baseline against STAGING_URL on main only.
6. Tests: /healthz, openapi.yaml validates (openapi-spec-validator).
Tag request: ask the lead to tag contracts-v0.1 once merged.
Check: http://localhost:8000/healthz and http://localhost:8000/docs
```

**What it does:** publishes the API contract on day one so Team A can build against mocks, and sets up local Docker + Render deploy files so deployment works from the start.

---

## B1 — AUTH: login, JWT, API keys, RBAC, audit hook (dedicated auth prompt)

```
Task B1. Authentication and authorisation. This is the security core; be careful and test thoroughly.
1. Models + migration: users (id, email unique, password_hash, full_name, role, institution_aicte_id nullable, dab_id nullable, student_apaar_hash nullable, is_active, failed_logins, locked_until, mfa_secret nullable, created_at, last_login_at), refresh_tokens (jti, user_id, expires_at, revoked_at, replaced_by, user_agent_hash), api_keys (id, institution_aicte_id, name, prefix, key_hash, scopes[], created_by, last_used_at, revoked_at), audit_log (id, ts, actor_type, actor_id, role, action, resource, resource_id, ip_hash, payload_json (masked), prev_hash, hash).
2. Passwords: argon2id (argon2-cffi), min 10 chars, breached-pattern check against a small local list; never return hashes.
3. Tokens: POST /v1/auth/login {email,password} → access JWT (15 min, HS256 or EdDSA, claims sub, role, inst, dab, jti, iat, exp, iss, aud) + refresh token (7 days) in an HttpOnly Secure SameSite=Lax cookie (and in body for API clients). POST /v1/auth/refresh with rotation + reuse detection (reuse ⇒ revoke whole family). POST /v1/auth/logout revokes. GET /v1/auth/me. POST /v1/auth/password.
4. Lockout: 5 failed logins ⇒ lock 15 min; slowapi rate limit 10/min/IP on login. Uniform error message (no user enumeration). Constant-time compare.
5. Optional TOTP MFA for AICTE_ADMIN (pyotp) behind a feature flag MFA_REQUIRED_FOR_ADMIN.
6. API keys: POST /v1/api-keys (INSTITUTION_ADMIN) returns the full key ONCE (format evk_<prefix>_<secret>), store sha256 hash; auth via `Authorization: ApiKey evk_...` or X-API-Key header; scopes upload|read; bound to one institution. List/revoke endpoints.
7. RBAC: app/security/deps.py → get_current_principal (JWT or API key), require_roles(*roles), require_scope(scope), require_same_institution(inst_id) helper, require_self_student(apaar). Roles exactly as agents.md §9. Unit-test a matrix: every role × every protected router → expected 200/403.
8. Audit: app/services/audit.py append(action, ...) computes hash = sha256(prev_hash + canonical_json(payload)) inside a transaction with a row lock on the last row (advisory lock on Postgres; serialised in SQLite). Log login success/failure, token reuse, key create/revoke.
9. Seed (app/seed.py, idempotent, --if-empty), password SEED_PASSWORD from env, exactly these users (runthrough.md depends on them): aicte.admin@demo.local, aicte.analyst@demo.local, inst.admin@demo.local + inst.staff@demo.local (demo institution), inst2.admin@demo.local (neighbour institution), dab.admin@demo.local (demo DAB), student@demo.local (linked to a demo APAAR), verifier@demo.local. Refuse to seed with the default password when ENV != dev.
10. Security headers middleware (HSTS when not dev, X-Content-Type-Options, frame-ancestors none, Referrer-Policy).
11. Update openapi.yaml (securitySchemes bearerAuth + apiKey), tests: login ok/bad, lockout, refresh rotation + reuse, API key auth, RBAC matrix, audit chain hashes link.
Tag request: ask the lead to tag api-v0.1 (Team A switches login from MSW to real API).
Check: http://localhost:8000/docs → POST /v1/auth/login with aicte.admin@demo.local → Authorize → GET /v1/auth/me.
```

**What it does:** gives the whole system its identity layer — human logins with short-lived JWTs and rotating refresh tokens, institution API keys for system-to-system upload, role checks on every endpoint, and tamper-evident logging of every security event.

---

## B2 — Database, master data, mock APAAR registry

```
Task B2. Core data model.
1. Models + migration: degree_awarding_bodies, institutions (onboarding_level, affiliated_dab_id, did), states, districts, programs, academic_years, enums, program_intake, declared_totals, batches (state machine per agents.md §8.7, version, supersedes_batch_id, idempotency_key, column_mapping_json, engine_version, catalog_version, quality_score_before/after), batch_files (bytea, sha256, size), batch_reports (json), issues (flattened from report: rule_id, severity, priority, bucket, status OPEN/ACCEPTED/DISMISSED/FIXED, decided_by, decided_at), corrections (issue_id, field, old_value_enc, new_value_enc, proposed_by, approved_by, status), duplicate_flags, student_records (current version + record_version, email/mobile encrypted), student_record_versions, transfers, consent_ledger, credentials, status_lists, webhooks, webhook_deliveries, notifications_outbox, metric_history, column_mapping_profiles, jobs.
2. Encryption: app/security/crypto.py AES-GCM (or Fernet) for email/mobile, keyed hash (HMAC-SHA256 with PEPPER) of APAAR for lookups/pseudonymisation.
3. Seeder loads data/master/*.csv and data/demo/* (registry, intake, declared totals, central snapshot, transfers, history).
4. ApaarRegistry Protocol + MockApaarRegistry (DB-backed) implementing what the engine expects (lookup). GET /v1/registry/{apaar}/check for AICTE only (returns exists + masked match result).
5. Master endpoints (read for all authenticated, write AICTE_ADMIN): states, districts, institutions, programs, academic-years, enums, DABs. GET /v1/templates/student-upload.xlsx — generated from master: headers, data-validation dropdowns from enums, APAAR column formatted as Text, an Instructions sheet in English + Hindi.
6. Tests: migrations up/down on SQLite and Postgres (CI service), seed idempotent, template opens and APAAR column is text.
Check: http://localhost:8000/docs → GET /v1/master/programs ; http://localhost:8000/v1/templates/student-upload.xlsx downloads.
```

**What it does:** creates every table the system needs, loads Team C's master/demo data, and provides the mock APAAR registry and the Excel template institutions download.

---

## B3 — Upload pipeline: batches, mapping, validation job, SSE, commit

```
Task B3. Upload → validate → commit. Requires engine-v0.1 tag.
1. POST /v1/batches (multipart file + academic_year, optional supersedes_batch_id, Idempotency-Key header) — INSTITUTION_ADMIN/STAFF or API key scope upload. Size/type check, sha256, store in batch_files. Enforce one non-terminal batch per institution+year (409 with the open batch id) unless superseding.
2. Mapping step: job runs engine.suggest_mapping (with saved profile) → state MAPPING. GET /v1/batches/{id}/mapping; PUT /v1/batches/{id}/mapping confirms (and optionally saves profile). API-key uploads auto-confirm if all required columns map with confidence ≥ 0.9.
3. Validation job (DB-backed jobs table + BackgroundTasks; resumable on restart: on startup re-queue jobs stuck RUNNING): builds context (master, intake, declared totals, registry, central snapshot = committed records of OTHER institutions for that year, history, previous batch profile, transfers) → engine.validate_batch → persist report, flatten issues/duplicate flags, metric_history, quality_score_before → state VALIDATED or IN_REVIEW.
4. SSE: GET /v1/events (auth via short-lived ticket query param since EventSource can't set headers: POST /v1/events/ticket). Events batch.progress, batch.validated, batch.committed, anomaly.detected, duplicate.cross_institution. In-process broadcaster + 5 s DB poll fallback.
5. GET /v1/batches (filters), GET /v1/batches/{id}, GET /v1/batches/{id}/report (json|xlsx via engine.export_report; pdf via WeasyPrint template in backend/app/reports/templates/), GET /v1/batches/{id}/issues (filter rule, severity, priority, bucket, status; sorted by priority).
6. POST /v1/batches/{id}/commit (INSTITUTION_ADMIN): blocked if any OPEN CRITICAL issue; advisory lock on (institution, year) + version check; upserts valid rows into student_records (new version if changed → supersede credentials, see B6), rows with unresolved ERRORs excluded and listed; state COMMITTED; audit + SSE + webhook + notification.
7. PUT /v1/students/{apaar_id} (institution of record): correction → new record version, audit, mark credentials superseded (hook for B6).
8. Tests: happy path with data/demo/batch_1_clean.csv, mapping with batch_2_errors.xlsx, concurrent commit race (two threads → one wins, other 409), idempotent re-upload returns same batch, supersede flow.
Check: http://localhost:8000/docs → POST /v1/batches with data/demo/batch_2_errors.xlsx → GET /v1/batches/{id}/issues.
```

**What it does:** the main pipeline from the PS — Institution → Upload → APAAR validation → Data verification → Central repository — with safe concurrency, resumable jobs and live events.

---

## B4 — Human review, corrections, duplicates, lifecycle, transfers, reconciliation, rollover

```
Task B4. Review and lifecycle. Works on engine-v0.1. Until engine-v0.5 lands, the rollover endpoint returns 501 and dq-comparison returns only the score delta; B7 finishes both.
1. Issues: POST /v1/issues/{id}/decision {action: ACCEPT_FIX|EDIT_FIX|DISMISS, value?, note} — INSTITUTION_ADMIN (STAFF may only propose). Creates corrections row; nothing changes the data until approved. POST /v1/batches/{id}/revalidate re-runs the engine on the corrected dataset and stores quality_score_after + engine.compare_reports → GET /v1/batches/{id}/dq-comparison (json|xlsx|pdf).
2. Duplicates: GET /v1/duplicates (scope, bucket, status; AICTE sees cross-institution, institutions see their own), GET /v1/duplicates/{id} (side-by-side masked records + matched_fields), POST /v1/duplicates/{id}/resolve {decision: SAME_PERSON|DIFFERENT_PEOPLE|TRANSFER, note} — AICTE_ANALYST for cross-institution.
3. Lifecycle: POST /v1/students/{apaar_id}/transitions with the allowed transitions table in agents.md §8.1 (invalid → 422 with V021); history in student_record_versions.
4. Transfers: POST /v1/transfers (destination INSTITUTION_ADMIN), GET /v1/transfers?direction=in|out, POST /v1/transfers/{id}/approve|reject (source), POST /v1/transfers/{id}/override (AICTE_ADMIN after 15 days). Approval sets source TRANSFERRED_OUT.
5. Aggregates: POST /v1/aggregates (AGGREGATE_ONLY institutions; totals per program/year), GET /v1/declared-totals, GET /v1/reconciliation?year=&state= (declared vs uploaded vs aggregate, status) and coverage % for dashboards.
6. Rollover: POST /v1/admin/rollover {from_year,to_year, dry_run} (AICTE_ADMIN) using engine.rollover_preview; dry_run returns counts.
7. Tests for each flow, especially: approved transfer → re-upload at destination has no V010.
Check: http://localhost:8000/docs → GET /v1/duplicates?scope=CROSS_INSTITUTION ; POST /v1/transfers.
```

**What it does:** the accountability layer — humans approve fixes, resolve duplicates, move students through their lifecycle and between institutions, and AICTE reconciles declared totals with real data.

---

## B5 — Consent ledger, audit chain verification, PII protection

```
Task B5. Privacy and audit.
1. Consent: POST /v1/consent {purpose: REPOSITORY|VERIFICATION_SHARE|ANALYTICS_AGGREGATE, action: GRANT|WITHDRAW} (STUDENT for self; INSTITUTION_ADMIN may record guardian consent with evidence ref), GET /v1/consent/me, append-only consent_ledger with hash linking. Effects per agents.md §8.4: VERIFICATION_SHARE withdraw → suspend credentials (hook into B6) and block presentations; REPOSITORY withdraw → pseudonymise PII, keep counts.
2. Audit: GET /v1/audit (AICTE_ADMIN, filters), GET /v1/audit/verify-chain → {valid, length, first_broken_id?, head_hash}; a test that tampering a row is detected. Daily head hash written to logs (stretch: Merkle root per batch).
3. PII: response serializers mask apaar/email/mobile unless principal is the record's student or its institution admin; AICTE_ANALYST always masked. Every unmasked read writes an audit row with purpose.
4. Data retention config + scheduled job stub to purge raw batch_files after 90 days.
5. backend/THREAT_MODEL.md: STRIDE table, assets, trust boundaries, holder-key custody decision (agents.md §8.2), consent/credential behaviour, DPDP Act 2023 note, residual risks.
Check: http://localhost:8000/docs → GET /v1/audit/verify-chain returns valid:true.
```

**What it does:** enforces consent, proves the audit log was never edited, and ensures nobody sees personal data they shouldn't.

---

## B6 — Verifiable credentials (SD-JWT VC), verification, QR, certificates

```
Task B6. Trust layer.
1. Keys: each issuer (institution, DAB, AICTE) has an Ed25519 key from ISSUER_KEYS_JSON (dev: generated + stored encrypted in DB). did:web documents: GET /.well-known/did.json (AICTE) and GET /issuers/{issuer_id}/did.json. GET /v1/trust-list (AICTE-signed list of issuer DIDs).
2. app/vc/sdjwt.py wrapper over the `sd-jwt` library (pin version; if its KB-JWT/VC API is insufficient implement SD-JWT per the IETF spec yourself: salted disclosures, _sd digests sha-256, ~-separated, KB-JWT with sd_hash). Claims: vct "EduVerifyEnrolmentCredential" or "EduVerifyDegreeCredential", iss, iat, exp, cnf.jwk (holder public key from the student's browser), status {status_list: {idx, uri}}, always-disclosed: institution name, credential type; selectively disclosable: full_name, apaar_id, institution_student_id, program, course_level, academic_year, enrolment_status, dob, category, quota, nationality, graduation year.
3. POST /v1/credentials/issue (INSTITUTION_ADMIN for enrolment; DAB_ADMIN for degree, only for records whose institution is affiliated) requires VERIFICATION_SHARE consent and a holder JWK registered via POST /v1/credentials/holder-key (STUDENT). GET /v1/credentials/me.
4. Status lists (Token Status List style bitstring, gzip+base64): bits for REVOKED, SUPERSEDED, SUSPENDED. GET /v1/status-lists/{id}. Hooks: record correction → SUPERSEDED (B3/B4), consent withdraw → SUSPENDED (B5), manual revoke POST /v1/credentials/{id}/revoke.
5. Presentation: GET /v1/verify/nonce?aud=... → nonce (5 min). Student browser builds SD-JWT+KB. POST /v1/verify (VERIFIER or public with rate limit) {presentation} → checks signature, issuer in trust list, not expired, status bits, KB-JWT signature vs cnf, nonce/aud, sd_hash → {result: VALID|INVALID|REVOKED|SUPERSEDED|SUSPENDED, disclosed_claims, issuer_name, issued_at, checked_at, reasons[]}. Audit every verification (no PII in audit beyond masked APAAR).
6. QR: GET /v1/credentials/{id}/qr.png encodes https://<FRONTEND_URL>/verify#<compact presentation or short-link id>. Short links stored 24 h for long presentations.
7. Certificates: GET /v1/credentials/{id}/certificate.pdf rendered with WeasyPrint from reports/templates/certificate.html (Team A owns the template; backend reads it) showing APAAR ID, institution student ID, issuer (DAB or institution), QR.
8. Tests: issue → present (selective subset) → verify VALID; tampered disclosure → INVALID; correction → SUPERSEDED; consent withdrawn → SUSPENDED; wrong nonce → INVALID.
Tag request: ask the lead to tag api-v1.0 (Team A A6 depends on it).
Check: http://localhost:8000/.well-known/did.json and http://localhost:8000/docs → POST /v1/verify.
```

**What it does:** turns repository records into tamper-proof, privacy-preserving credentials students control, and lets employers/regulators verify only what they are shown.

---

## B7 — Integrations: webhooks, notifications, bulk export, reports, dashboards API

```
Task B7. Integration and analytics APIs.
1. Webhooks: POST/GET/DELETE /v1/webhooks (INSTITUTION_ADMIN; url https only except localhost in dev, events[], secret shown once), POST /v1/webhooks/{id}/test. Delivery worker: HMAC-SHA256 signature header X-EduVerify-Signature (t=,v1=), retries with exponential backoff (5 tries), webhook_deliveries log, GET /v1/webhooks/{id}/deliveries.
2. Notifications: outbox + worker; email via SMTP (Mailpit locally), SMS adapter stub; templates for batch validated/committed, review needed, transfer request, consent change, credential revoked/superseded. GET /v1/notifications/me.
3. Bulk export (AICTE_ADMIN): GET /v1/exports/students?year=&state=&format=csv|parquet (streamed, masked unless ?unmasked=true + reason → audit).
4. Dashboards API (cached 30 s): /v1/dashboards/aicte/summary (institutions, coverage %, students, fill %, excess, supernumerary/NRI/OCI/FN breakdown, DQ avg), /aicte/map?metric= (by LGD state code), /aicte/leaderboards (excess enrolment, low DQ, most cross-dupes), /aicte/anomalies (feed), /institution/summary (own), /institution/dq-trend.
5. Reports: POST /v1/reports {type: POLICY|ACCREDITATION|MONITORING|REGULATORY, filters: year, state, program, category, format: pdf|xlsx} → job → GET /v1/reports/{id}/download. PDF templates read from reports/templates/ (Team A).
6. Finish B4 stubs: wire POST /v1/admin/rollover to engine.rollover_preview (engine-v0.5) and GET /v1/batches/{id}/dq-comparison to engine.compare_reports + export_report (engine-v1.0). Bump the engine pin.
7. Tests incl. webhook signature verification example in Python + Node in backend/docs/webhooks.md.
Check: http://localhost:8000/docs → GET /v1/dashboards/aicte/summary ; emails at http://localhost:8025
```

**What it does:** connects EduVerify to institution ERPs and AICTE systems (webhooks, exports, API keys), notifies people, and feeds the dashboards and policy reports.

---

## B8 — Hardening, contract tests, security scans, deploy to Render

```
Task B8. Ship it.
1. Schemathesis full run against the live app using contracts/openapi.yaml (all endpoints, auth via fixture tokens); fix every drift.
2. Security: bandit clean (or justified # nosec), pip-audit clean, rate limits on public endpoints (verify, login), request size limits, ZAP baseline config in infra/zap/ with ignore list reviewed.
3. Performance: 20k-row batch end-to-end < 2 min on Render free; add DB indexes (institution+year, apaar_hash, batch_id, rule_id/priority).
4. Environments: render.yaml with env groups dev/staging/prod (staging = same blueprint, different branch), PUBLIC_BASE_URL/FRONTEND_URL per env. TLS is automatic on Render; enforce HTTPS redirect + HSTS outside dev.
5. Migrations strategy doc: expand/contract, never destructive in one deploy; alembic downgrade tested.
6. Backups: infra/backup.sh (pg_dump to S3-compatible bucket / local file), infra/restore.sh; documented restore drill. Note Render free DB expires after 30 days.
7. Deploy via Blueprint, seed demo data, smoke test script infra/smoke.sh (healthz, login, upload demo batch, verify a credential) against the deployed URL.
8. Update README deploy section with the hosted demo URL.
Check: http://localhost:8000/healthz locally, then the Render URL /healthz.
```

**What it does:** proves the API matches its contract, closes security gaps, and puts a working demo on the internet with a backup/restore plan.
