# steps.md — Build order and per-phase Antigravity prompts

> Read `agents.md` first; it defines the contracts, rule IDs, roles and folder ownership used below.
> Each phase has one prompt per team. Paste the prompt for your team into Antigravity **at the start of that phase**. Do not start the next phase until the phase's **sync checkpoint** passes.

---

## 0. How every prompt runs (the loop each agent follows)

1. **Brainstorm.** List 2–3 approaches, pick one, note risks (≤10 lines).
2. **Plan.** Write a checklist of files and functions to create, with tests. Put it in the PR description.
3. **Work.** Implement one checklist item at a time, running tests after each.
4. **Review.** Self-review the diff against `agents.md` §8 (folder ownership, no PII in logs, tests, OpenAPI updated).
5. **Report.** Give a terse summary: what's done, what's left, any contract question for another team.

Model use: a fast model for reading docs and web search; a strong coding model for implementation and review.

---

## 1. Timeline at a glance

| Phase | Goal | Team A (Data & Intelligence) | Team B (Platform & Trust) | Team C (Experience & Insights) | Sync checkpoint |
|---|---|---|---|---|---|
| 0 | Repo and contracts | rule_catalog.yaml, synthetic generator v0 | openapi.yaml, schemas, docker-compose | Vite app shell, MSW mocks, design tokens | All 3 contracts merged; `docker compose up` runs |
| 1 | Foundations | Parser + schema rules V001–V008 | DB, auth, RBAC, upload endpoint (sync) | Login, upload page, issue table on mocks | Upload a CSV and see real V001–V008 issues in the UI |
| 2 | Core validation | Intake/consistency/consent rules V012–V019, DQ report | Async jobs, SSE, mock APAAR registry (V003/V004), central repository | Institution dashboard, AICTE console v1 | Over-intake batch shows V012 live on the AICTE console |
| 3 | Intelligence | Dedup (V009–V011), anomaly (V020), metric history | Duplicate review API, metric_history persistence | Duplicate review queue, anomaly feed | Cross-institution duplicate seeded and caught end to end |
| 4 | Trust and verification | Report exports (XLSX/JSON) | Consent ledger, audit chain, SD-JWT issue/verify, QR, did.json | Verifier portal, student consent/share, certificate template | QR on certificate verifies with selective disclosure; tampered audit row detected |
| 5 | Hardening and demo | Precision/recall eval, load test 50k rows | Security pass, rate limit, webhooks, seed script | Policy reports, lit review, demo script, deck | Full 5-minute demo runs twice in a row with no manual fixes |

---

## Phase 0 — Repo and contracts

**Team A prompt**
```
Phase 0, Team A. Read agents.md §5–6 and §9.
1. Create engine/ as a Python package `apaar_engine` (pyproject.toml, ruff, pytest).
2. Write contracts/rule_catalog.yaml with V001–V020 (id, severity, description, fields, params) exactly as in agents.md §6.
3. Write engine/apaar_engine/models.py: Pydantic v2 models StudentRecord, ProgramIntake, Issue, DuplicateCluster, Anomaly, BatchReport matching agents.md §5.
4. Write data/synthetic/generate.py v0: 5 institutions, 3 programs each with approved_intake, 1,000 valid students with 12-digit APAAR IDs. Output students.csv, intake.csv, registry.csv (mock APAAR registry) and defects.json (empty for now).
5. pytest: the models round-trip the generated CSV.
Do not touch backend/ or frontend/. Brainstorm → plan → work → review. Terse output.
```

