# agents.md — EduVerify (APAAR-based Student Data Management & Verification System)

> **Read this file first, before `steps.md`, before every task.** It is the single source of truth for all 3 teams and every AI agent (Antigravity, Claude, etc.).
> Order of reading: `agents.md` → `steps.md` → your team file in `prompts/` → `runthrough.md` (how the finished app is used).

---

## 0. Files in this kit

| File | What it is |
|---|---|
| `agents.md` | Rules, architecture, contracts, ownership, decisions. Binding. |
| `steps.md` | Build order. Every prompt, what it does, its done-check, its localhost link, sync points between teams. |
| `prompts/team-a-frontend.md` | Paste-ready prompts for Team A (Frontend) |
| `prompts/team-b-backend.md` | Paste-ready prompts for Team B (Backend) — includes the dedicated **Auth** prompt |
| `prompts/team-c-ai.md` | Paste-ready prompts for Team C (AI / Data engine) |
| `runthrough.md` | End-to-end walkthrough of the finished app, screen by screen, with URLs |

---

## 1. What we are building

**EduVerify** lets AICTE-approved institutions upload student-level admission data (CSV/Excel or API), keyed by **APAAR ID**. Every upload is mapped (smart column mapping), validated (format, missing fields, cross-field consistency, intake limits, NRI/OCI/FN rules, intra- and cross-institution duplicates), explained field-by-field, prioritised by risk, and routed either to auto-flag or to human review. Clean, approved records go to the **AICTE Central Repository**. AICTE and institutions see live dashboards and before/after data-quality reports. Students hold a **signed, selectively disclosable credential** (SD-JWT VC + QR) that employers and regulators verify without seeing the full record. Every action is authenticated, role-checked, consent-gated and written to a hash-chained audit log.

**Pipeline (from the PS):**
`Institution → Student Data Upload → APAAR Validation → Data Verification → AICTE Central Repository → Analytics & Monitoring → Authorized Verification`

---

## 2. Teams and ownership (no overlapping files = no merge conflicts)

| Team | Name | Writes ONLY to | Mission |
|---|---|---|---|
| **A** | Frontend | `frontend/`, `docs/`, `demo/`, `reports/templates/`, `.github/workflows/frontend.yml` | All UI: institution portal, AICTE console, student wallet, verifier portal, reports UI, certificate template, i18n, literature review, demo script |
| **B** | Backend | `backend/`, `contracts/openapi.yaml`, `contracts/schemas/`, `infra/`, `render.yaml`, `docker-compose.yml`, `.env.example`, `.github/workflows/backend.yml`, `.github/workflows/security.yml` | API, DB, **auth/RBAC**, consent, audit chain, central repository, lifecycle/transfer, credentials, verification, webhooks, notifications, deploy |
| **C** | AI / Data | `engine/`, `data/`, `contracts/rule_catalog.yaml`, `contracts/column_synonyms.yaml`, `.github/workflows/engine.yml` | Parser, smart column mapping, rule engine (explainable), fuzzy dedup, anomaly + schema drift, reconciliation, DQ reports, master data + synthetic data |

**Root files** (`.gitignore`, `.gitattributes`, `.editorconfig`, `README.md`, `.github/CODEOWNERS`, `agents.md`, `steps.md`, `runthrough.md`, `prompts/`) are created once in Phase 0 by the **project lead** and then frozen. Changes go through a PR approved by all three teams.

### 2.1 Merge-conflict prevention rules (mandatory)

1. **Folder ownership is absolute.** Read anything, write only your folders. CODEOWNERS enforces review.
2. **No root `package.json`, no root `requirements.txt`, no root lockfile.** Each package has its own: `frontend/package-lock.json`, `backend/requirements.txt` (+ `requirements.lock`), `engine/pyproject.toml`.
3. **One CI workflow file per team** (listed above). Never edit another team's workflow.
4. **Contracts** (`contracts/`) change only via a PR labelled `contract-change`, approved by the owner + one other team. Bump the version string at the top of the file every time.
5. **Generated code is regenerated, not hand-merged.** `frontend/src/api/schema.gen.ts` is generated from `contracts/openapi.yaml` (`npm run gen:api`). If it conflicts, delete it and regenerate.
6. **Alembic migrations** only by Team B; one migration per PR; if two PRs collide, rebase and re-run `alembic revision --autogenerate` (never merge two heads by hand; use `alembic merge` only if both are already on `main`).
7. **Backend routers are one file per feature** (`backend/app/routers/<feature>.py`) and registered through a single list in `backend/app/routers/__init__.py` — append one line, sorted alphabetically.
8. **Frontend routes are one folder per feature** (`frontend/src/features/<feature>/`) and registered through `frontend/src/app/routes.tsx` — append one line, sorted alphabetically.
9. **Branch names:** `a/<topic>`, `b/<topic>`, `c/<topic>`. Short-lived (< 1 day). `git pull --rebase origin main` before every push. Squash-merge only.
10. **Line endings:** `.gitattributes` sets `* text=auto eol=lf`. Formatters: Prettier (A), ruff format (B, C). Run before commit so formatting never causes conflicts.
11. **Large data never committed.** `data/synthetic/` is gitignored and regenerated with a fixed seed. Only `data/demo/` (small, ≤ 2 MB total) and `data/master/` are committed.
12. **Tags mark integration points:** `contracts-v0.1`, `engine-v0.1`, `api-v0.1`, … (see `steps.md` §Sync points). Consumers pin to a tag, not to `main`.

---

## 3. Architecture and fixed tech stack

```
 ┌──────────────────────────── Team A · Frontend (Render Static Site) ─────────────────────────────┐
 │ React 18 · Vite · TypeScript · Tailwind · shadcn/ui · TanStack Query · React Router · Recharts  │
 │ react-i18next (en, hi) · react-dropzone · MSW (mocks from openapi.yaml) · @sd-jwt/* + WebCrypto │
 │ Institution portal │ AICTE console │ Student wallet │ Verifier portal │ Reports │ Certificate   │
 └───────────────────────────────▲─────────────────────────────────────────────────────────────────┘
                                 │ HTTPS REST (OpenAPI 3.1) + SSE
 ┌───────────────────────────────┴──────── Team B · Backend (Render Web Service) ──────────────────┐
 │ FastAPI · Python 3.11 · SQLAlchemy 2 · Alembic · Pydantic v2                                     │
 │ Auth: JWT (access+refresh) + argon2 + hashed API keys · RBAC deps · rate limit (slowapi)        │
 │ Consent ledger · hash-chained audit log · field encryption (Fernet/AES-GCM) · PII masking       │
 │ Jobs: DB-backed job table + FastAPI BackgroundTasks (no Redis needed on Render free)            │
 │ VC: SD-JWT VC (issuer Ed25519) · did:web · status list · QR · WeasyPrint PDF                    │
 │ Webhooks (HMAC) · notification outbox (SMTP / SMS stub) · mock APAAR registry adapter          │
 └──────┬────────────────────────────────────────────┬────────────────────────────────────────────┘
        │ `import eduverify_engine` (pip install ./engine)
 ┌──────▼──────────── Team C · AI engine (pure Python package) ─────┐   ┌──────────────────────────┐
 │ pandas · pandera · openpyxl · rapidfuzz · jellyfish/indic-soundex │   │ PostgreSQL 16 (Render)   │
 │ scikit-learn IsolationForest · optional extra [splink] (DuckDB)   │   │ SQLite for local/tests   │
 │ Dev harness: FastAPI on :8100 (local only, never deployed)        │   └──────────────────────────┘
 └────────────────────────────────────────────────────────────────────┘
```

**Local ports (memorise):**

| Service | URL |
|---|---|
| Frontend (Vite) | http://localhost:5173 |
| Backend API + Swagger | http://localhost:8000/docs (health: http://localhost:8000/healthz) |
| Engine dev harness (Team C only) | http://localhost:8100/docs |
| Mailpit (email inbox for notifications) | http://localhost:8025 |
| Postgres | `localhost:5432` (via `docker compose up db`) |

**Render-safe rules (so deploy never breaks):**
- Backend binds `0.0.0.0:$PORT`; never hard-code 8000 in the start command.
- Start command: `alembic upgrade head && python -m app.seed --if-empty && uvicorn app.main:app --host 0.0.0.0 --port $PORT` (migrations in start command works on free plan).
- `DATABASE_URL` from Render; code rewrites `postgres://` → `postgresql+psycopg://`.
- No local-disk persistence (Render disk is ephemeral): uploaded files stored as `bytea` in Postgres (`batch_files` table, 10 MB limit) or S3-compatible storage behind a `FileStore` interface.
- No Redis in the MVP. SSE uses an in-process broadcaster (single instance) + DB polling fallback.
- `CORS_ORIGINS` env var lists the frontend URL. Frontend reads `VITE_API_URL` at build time.
- Frontend static site has rewrite `/* → /index.html` for React Router.
- Engine heavy deps (`splink`, `duckdb`) are an **optional extra**; default dedup uses rapidfuzz so the 512 MB free instance does not OOM.
- Pin Python with a `.python-version` file in `backend/` **and** the `PYTHON_VERSION=3.11.9` env var; pin Node with `NODE_VERSION=20`. Set `plan: free` explicitly in `render.yaml`.
- Render free Postgres **expires 30 days after creation** (14-day grace). Create it ≤ 30 days before the final demo, or keep a `pg_dump` and restore with `infra/restore.sh`. Free web services sleep after 15 min idle → open the demo URL 2 minutes before presenting.
- Keys (JWT secret, Ed25519 issuer key, Fernet key) come from env vars; `app.keys` generates dev keys if missing **only when `ENV=dev`**.