**Team B prompt**
```
Phase 0, Team B. Read agents.md fully.
1. Write contracts/openapi.yaml (OpenAPI 3.1) covering: auth (/v1/auth/login), institutions, programs/intake, batches (POST upload, GET status, GET report, GET issues, POST resubmit), students (GET/PUT by apaar_id, masked), duplicates (list, resolve), anomalies (list), consent (grant/withdraw), credentials (issue, revoke, status list), verify (POST), audit (list, verify-chain), reports (generate), events (SSE /v1/events). Use the BatchReport schema from agents.md §5.3.
2. contracts/schemas/student_record.json (JSON Schema) from agents.md §5.1.
3. backend/ skeleton: FastAPI app, settings via pydantic-settings, health endpoint, Alembic init.
4. docker-compose.yml: postgres:16, redis:7, backend, frontend. Add .env.example.
Do this contract work FIRST and push it early: Team C mocks against it.
Brainstorm → plan → work → review. Terse output.
```

**Team C prompt**
```
Phase 0, Team C. Read agents.md §2, §3, §7, §10.
1. frontend/: Vite + React 18 + TS + Tailwind + shadcn/ui + React Router + TanStack Query.
2. Generate a typed API client from contracts/openapi.yaml (openapi-typescript) once Team B pushes it; until then stub the types.
3. MSW mock handlers for every endpoint, returning realistic fake data (masked APAAR like 1234****9012).
4. Layout with role-based navigation: Institution, AICTE, Verifier, Student. Design tokens: government-portal palette, accessible contrast, dark mode.
5. docs/literature_review.md skeleton with the source table from agents.md §9.
Brainstorm → plan → work → review. Terse output.
```

✅ **Checkpoint 0:** contracts merged; `docker compose up` starts all services; frontend renders with mocks.

---

## Phase 1 — Foundations

**Team A prompt**
```
Phase 1, Team A.
1. engine/apaar_engine/parser.py: read CSV and XLSX (openpyxl), detect encoding, normalise headers (case, spaces, common aliases like "APAAR No" → apaar_id), trim cells, keep the original row number. Bad rows become issues; parsing never crashes.
2. engine/apaar_engine/rules/: a registry that loads rule_catalog.yaml and maps rule_id → function. Implement V001, V002, V005, V006, V007, V008 vectorised in pandas/pandera.
3. engine/apaar_engine/validate.py: validate_batch(file_or_df, intake_df, registry=None, history=None) -> BatchReport. Rules that need registry/history are skipped when those are None.
4. Extend the generator to inject these defects at known rows and record them in defects.json.
5. pytest: every injected defect is found with the right rule_id and row; clean rows have no issues.
Terse output.
```

**Team B prompt**
```
Phase 1, Team B.
1. SQLAlchemy models + Alembic migration: institutions, users, api_keys, programs, program_intake, batches, student_records, issues, audit_log (with prev_hash, hash).
2. Auth: POST /v1/auth/login (argon2 passwords, JWT access + refresh); API key auth for institution machine clients (hashed keys, prefix shown once).
3. RBAC dependency require_roles(...) enforced on every router; roles from agents.md §7.
4. POST /v1/batches (multipart CSV/XLSX, max 20 MB, idempotency-key header), run apaar_engine.validate_batch synchronously for now, persist the batch and issues, return the BatchReport.
5. Seed script: AICTE admin, 5 institutions with admins, programs and intake from data/synthetic/intake.csv.
6. Tests with httpx: role denial, an upload happy path, a duplicate idempotency key.
Install the engine as an editable dependency (pip install -e ../engine). Terse output.
```

**Team C prompt**
```
Phase 1, Team C.
1. Login page → JWT stored in memory (refresh via httpOnly cookie when the backend supports it), role-based redirect.
2. Institution "Upload batch" page: download the CSV template (headers from student_record.json), drag-drop upload with progress, then show the BatchReport summary cards (total/valid/warning/error, quality score).
3. Issues table: virtualised, filter by rule_id/severity/field, search by masked APAAR, export the issue list as CSV, rule descriptions as tooltips (from rule_catalog.yaml).
4. Switch from MSW to the real backend behind an env flag VITE_USE_MOCKS.
5. Vitest for the table filters; a Playwright smoke test for login → upload → issues.
Terse output.
```