---

## 4. Monorepo layout

```
eduverify/
├── agents.md  steps.md  runthrough.md  README.md
├── prompts/ team-a-frontend.md  team-b-backend.md  team-c-ai.md
├── contracts/
│   ├── openapi.yaml              (B)  API contract, versioned
│   ├── schemas/                  (B)  student_record.json, batch_report.json, enums.json, credential.json
│   ├── rule_catalog.yaml         (C)  V001–V035, versioned
│   └── column_synonyms.yaml      (C)  smart column mapping dictionary
├── engine/                       (C)  eduverify_engine package + devserver + tests
├── data/                         (C)  master/, demo/, generator, adapters, fixtures/
├── backend/                      (B)  app/, alembic/, tests/, THREAT_MODEL.md
├── frontend/                     (A)  src/, e2e/, public/
├── docs/  demo/  reports/templates/   (A)
├── infra/                        (B)  backup scripts, zap config
├── render.yaml  docker-compose.yml  .env.example   (B)
└── .github/ CODEOWNERS (lead) · workflows/frontend.yml (A) · backend.yml (B) · engine.yml (C) · security.yml (B)
```

---

## 5. Canonical data contract (`contracts/schemas/student_record.json`)

All teams use these field names exactly (snake_case). Enum values live in `contracts/schemas/enums.json` and the master tables (§7).

### 5.1 `student_record` — one row per student per program per academic year

| Field | Type | Req | Notes / rules |
|---|---|---|---|
| `apaar_id` | string(12) | yes | Exactly 12 digits, **always treated as text** (leading zeros). Internal structure not officially published → structure checks are WARN only |
| `institution_aicte_id` | string | yes | Must match uploader's institution and exist in master |
| `institution_student_id` | string | yes | Roll/PRN/enrolment no.; unique within institution + academic_year |
| `full_name` | string | yes | `name_norm` computed by engine |
| `dob` | date ISO | yes | Plausible for `course_level` |
| `gender` | M/F/T | yes | |
| `category` | GEN/EWS/OBC-NCL/SC/ST | yes | |
| `pwd` | bool | no | |
| `program_code` | string | yes | Must exist in `programs` master and be approved for this institution/year |
| `course_level` | DIPLOMA/UG/PG/PGDM/PHD | yes | Must agree with program master |
| `department` | string | no | Must agree with program master if given |
| `academic_year` | `2026-27` | yes | Must exist in `academic_years` master |
| `year_of_study` | int 1–6 | yes | ≤ program duration; lateral entry starts at 2 |
| `admission_date` | date ISO | yes | Inside academic-year admission window |
| `admission_type` | REGULAR/LATERAL/TRANSFER_IN | yes | |
| `expected_graduation_year` | int | no | Must equal admission year + program duration − (lateral ? 1 : 0) ± 1 (USP 3) |
| `seat_type` | REGULAR/SUPERNUMERARY | yes | |
| `supernumerary_scheme` | TFW/PMSSS/JK/NE/FN_OCI_NRI/PWD/OTHER/null | if SUPERNUMERARY | |
| `quota` | NONE/NRI/OCI/FN/PIO/CIWG | yes | |
| `nationality` | ISO-3166 alpha-2 | yes | |
| `nri_status`, `oci_status`, `fn_status` | bool | yes | Consistency with quota/nationality (V014) |
| `enrolment_status` | ACTIVE/WITHDRAWN/DEFERRED/TRANSFERRED_OUT/COMPLETED/GRADUATED | yes | Changes only via lifecycle endpoint after commit (§8.1) |
| `consent_status` | GRANTED/REFUSED/WITHDRAWN | yes | |
| `consent_date` | date | if GRANTED | |
| `guardian_consent` | bool | if age < 18 | |
| `email`, `mobile` | string | no | Encrypted at rest, masked in UI and logs |

### 5.2 Supporting tables (contract-level)

- `program_intake`: `institution_aicte_id, program_code, academic_year, approved_intake, supernumerary_allowed (JSON per scheme), approval_letter_ref`
- `declared_totals` (statistical submission from approval process): `institution_aicte_id, program_code, academic_year, declared_enrolment, declared_supernumerary, declared_nri, declared_oci, declared_fn, source (APPROVAL_PROCESS|AGGREGATE_MODE), submitted_at`

### 5.3 `BatchReport` (engine output, Pydantic model `engine/eduverify_engine/models.py`, mirrored in `contracts/schemas/batch_report.json`)

```json
{
  "batch_id": "uuid", "institution_aicte_id": "1-12345678",
  "engine_version": "1.0.0", "rule_catalog_version": "1.0.0",
  "rows_total": 0, "rows_valid": 0, "rows_warning": 0, "rows_error": 0,
  "quality_score": 0.0,
  "column_mapping": [{"source": "PRN", "target": "institution_student_id", "confidence": 0.97, "method": "synonym|fuzzy|user"}],
  "metrics": {"completeness": {"dob": 0.99}, "validity": {"apaar_id": 0.97}, "uniqueness": {"apaar_id": 1.0}},
  "issues": [{
    "issue_id": "uuid", "row": 12, "record_key": "inst_student_id", "field": "expected_graduation_year",
    "rule_id": "V025", "severity": "ERROR", "priority": "HIGH", "confidence": 0.98,
    "bucket": "AUTO_FLAG",
    "message": "Graduation year inconsistent with admission year and program duration",
    "reason": "admission_date 2026-08-01 + B.Tech duration 4y ⇒ expected 2030, got 2028",
    "evidence": {"admission_date": "2026-08-01", "program_duration_years": 4, "value": 2028},
    "suggested_fix": {"value": 2030, "rationale": "admission year + duration", "requires_approval": true},
    "value_masked": "2028"
  }],
  "review_summary": {"AUTO_FLAG": 0, "HUMAN_REVIEW": 0, "INFO": 0},
  "priority_summary": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
  "intake_summary": [{"program_code": "...", "approved": 60, "enrolled": 63, "supernumerary": 4, "excess": 3}],
  "reconciliation": [{"program_code": "...", "declared": 60, "uploaded": 52, "delta": -8, "status": "MISMATCH"}],
  "duplicate_clusters": [{"cluster_id": "...", "members": [{"row": 4, "apaar_masked": "1234****9012", "institution": "..."}],
                          "score": 0.93, "matched_fields": {"full_name": 0.91, "dob": 1.0, "gender": 1.0},
                          "scope": "INTRA|CROSS_INSTITUTION", "bucket": "AUTO_FLAG|HUMAN_REVIEW"}],
  "schema_drift": [{"kind": "COLUMN_REMOVED|TYPE_CHANGED|NEW_CATEGORY|NULL_RATE_JUMP", "column": "...", "previous": "...", "current": "..."}],
  "anomalies": [{"metric": "nri_share", "value": 0.4, "baseline": 0.05, "z": 6.1, "method": "zscore|isolation_forest", "reason": "..."}]
}
```

**Quality score** = `100 × (1 − Σ(weight_priority × issues) / (rows_total × max_weight))`, weights CRITICAL 10, HIGH 5, MEDIUM 2, LOW 1, clipped to [0, 100]. Same formula before and after review → the before/after report (USP 5).

---

## 6. Validation rule catalog (`contracts/rule_catalog.yaml`, owner Team C, `catalog_version` semver at top)

Each rule entry: `id, name, severity, default_priority, bucket_policy, owner, since_version, description, fix_hint`.