✅ **Checkpoint 1:** upload `data/synthetic/students_with_defects.csv` in the UI and see the V001–V008 issues at the right rows.

---

## Phase 2 — Core validation and central repository

**Team A prompt**
```
Phase 2, Team A.
1. Implement V012 (regular enrolment > approved_intake), V013 (supernumerary > allowed per scheme, from program_intake.supernumerary_allowed config), V014 (OCI/FN with nationality IN; NRI flag mismatch with quota), V015, V016 (age vs course_level: configurable ranges), V017 (admission_date within the academic-year window), V018 (consent missing; under 18 without guardian_consent), V019 (program not approved).
2. V003/V004: accept a `registry` object with lookup(apaar_id) -> {name, dob} | None. V004 uses rapidfuzz token_set_ratio on normalised names plus exact DOB.
3. intake_summary per program: approved, enrolled_regular, supernumerary by scheme, excess.
4. quality_score = weighted (completeness, validity, uniqueness, consistency) in 0–100; document the weights in the code.
5. reports/dq_report.py: BatchReport → XLSX (Summary, Issues, Intake, Column Metrics sheets) and JSON.
6. Generator: add over-intake, OCI-with-IN and missing-consent defects. Update the tests.
Terse output.
```

**Team B prompt**
```
Phase 2, Team B.
1. Move validation to an async worker (RQ + Redis; fallback BackgroundTasks). Batch states: UPLOADED → VALIDATING → VALIDATED | REJECTED → COMMITTED.
2. GET /v1/events (SSE): emit batch.progress, batch.completed, anomaly.detected, duplicate.flagged, scoped by role and institution.
3. ApaarRegistry interface + MockApaarRegistry (seeded from data/synthetic/registry.csv), passed into validate_batch.
4. Commit step: only rows without ERROR issues upsert into student_records (key: apaar_id + program_code + academic_year). Keep version history (valid_from, valid_to). Institutions can PUT corrections with a reason; every change goes to the audit log.
5. Aggregation endpoints for dashboards: /v1/stats/intake (by state/program/year), /v1/stats/quotas, /v1/stats/quality.
6. GET /v1/batches/{id}/report.xlsx using Team A's exporter.
Terse output.
```

**Team C prompt**
```
Phase 2, Team C.
1. Institution dashboard: per-program intake vs enrolment bars (approved / regular / supernumerary / excess in red), quota breakdown (NRI/OCI/FN/PIO), DQ score trend across batches, batch history list with status chips updated live via SSE.
2. AICTE console v1: KPI tiles (institutions reporting, students, average DQ score, excess-enrolment count), state-wise choropleth or table drilldown → institution → program, an "excess enrolment" leaderboard, live batch feed.
3. Fix-and-resubmit flow: download the issue XLSX, upload a corrected file linked to the original batch, show a diff of the issue counts.
4. Mask PII by default; "reveal" needs the AICTE_ANALYST role and shows that the action is audited.
Terse output.
```

✅ **Checkpoint 2:** an over-intake batch from institution 3 shows V012 on the institution page and lights up the AICTE console in real time.

---

## Phase 3 — Intelligence: dedup and anomaly detection