| ID | Sev | Priority | Check |
|---|---|---|---|
| V001 | ERROR | CRITICAL | Required column missing after column mapping |
| V002 | ERROR | CRITICAL | `apaar_id` missing or not 12 digits |
| V003 | ERROR | CRITICAL | `apaar_id` not in (mock) APAAR registry |
| V004 | WARN | HIGH | Registry name/DOB fuzzy mismatch |
| V005 | ERROR | MEDIUM→HIGH | Required field null/empty (HIGH if identity field) |
| V006 | ERROR | LOW | Invalid format (date, enum, email, mobile, ISO country) |
| V007 | ERROR | CRITICAL | Duplicate `apaar_id` within batch |
| V008 | ERROR | CRITICAL | Duplicate `institution_student_id` within institution + year |
| V009 | WARN | HIGH | Probable same person, different APAAR, same batch (fuzzy) |
| V010 | ERROR | CRITICAL | Same APAAR ACTIVE at another institution in same year **and no approved transfer** |
| V011 | WARN | HIGH | Probable same person at another institution under different APAAR |
| V012 | ERROR | HIGH | Regular-seat enrolment > `approved_intake` |
| V013 | ERROR | HIGH | Supernumerary count > allowed for scheme |
| V014 | ERROR | HIGH | Quota/nationality inconsistent (OCI/FN with IN, NRI flag mismatch) |
| V015 | ERROR | HIGH | SUPERNUMERARY without scheme, or scheme on REGULAR seat |
| V016 | WARN | MEDIUM | Age implausible for `course_level` |
| V017 | ERROR | HIGH | `admission_date` outside academic-year window |
| V018 | ERROR | HIGH | Consent missing; or under 18 without guardian consent |
| V019 | ERROR | HIGH | `program_code` not approved for institution/year (master data) |
| V020 | WARN | MEDIUM | Batch metric anomaly vs institution history |
| V021 | ERROR | HIGH | Invalid lifecycle transition (e.g. GRADUATED → ACTIVE) |
| V022 | WARN | HIGH | Uploaded counts ≠ declared statistical totals beyond tolerance (default ±2 % or ±2 students) |
| V023 | WARN | HIGH | APAAR/ID looks Excel-mangled (11 digits, scientific notation, `.0` suffix) |
| V024 | ERROR | MEDIUM | Ambiguous or unparseable date under the date policy |
| V025 | ERROR | HIGH | `expected_graduation_year` inconsistent with admission year + duration |
| V026 | ERROR | HIGH | Conflicting course/department/level for same student across rows |
| V027 | ERROR | HIGH | `year_of_study` > program duration, or lateral entry with year 1 |
| V028 | WARN | MEDIUM | Schema drift: required column disappeared / type changed vs previous batch |
| V029 | WARN | LOW | Schema drift: new unseen category value |
| V030 | WARN | HIGH | Missing-ID / null-rate jump vs previous batch |
| V031 | INFO | LOW | Formatting inconsistency (case, whitespace, title-case names) — auto-normalisable |
| V032 | WARN | HIGH | Transfer pending: APAAR active elsewhere, transfer request open |
| V033 | ERROR | HIGH | Record references institution not affiliated to stated degree-awarding body |
| V034 | WARN | MEDIUM | Student marked ACTIVE in previous year missing from this year's rollover batch |
| V035 | ERROR | CRITICAL | Batch institution ≠ authenticated uploader's institution |

**Buckets (USP 4):** `AUTO_FLAG` = deterministic rule, confidence ≥ 0.95. `HUMAN_REVIEW` = fuzzy/heuristic, 0.75 ≤ confidence < 0.95 (dedup 0.75–0.92). `INFO` = cosmetic or auto-normalisable. **No suggested fix is ever applied without a human approval** stored in the `corrections` table with who/when/old/new.

**Supernumerary limits and tolerances are configuration** (`program_intake.supernumerary_allowed`, `settings.reconciliation_tolerance`). Confirm percentages against the current AICTE Approval Process Handbook before the demo.

---

## 7. Master data (owner: Team C produces CSVs in `data/master/`; Team B loads into tables)

| Table | Columns | Source |
|---|---|---|
| `states` | `lgd_state_code, name, name_hi` | LGD (Local Government Directory) codes |
| `districts` | `lgd_district_code, lgd_state_code, name` | LGD |
| `degree_awarding_bodies` | `dab_id, name, type (UNIVERSITY/DEEMED/AUTONOMOUS_INSTITUTION), state_code, did` | synthetic |
| `institutions` | `institution_aicte_id, name, state_code, district_code, type, affiliated_dab_id, onboarding_level (FULL/AGGREGATE_ONLY), did` | synthetic, AICTE-style IDs |
| `programs` | `program_code, name, course_level, department, duration_years, lateral_allowed` | synthetic, AICTE-style |
| `academic_years` | `academic_year, start_date, end_date, admission_window_start, admission_window_end, is_current` | config |
| `enums` | `enum_name, value, label_en, label_hi` | generated from `contracts/schemas/enums.json` |

The CSV upload template (`GET /v1/templates/student-upload.xlsx`) is generated from these tables with dropdown validation in Excel and the APAAR column pre-formatted as **Text**.

---

## 8. Key design decisions (closes the judge-facing logic gaps)

### 8.1 Student lifecycle and transfers
- After commit, `enrolment_status` changes only through `POST /v1/students/{apaar_id}/transitions` (`{to_status, effective_date, reason, evidence_ref}`).
- Allowed transitions: `ACTIVE→WITHDRAWN|DEFERRED|TRANSFERRED_OUT|COMPLETED`, `DEFERRED→ACTIVE|WITHDRAWN`, `COMPLETED→GRADUATED`. Anything else → V021.
- **Transfer flow:** destination institution creates `POST /v1/transfers` (APAAR, from institution) → source institution approves/rejects (or AICTE overrides after 15 days) → on approval source record becomes `TRANSFERRED_OUT`, destination may upload with `admission_type=TRANSFER_IN`. V010 ignores APAARs with an approved transfer; an open transfer yields V032 (WARN) instead of V010.
- **Lateral entry:** `admission_type=LATERAL`, `year_of_study=2`, program must have `lateral_allowed`.

### 8.2 Holder key custody (SD-JWT key binding)
- **Decision: holder key lives in the student's browser.** Generated with WebCrypto (ECDSA P-256 / ES256, `extractable: false`), stored in IndexedDB. Public JWK sent at issuance and placed in the credential's `cnf` claim. Presentations carry a KB-JWT signed in the browser over `nonce + aud + sd_hash`.
- Lost device / cleared browser → student requests re-issue; old credential revoked, new key bound. Documented in `backend/THREAT_MODEL.md` (server never holds holder private keys; trade-off: device loss = re-issue).
- Issuer key: Ed25519 (EdDSA) per issuing body, from env, published in `/.well-known/did.json` and per-issuer `did:web` docs.

### 8.3 Corrections supersede credentials
- Any `PUT /v1/students/{apaar_id}` correction or approved correction creates a new record version (`record_version += 1`) and marks every credential issued on the old version as **SUPERSEDED** (status list bit set). Verifier sees: *"Superseded — a newer version exists, ask the holder for an updated credential."*

### 8.4 Consent withdrawal and credentials
- Purposes: `REPOSITORY`, `VERIFICATION_SHARE`, `ANALYTICS_AGGREGATE`.
- Withdrawing `VERIFICATION_SHARE` **suspends** all the student's credentials (status list suspension bit) and blocks new presentations; re-granting lifts suspension. Verification of a suspended credential returns *"Holder has withdrawn consent"* without revealing data.
- Withdrawing `REPOSITORY` consent: PII fields are pseudonymised (name/contact removed, APAAR replaced by a keyed hash) while counts remain for statutory aggregate statistics. Flag in the threat model that real deployment needs a legal-basis review under the DPDP Act 2023.

### 8.5 Reconciliation with statistical totals + aggregate-only mode
- `declared_totals` stores what institutions declared at approval. Engine compares uploaded student-level counts per program/year → V022 + reconciliation table in BatchReport and AICTE dashboard.
- Institutions with `onboarding_level=AGGREGATE_ONLY` submit totals via `POST /v1/aggregates` (and a UI form). Dashboards show **coverage %** = institutions with student-level data / all institutions.

### 8.6 Affiliation and certificate issuer
- Institutions are affiliated to a degree-awarding body (DAB). **Enrolment credential** issuer = institution. **Degree certificate** issuer = DAB (or the institution itself if autonomous/deemed). AICTE publishes the trust list of issuer DIDs. Certificates print APAAR ID + institution student ID + verification QR (PS requirement 10).

### 8.7 Batch concurrency and supersede
- Batch states: `UPLOADED → MAPPING → VALIDATING → VALIDATED → (IN_REVIEW) → COMMITTED | REJECTED | SUPERSEDED | FAILED`.
- At most **one non-terminal batch per (institution, academic_year, program set)**; a new upload with `supersedes_batch_id` marks the old one SUPERSEDED.
- Commit takes a Postgres advisory lock on `(institution_aicte_id, academic_year)` and checks `batch.version` (optimistic). Uploads accept an `Idempotency-Key` header (24 h).

### 8.8 Academic-year rollover
- `POST /v1/admin/rollover` (AICTE_ADMIN) for `from_year → to_year`: ACTIVE students get a provisional next-year row with `year_of_study+1` unless at final year (→ `COMPLETED`). Institutions confirm via the next upload; missing students raise V034.

### 8.9 Parser policy (engine)
- Read every cell as **string** (`dtype=str`, `keep_default_na=False`; openpyxl reads raw cell values, numeric IDs are flagged V023).
- Date policy: canonical ISO `YYYY-MM-DD`. Accepted inputs: ISO, `DD-MM-YYYY`, `DD/MM/YYYY`, `DD.MM.YYYY` (Indian default), Excel date-typed cells. **`MM/DD/YYYY` is never assumed.** Ambiguous/unparseable → V024 with the parsed candidates as evidence.
- Encoding detection (`charset-normalizer`), BOM strip, header normalisation, row-level error capture (never crash on a bad row).