**Team A prompt**
```
Phase 3, Team A.
1. engine/apaar_engine/dedup/normalize.py: Indian name normalisation (uppercase, strip honorifics SHRI/SMT/KUMARI/DR/MR/MS, remove punctuation, collapse spaces, expand/handle initials, sorted tokens) + indic-soundex codes.
2. dedup/intra.py (V009): block on (soundex of first token, dob year) and (dob, gender); score with Jaro-Winkler + token_set_ratio + exact dob; cluster pairs ≥0.92 = flag, 0.75–0.92 = review.
3. dedup/cross.py (V010, V011): input = new batch + central repository snapshot (DataFrame). V010 = same APAAR ACTIVE at another institution in the same year. V011 = Splink (duckdb, link_only) fuzzy match with a different APAAR. Return DuplicateClusters with scope=CROSS_INSTITUTION and the evidence fields.
4. anomaly/metrics.py: Deequ-style per-batch metric state (null rate per column, duplicate rate, nri/oci/fn share, supernumerary share, intake fill ratio, rows); mergeable JSON states.
5. anomaly/detect.py (V020): z-score / relative change vs the institution's history (min 3 batches, else peer-group baseline by state + program); plus IsolationForest across institutions; every anomaly gets a human-readable reason.
6. Generator: transliteration variants (Bhairoo/Bheru, Krishna/Krushna), initials, swapped name order, cross-institution double enrolment, a sudden NRI-share spike. Report precision/recall/F1 per rule in tests.
Terse output.
```

**Team B prompt**
```
Phase 3, Team B.
1. Pass a central repository snapshot (only the columns needed for blocking) and the metric history into validate_batch. Persist metric states to metric_history.
2. duplicate_flags table + endpoints: GET /v1/duplicates (filter scope/status), POST /v1/duplicates/{id}/resolve {decision: SAME_PERSON|DIFFERENT|INSTITUTION_ERROR, note}. Resolution is audited and notifies both institutions (SSE + webhook).
3. anomalies table + GET /v1/anomalies; AICTE can acknowledge or escalate them.
4. Performance: index apaar_id, (institution, program, year), name_norm soundex; a 50k-row batch must validate in < 60 s locally.
Terse output.
```

**Team C prompt**
```
Phase 3, Team C.
1. Duplicate review queue (AICTE): list with score, scope and institutions; side-by-side compare showing which fields matched and how strongly; resolve buttons with a note; keyboard shortcuts.
2. Anomaly feed: live cards (metric, value vs baseline, reason, institution), acknowledge/escalate, sparkline of the metric history.
3. Institution view of duplicates that involve its students (masked info about the other institution).
Terse output.
```

✅ **Checkpoint 3:** a seeded cross-institution double enrolment (same student, transliterated name, different APAAR) is caught as V011 and resolved from the UI.

---

## Phase 4 — Trust: consent, audit, verifiable credentials

**Team A prompt**
```
Phase 4, Team A.
1. Credential claim builder: from_student_record(record) → a dict of claims for the SD-JWT (apaar_id, institution_student_id, full_name, program, course_level, academic_year, enrolment_status, quota flags), each marked selectively disclosable except issuer metadata.
2. Report exports for policy use: aggregate tables (by state, program, category, quota, year) as DataFrames + XLSX, with small-cell suppression (counts < 5 shown as "<5") for privacy.
3. Tests for both.
Terse output.
```

**Team B prompt**
```
Phase 4, Team B.
1. Consent ledger: POST /v1/consent {purpose: REPOSITORY|VERIFICATION_SHARE, action: GRANT|WITHDRAW}; current consent = the latest event. Block credential issue/verify without VERIFICATION_SHARE consent. Show consent history to the student.
2. Audit chain: every write + PII read + verification appends (actor, role, action, entity, ts, prev_hash, hash). GET /v1/audit/verify-chain recomputes and returns the first broken link if any. Add a script that tampers one row for the demo.
3. Keys: Ed25519 per institution + AICTE root key; /.well-known/did.json (did:web) and a trusted-issuer list signed by AICTE.
4. POST /v1/credentials/issue → SD-JWT VC (claims from Team A's builder). POST /v1/credentials/{id}/revoke → status list bit. GET /v1/status-list.
5. POST /v1/verify {presentation}: check signature, issuer in the trust list, not revoked, disclosures hash-match; return only the disclosed claims + issuer + issued_at. VERIFIER role or a public endpoint with rate limit; always audited.
6. QR payload: a compact URL https://<host>/verify#<presentation> for certificates (APAAR + institution_student_id always disclosed on certificates per PS requirement 10).
7. Stretch: a Merkle root of committed records per batch stored in batches.merkle_root; per-record inclusion proof endpoint.
Terse output.
```

**Team C prompt**
```
Phase 4, Team C.
1. Student page: own record (masked), consent toggles with history, "Share" builder: pick fields → call issue/present → show the QR + copy link + expiry.
2. Verifier portal: camera QR scan (html5-qrcode) or paste → big green VERIFIED / red FAILED with reason (bad signature, revoked, untrusted issuer), disclosed fields only, issuer name, check timestamp.
3. Certificate template (reports/templates/certificate.html, printable A4): institution name, student name, program, APAAR ID, student ID, QR code, verification URL.
4. Audit page (AICTE): searchable log + "Verify chain integrity" button showing OK or the broken link.
Terse output.
```

✅ **Checkpoint 4:** print a certificate, scan its QR on the verifier portal, see only the chosen fields; revoke it and the scan fails; tamper an audit row and the chain check catches it.

---

## Phase 5 — Hardening, reports and demo

**Team A prompt**
```
Phase 5, Team A.
1. Evaluation script: on 3 seeds of synthetic data print a precision/recall/F1 table per rule and for dedup; save it to docs/evaluation.md (Team C links it in the deck).
2. Load test: 50k-row batch and 200k-row central repository; profile and fix hotspots.
3. Constraint suggestion (Deequ idea): profile a clean batch and suggest new rules (not-null, enum, regex) for AICTE admin approval; output YAML.
Terse output.
```

**Team B prompt**
```
Phase 5, Team B.
1. Security pass: OWASP top 10 checklist, input size limits, CSV formula injection guard on exports (prefix = + - @), CORS lock-down, rate limits, secure headers, encrypted email/mobile at rest, secrets only from env.
2. Webhooks to institution systems (batch.completed, duplicate.flagged) with HMAC signatures + retries.
3. One-command demo: `make demo` seeds data, creates users per role, and loads the 4 demo batches (clean, defects, over-intake, cross-duplicate).
4. README backend section + Postman/Bruno collection generated from OpenAPI.
Terse output.
```

**Team C prompt**
```
Phase 5, Team C.
1. Report builder: filters (year, state, program, category, quota) → preview → export PDF/XLSX (policy, accreditation and monitoring templates).
2. Finish docs/literature_review.md: a comparison table (approach, privacy, selective disclosure, scale, cost, gaps) of the sources in agents.md §9 vs APAAR-SDMS. Mark sources read only as abstracts.
3. demo/demo_script.md (5 minutes): (1) institution uploads a defective batch → issues; (2) fix + resubmit → committed; (3) AICTE console shows over-intake + anomaly live; (4) cross-institution duplicate resolved; (5) certificate QR verified by an employer with selective disclosure; (6) audit tamper detected.
4. demo/pitch_outline.md: problem → solution → architecture → innovation (anomaly, fuzzy dedup, SD-JWT) → evaluation numbers → impact → roadmap (real APAAR/DigiLocker integration, PPRL, ZK predicates).
5. Accessibility + mobile pass; Playwright full-demo test.
Terse output.
```

✅ **Checkpoint 5 (final):** `make demo` → the demo script runs twice end to end with no manual fixes; all tests green.

---

## 6. Open items to confirm (do not assume)

- The official APAAR ID format and checksum (we validate 12 digits only; structure is a warning).
- Real APAAR/DigiLocker API access for production; we use a mock registry behind an interface.
- Current AICTE supernumerary percentages per scheme (kept in config).
- IEEE document 10163764 vs Rustemi et al. 2023 (DOI 10.1109/access.2023.3289598): confirm they are the same paper.
- Springer s10639-024-12493-6: get the full text manually; the research agent couldn't access it.
- SynEdu-HEDL column count (85 on Zenodo vs ~60 on GitHub): check the actual zip.