### 8.10 Notifications
- `notifications_outbox` table + worker: email via SMTP (Mailpit locally, any SMTP on Render), SMS through an adapter stub (logs only). Events: batch completed, review needed, transfer request, consent change, credential revoked.

---

## 9. Roles and RBAC

| Role | Can |
|---|---|
| `AICTE_ADMIN` | Everything; manage institutions, master data, rule config, rollover, trust list |
| `AICTE_ANALYST` | Read all aggregates/records (PII masked), run reports, resolve cross-institution flags |
| `DAB_ADMIN` | Issue degree credentials for affiliated institutions' graduates |
| `INSTITUTION_ADMIN` | Upload/fix/commit own batches, approve corrections, transfers, users, API keys, webhooks, issue enrolment credentials |
| `INSTITUTION_STAFF` | Upload, map columns, view own batches, propose corrections |
| `VERIFIER` | Verify presented credentials; no browsing |
| `STUDENT` | View own record, manage consent, hold keys, create selective-disclosure presentations |

Every endpoint declares its roles via `Depends(require_roles(...))`. Every PII read, every verification and every state change writes an audit row. API keys are scoped to one institution and to `upload`/`read` scopes.

---

## 10. USP → feature map

| USP | Where | Owner |
|---|---|---|
| 1 Field-level explainable verification | Issue model (`reason`, `evidence`, `suggested_fix`) + issue cards UI | C, A |
| 2 Intelligent duplicate detection | Name normalisation + Jaro-Winkler/token-set + phonetic + DOB/gender blocking; `matched_fields` + score; side-by-side compare | C, A |
| 3 Cross-field / cross-record consistency | V014, V015, V017, V025, V026, V027 | C |
| 4 Confidence-based human review | `bucket` + `confidence`; corrections require approval | C, B, A |
| 5 Before/after DQ report | `quality_score_before/after`, resolved/pending counts, XLSX/PDF | C, B, A |
| 6 Smart column mapping | `column_synonyms.yaml` + fuzzy header match + confirm UI + saved mapping profiles | C, B, A |
| 7 Schema-drift detection | V028–V030 vs previous committed batch | C |
| 8 Risk-based prioritisation | `priority` CRITICAL/HIGH/MEDIUM/LOW, sorted issue queue | C, A |
| Innovation | Anomaly detection (z-score + IsolationForest), SSE real-time, SD-JWT selective disclosure, hash-chained audit | C, B |

## 11. PS requirement → feature map (judges' checklist)

| # | Requirement | Feature |
|---|---|---|
| 1 | Secure upload/update API on APAAR | `POST /v1/batches`, `PUT /v1/students/{apaar_id}`, API keys, idempotency |
| 2 | Intake, enrolment, supernumerary, NRI/OCI/FN fields | Schema §5 + `program_intake` + `declared_totals` |
| 3 | Duplicates, invalid APAAR, excess intake, inconsistencies, cross-institution duplicates | V001–V035, dedup engine |
| 4 | Real-time dashboards | AICTE console + institution dashboard + SSE |
| 5 | Secure verification for stakeholders | Verifier portal, `POST /v1/verify`, VERIFIER role |
| 6 | Verifiable records linked to identity | SD-JWT VC bound to APAAR + holder key |
| 7 | Integration | OpenAPI 3.1, API keys, webhooks (HMAC), bulk export |
| 8 | Security, privacy, auth, RBAC, audit, consent | §8, §9, audit chain, encryption, masking |
| 9 | Reports | Policy/accreditation report builder (PDF/XLSX), DQ report |
| 10 | APAAR + student ID on certificates | Certificate template with QR |

---

## 12. Engineering standards

- **Workflow per task:** Brainstorm → Plan (checklist in PR description) → Work → Review. If your Antigravity workspace has the skills `/ce-brainstorm`, `/ce-plan`, `/ce-work`, `/caveman`, use them in that order; otherwise do the same steps manually.
- **Models:** fast/cheap model (Haiku-class) for web research and doc reading; strong coding model (Sonnet-class) for implementation and review.
- **Tests are part of done:** engine pytest (fixtures in `data/fixtures/`), backend pytest + httpx + **schemathesis** against `contracts/openapi.yaml`, frontend Vitest (incl. empty / error / offline states for every page) + Playwright smoke.
- **Security CI (`security.yml`):** `bandit -r backend engine`, `pip-audit`, `npm audit --audit-level=high`, ZAP baseline scan against the Render staging URL on `main`.
- **Never use real student data.** Synthetic only (`data/` generator) + public datasets in §13.
- **Never log raw APAAR or PII.** Use `mask_apaar()` → `1234****9012`, `mask_email()`, `mask_mobile()`.
- **Secrets** only in env vars; ship `.env.example`.
- **Commits:** Conventional Commits, e.g. `feat(engine): add V025 graduation-year rule`. One feature per PR.
- **Definition of done:** tests + lint pass, endpoint in OpenAPI, localhost link works, demo path in `runthrough.md` still works.
- **Accessibility:** WCAG AA; keyboard navigable; masked PII by default; English + Hindi.
- **India map:** use only official boundaries — state shapefiles from the Survey of India Online Maps portal (onlinemaps.surveyofindia.gov.in), converted to simplified GeoJSON with `mapshaper` and keyed by LGD state code; check the licence terms before shipping. Until that file is in `frontend/public/geo/`, use a state tile-grid/bar chart fallback. Never ship Natural Earth or random GitHub boundaries.
- **Agent output:** terse. Plans as checklists, code over prose.

---

## 13. Research basis

Verified by a research pass on 2026-10-23. Status column: ✅ confirmed · 🟡 likely · ❓ verify by hand before citing.

| Source | How we use it | Status |
|---|---|---|
| HF `neuralsorcerer/student-performance` (CC0, 26 cols, ~100M rows) | Value ranges, consistency patterns, 50k-row load-test sample | ✅ |
| `drsanjayagal/UniversityIntake-MLDataset` (CC BY 4.0, ~29 cols: gender, age, category, state, urban_rural, marks, income, first-gen…) | Intake-side fields, MCAR/MAR missing-value fixtures, category/state/age mapping | 🟡 |
| `drsanjayagal/SynEdu-HEDL` (20k synthetic students, 6 tables incl. STUDENT_PROFILE with `student_id`, `enrollment_year`) / Zenodo 10.5281/zenodo.18884938 | Multi-table referential integrity, duplicate-enrolment test model | 🟡 licence not shown on repo page — cite Zenodo record, check licence there |
| Schelter et al., *Automating Large-Scale Data Quality Verification* (Deequ, PVLDB 11, 2018) | Constraint types (completeness, uniqueness, compliance), metric history, anomaly detection on metrics, constraint suggestion → V020, V028–V030, quality score | ✅ |
| Christen, *A Survey of Indexing Techniques for Scalable Record Linkage and Deduplication* (IEEE TKDE 24(9), 2012; ANU repository link) | Blocking (APAAR exact, then DOB+gender+phonetic key) before fuzzy compare | ✅ |
| ScienceDirect S0306437912001470 (Information Systems, 2013) — expected: Vatsalan, Christen, Verykios, *A taxonomy of privacy-preserving record linkage techniques* | Privacy classification; future Bloom-filter linkage across bodies | ❓ page blocked; confirm title |
| Berrios Moya, Ayoade, Uddin, *A ZKP-Enabled Blockchain-Based Academic Record Verification System* (Sensors 25(11):3450, 2025) — zkEVM, DIDs, IPFS | Motivation for selective disclosure; we use SD-JWT now, ZK predicates as stretch | 🟡 |
| Springer s10639-024-12493-6 (Education and Information Technologies, 2024) | Institution authentication, issuance, third-party verification, auditability | ❓ paywalled; read manually |
| Rustemi, Dalipi, Atanasovski, Risteski, *A Systematic Literature Review on Blockchain-Based Systems for Academic Certificate Verification* (IEEE Access 11, 2023, DOI 10.1109/ACCESS.2023.3289598) — 34 studies from 1,744, PRISMA | Literature review, existing-solution comparison, gap justification | ✅ |
| APAAR (apaar.education.gov.in): 12-digit ID, consent-based (parental consent for minors), shown in DigiLocker | V002, V018, consent ledger | ✅ (ABC link: 🟡) |

**Library versions to pin (check with `pip index versions` / `npm view` at Phase 0):** Python `sd-jwt` (OpenWallet Foundation, 0.10.x) wrapped behind `backend/app/vc/sdjwt.py` so it can be swapped for a hand-rolled implementation if its KB-JWT API is insufficient; npm `@sd-jwt/sd-jwt-vc` + `@sd-jwt/core` (0.19–0.20 line); `splink` **4.x stable** (5.x is pre-release — do not use) as an optional extra.

**Design decision:** SD-JWT + Ed25519 + hash-chained audit log gives selective disclosure, issuer authenticity and tamper evidence without blockchain cost. ZK predicate proofs and Merkle anchoring of batch hashes are stretch goals. No public APAAR API → **mock APAAR registry** behind an `ApaarRegistry` interface, swappable later.
