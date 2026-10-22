# agents.md — APAAR-SDMS (APAAR-based Student Data Management & Verification System)

> Read this file before every task. It is the shared source of truth for all 3 teams and every AI agent working in this repo (Antigravity, Claude, etc.).
> The step-by-step build order and the per-phase prompts are in `steps.md`.

---

## 1. What we are building (one paragraph)

A platform that lets AICTE-approved institutions upload student-level admission data (CSV/Excel or API), keyed by **APAAR ID**. Every upload is validated automatically (format, missing fields, duplicates, intake limits, NRI/OCI/FN consistency, cross-institution duplicate enrolment). An anomaly engine scores each upload. Clean records go into a central AICTE repository. AICTE and institutions get live dashboards and reports. Students can share a **signed, selectively disclosable verifiable record** (SD-JWT credential plus QR code) with employers or regulators, who verify it without seeing the full record. Every action is consent-gated, role-checked and written to a tamper-evident audit log.

**Pipeline (from the PS):**
`Institution → Upload → APAAR Validation → Data Verification → AICTE Central Repository → Analytics & Monitoring → Authorized Verification`

---

## 2. Requirement → feature map (the judges' checklist)

| # | PS requirement | Our feature | Owner |
|---|---|---|---|
| 1 | Secure upload/update API keyed on APAAR | `POST /v1/batches` (CSV/XLSX), `PUT /v1/students/{apaar_id}`, API keys for institutions | B (API), A (parsing) |
| 2 | Fields: approved intake, actual enrolment, supernumerary, NRI, OCI, FN, others | Canonical schema (§5) + `program_intake` table | A (schema), B (DB) |
| 3 | Validation: duplicates, invalid/missing APAAR, intake exceeded, inconsistencies, cross-institution duplicates | Rule engine with rule IDs `V001–V020` (§6) + record-linkage dedup | A |
| 4 | Real-time dashboards for AICTE and institutions | React dashboards + server-sent events on batch completion | C (UI), B (events) |
| 5 | Secure verification for AICTE, institutions, employers, regulators | Verifier portal + `POST /v1/verify` + role `VERIFIER` | B (logic), C (UI) |
| 6 | Verifiable student records linked to academic identity | SD-JWT Verifiable Credential signed with the institution key and countersigned by AICTE; QR code | B |
| 7 | Integration with existing systems | OpenAPI 3.1 spec, API keys, webhooks, bulk import | B |
| 8 | Security, privacy, auth, RBAC, audit, consent | JWT + RBAC, consent ledger, hash-chained audit log, PII masking, field encryption | B |
| 9 | Reports for policy, accreditation, monitoring | PDF/XLSX report generator + batch data-quality report | A (DQ report), C (policy reports) |
| 10 | APAAR ID and student ID printed on certificates | Certificate template with APAAR, student ID and verification QR | C (template), B (signing) |
| Innovation | Anomaly detection, real-time monitoring, selective disclosure | Deequ-style metric history + Isolation Forest + Splink fuzzy dedup + SD-JWT | A + B |

---

## 3. Team split (3 teams, no overlapping files)

| Team | Name | Owns (writes only here) | Mission |
|---|---|---|---|
| **A** | Data & Intelligence | `engine/`, `data/`, `contracts/rule_catalog.yaml` | Parsing, validation rules, dedup/record linkage, anomaly detection, batch data-quality reports, synthetic test data |
| **B** | Platform & Trust | `backend/`, `contracts/openapi.yaml`, `contracts/schemas/`, `docker-compose.yml`, `infra/` | API, DB, auth/RBAC, consent, audit log, central repository, verifiable credentials, verification API, integrations |
| **C** | Experience & Insights | `frontend/`, `docs/`, `reports/templates/`, `demo/` | Dashboards (AICTE, institution, verifier, student), report UI, certificate template, literature review, pitch deck, demo script |

**Rule:** a team may *read* any folder but writes only to its own. To change a shared contract in `contracts/`, open a PR tagged `contract-change` and get approval from the owning team plus one other team.

---

## 4. Architecture and tech stack (fixed; do not swap without a contract-change PR)

```
            ┌───────────────────── Frontend (Team C) ─────────────────────┐
            │ React 18 + Vite + TypeScript + Tailwind + shadcn/ui + Recharts│
            │ Institution portal │ AICTE console │ Verifier portal │ Student │
            └───────────────▲─────────────────────────────────────────────┘
                            │ REST (OpenAPI) + SSE
            ┌───────────────┴──────── Backend (Team B) ───────────────────┐
            │ FastAPI (Python 3.11) · SQLAlchemy 2 · Alembic · Pydantic v2 │
            │ Auth (JWT + API keys) · RBAC · Consent · Audit chain        │
            │ VC issuer/verifier (SD-JWT, Ed25519) · Mock APAAR registry  │
            │ Celery/RQ worker (or FastAPI BackgroundTasks for the demo)  │
            └──────┬──────────────────────────────┬───────────────────────┘
                   │ imports Python package       │
            ┌──────▼───────── Engine (Team A) ─────┐   ┌──────────────────┐
            │ apaar_engine: pandas + pandera       │   │ PostgreSQL 16    │
            │ rapidfuzz + indic-soundex + Splink   │   │ (SQLite fallback)│
            │ (DuckDB) · scikit-learn IsolationForest│  │ Redis (queue)    │
            └──────────────────────────────────────┘   └──────────────────┘
```

- **Language:** Python 3.11 for engine and backend; TypeScript for frontend.
- **Validation:** `pandas` + `pandera` (Deequ-style constraints: completeness, uniqueness, compliance, size, statistics).
- **Dedup:** exact APAAR blocking, then `Splink` (DuckDB backend, Fellegi-Sunter) or `recordlinkage` for fuzzy matching, `rapidfuzz` (Jaro-Winkler, token-set), and `indic-soundex` for Indian names.
- **Anomaly:** per-institution metric history with z-score/rate-of-change (Deequ idea) plus `IsolationForest` on institution-level features.
- **Credentials:** W3C VC data model as **SD-JWT** signed with Ed25519. Issuer keys published at `/.well-known/did.json` (did:web). Revocation via a status list. No blockchain in the MVP; an optional Merkle root per batch is a stretch goal.
- **Audit:** append-only `audit_log` table in which each row stores `prev_hash` and `hash = sha256(prev_hash + payload)`.
- **Run:** `docker compose up` brings up db, redis, backend and frontend.

---

## 5. Canonical data contract (`contracts/schemas/student_record.json`)

All teams code against these field names exactly (snake_case).

### 5.1 `student_record` (one row per student per program per academic year)

| Field | Type | Required | Rule notes |
|---|---|---|---|
| `apaar_id` | string(12) | yes | Exactly 12 digits. Internal structure is **not officially confirmed**, so treat any structure check as a warning only |
| `institution_aicte_id` | string | yes | Must match the uploader's institution |
| `institution_student_id` | string | yes | Roll/enrolment number; unique within institution + year |
| `full_name` | string | yes | Normalised copy stored in `name_norm` |
| `dob` | date (YYYY-MM-DD) | yes | Age plausible for `course_level` |
| `gender` | enum M/F/T | yes | |
| `category` | enum GEN/EWS/OBC-NCL/SC/ST | yes | |
| `pwd` | bool | no | |
| `program_code` | string | yes | Must exist in `program_intake` |
| `course_level` | enum DIPLOMA/UG/PG/PGDM/PHD | yes | |
| `academic_year` | string `2026-27` | yes | |
| `admission_date` | date | yes | Inside the academic-year window |
| `admission_type` | enum REGULAR/LATERAL/TRANSFER | yes | |
| `seat_type` | enum REGULAR/SUPERNUMERARY | yes | |
| `supernumerary_scheme` | enum TFW/PMSSS/JK/NE/FN_OCI_NRI/OTHER/null | if SUPERNUMERARY | |
| `quota` | enum NONE/NRI/OCI/FN/PIO/CIWG | yes | |
| `nationality` | ISO-3166 alpha-2 | yes | |
| `nri_status` | bool | yes | Consistent with `quota` and `nationality` |
| `oci_status` | bool | yes | OCI ⇒ nationality ≠ IN |
| `fn_status` | bool | yes | FN ⇒ nationality ≠ IN |
| `enrolment_status` | enum ACTIVE/WITHDRAWN/DEFERRED/COMPLETED | yes | |
| `consent_status` | enum GRANTED/REFUSED/WITHDRAWN | yes | |
| `consent_date` | date | if GRANTED | |
| `guardian_consent` | bool | if age < 18 | |
| `email`, `mobile` | string | no | Stored encrypted and masked in UI |

### 5.2 `program_intake`

`institution_aicte_id, program_code, academic_year, approved_intake, supernumerary_allowed (JSON per scheme), approval_letter_ref`

### 5.3 `BatchReport` (engine output, Pydantic model in `engine/apaar_engine/models.py`)

```json
{
  "batch_id": "uuid", "institution_aicte_id": "...", "rows_total": 0,
  "rows_valid": 0, "rows_warning": 0, "rows_error": 0,
  "quality_score": 0.0,
  "metrics": {"completeness": {"col": 0.99}, "uniqueness": {"apaar_id": 1.0}},
  "issues": [{"row": 12, "field": "apaar_id", "rule_id": "V002", "severity": "ERROR", "message": "...", "value_masked": "1234****9012"}],
  "intake_summary": [{"program_code": "...", "approved": 60, "enrolled": 63, "supernumerary": 4, "excess": 3}],
  "duplicate_clusters": [{"cluster_id": "...", "apaar_ids": [], "score": 0.93, "scope": "INTRA|CROSS_INSTITUTION"}],
  "anomalies": [{"metric": "nri_share", "value": 0.4, "baseline": 0.05, "z": 6.1, "reason": "..."}]
}
```

---

## 6. Validation rule catalog (`contracts/rule_catalog.yaml`, owned by Team A)

| ID | Severity | Check |
|---|---|---|
| V001 | ERROR | Required column missing from file header |
| V002 | ERROR | `apaar_id` missing or not 12 digits |
| V003 | ERROR | `apaar_id` not found in the (mock) APAAR registry |
| V004 | WARN | APAAR registry name/DOB does not match the uploaded name/DOB (fuzzy) |
| V005 | ERROR | Required field null or empty |
| V006 | ERROR | Invalid format (date, enum, email, mobile, ISO country) |
| V007 | ERROR | Duplicate `apaar_id` within the batch |
| V008 | ERROR | Duplicate `institution_student_id` within institution and year |
| V009 | WARN | Probable duplicate person in the batch with a different APAAR (fuzzy name + DOB) |
| V010 | ERROR | Same APAAR ACTIVE at another institution in the same academic year |
| V011 | WARN | Probable same person at another institution under a different APAAR |
| V012 | ERROR | Regular-seat enrolment > `approved_intake` for the program |
| V013 | ERROR | Supernumerary count > allowed for that scheme |
| V014 | ERROR | Quota/nationality inconsistent (OCI or FN with IN, NRI flag mismatch) |
| V015 | ERROR | `seat_type=SUPERNUMERARY` with no scheme, or a scheme on a regular seat |
| V016 | WARN | Age implausible for `course_level` |
| V017 | ERROR | `admission_date` outside the academic-year window |
| V018 | ERROR | `consent_status` missing; or under 18 without `guardian_consent` |
| V019 | ERROR | `program_code` not in approved programs |
| V020 | WARN | Batch metric anomaly vs. institution history (null rate, NRI share, intake fill jump) |

Supernumerary limits per scheme are **configuration**, not hard-coded. Load them from `program_intake.supernumerary_allowed` and confirm the percentages against the current AICTE Approval Process Handbook.

---

## 7. Roles and RBAC

| Role | Can |
|---|---|
| `AICTE_ADMIN` | Everything; manage institutions, keys and rule configuration |
| `AICTE_ANALYST` | Read all aggregates and records (PII masked), run reports, resolve flags |
| `INSTITUTION_ADMIN` | Upload and fix own batches, manage own users and API keys, issue credentials |
| `INSTITUTION_STAFF` | Upload and view own batches |
| `VERIFIER` (employer, regulator) | Verify presented credentials; no browsing |
| `STUDENT` | View own record, manage consent, generate selective-disclosure presentations |

Every endpoint declares its roles. Every read of PII and every verification writes an audit row.

---

## 8. Agent working rules (for every AI agent in Antigravity)

1. **Workflow per task: Brainstorm → Plan → Work → Review.** Write the plan as a checklist in the PR description before coding. Do not code without a plan.
2. **Models:** use a fast, cheap model for web research and doc reading, and a stronger coding model for implementation and review.
3. **Stay in your folder** (§3). Contracts change only via PR.
4. **Tests are part of done.** Engine: pytest with fixtures in `data/fixtures/`. Backend: pytest + httpx. Frontend: Vitest plus one Playwright smoke test.
5. **Never use real student data.** Use only synthetic data from `data/synthetic/` (Team A generator) and the public datasets in §9.
6. **Never log raw APAAR IDs or PII.** Use `mask_apaar()` (`1234****9012`).
7. **Secrets** go in `.env` (not committed); ship `.env.example`.
8. **Commits:** Conventional Commits (`feat(engine): add V012 intake rule`). One feature per PR.
9. **Definition of done:** tests pass, lint passes (ruff/eslint), endpoint documented in OpenAPI, demo path still works.
10. **Be terse in agent output:** short plans, no filler, code over prose.

---

## 9. Research basis (what we learned and how we use it)

| Source | Use in project | Status |
|---|---|---|
| HF `neuralsorcerer/student-performance` (CC0, 26 cols, ~100M rows) | Value ranges and a consistency rule pattern; sample about 50k rows for load tests | Schema from viewer |
| `drsanjayagal/UniversityIntake-MLDataset` (CC BY 4.0, 28 cols, injected MCAR/MAR gaps) | Intake-side fields; missing-value test fixtures; `category`, `state`, `age` mapping | Run its generator to get CSVs |
| `drsanjayagal/SynEdu-HEDL` / Zenodo 10.5281/zenodo.18884938 (CC BY 4.0, 20k students) | Multi-table referential-integrity and duplicate-enrolment test model (`student_id`, `enrollment_year`, `program`) | Cite Zenodo copy; column count conflicts (85 vs ~60) |
| Schelter et al., *Automating Large-Scale Data Quality Verification* (VLDB 2018, Deequ) | Constraint types, incremental metric states, anomaly detection on metric history, constraint suggestion | PDF not machine-readable; based on Deequ docs |
| Christen, *Survey of Indexing Techniques for Record Linkage* (TKDE 2012, ANU) | Blocking strategy for cross-institution dedup | Abstract only |
| Vatsalan, Christen, Verykios, *Taxonomy of PPRL* (Inf. Systems 2013) | Privacy-preserving linkage; future work on Bloom-filter linkage across bodies | Abstract only; DOI match unconfirmed |
| Berrios Moya et al., *ZKP-Enabled Blockchain Academic Record Verification* (Sensors 2025) | Selective disclosure motivation; DID-based issuer trust | Abstract only |
| Rustemi et al., *SLR on Blockchain Certificate Verification* (IEEE Access 2023, 34 studies) | Literature review and gap justification | **Confirm IEEE doc ID 10163764 matches this paper** |
| Springer s10639-024-12493-6 | Issuance, third-party verification, auditability | **Not accessible; read manually** |
| APAAR ID: 12 digits, MoE, DigiLocker/ABC linked, consent-based (opt-in, withdrawable) | V002, V018, consent ledger | Secondary sources; confirm at apaar.education.gov.in |

**Design decision:** SD-JWT plus Ed25519 plus a hash-chained audit log gives selective disclosure, issuer authenticity and tamper evidence without blockchain cost. ZK predicate proofs (for example "enrolled AND not FN") and Merkle anchoring are stretch goals. No public APAAR API is available to us, so Team B ships a **mock APAAR registry** seeded from synthetic data behind an adapter interface that can be swapped later.

---

## 10. Master prompts per team (paste one into each team's Antigravity workspace)

### Team A — Data & Intelligence

```
You are the Team A agent for APAAR-SDMS. Read agents.md and steps.md first; they are binding.
You own ONLY: engine/, data/, contracts/rule_catalog.yaml.
Goal: build the Python package `apaar_engine` that turns an uploaded CSV/XLSX plus intake data into a BatchReport (agents.md §5.3), implementing every rule V001–V020 (§6).
Stack: Python 3.11, pandas, pandera, openpyxl, rapidfuzz, indic-soundex, splink (duckdb), scikit-learn, pydantic v2, pytest.
Deliverables:
1. Synthetic data generator (data/synthetic/generate.py): N institutions, programs with approved intake, students with valid APAARs, plus seeded defects (bad APAAR, nulls, intra/cross duplicates, transliterated names, over-intake, OCI-with-IN, missing consent). Emit a ground-truth defects file.
2. Public-dataset adapters: map UniversityIntake and SynEdu-HEDL columns to our schema for fixtures.
3. Parser: CSV/XLSX, header normalisation, encoding detection, row-level error capture (never crash on a bad row).
4. Rule engine: one function per rule, registered from rule_catalog.yaml, vectorised in pandas.
5. Dedup: exact APAAR blocking, then Splink/rapidfuzz fuzzy on name_norm + dob + gender with Indian-name normalisation (strip honorifics, token-set, initials, indic-soundex). Thresholds: >=0.92 auto-flag, 0.75-0.92 review queue.
6. Anomaly: Deequ-style metric states per institution per batch; z-score/rate-of-change vs history; IsolationForest on institution features (fill ratio, supernumerary share, NRI/OCI/FN share, duplicate rate, upload latency).
7. Batch data-quality report: quality_score, per-column completeness/validity, issue list, intake summary; export JSON + XLSX (+ PDF via the backend).
8. Public API: `validate_batch(file_or_df, intake_df, registry, history) -> BatchReport`; stays pure (no DB, no HTTP).
Measure precision/recall of the defect detection against the ground truth and print it in tests.
Workflow: brainstorm → write plan checklist → implement → pytest → review. Keep output terse.
```

### Team B — Platform & Trust

```
You are the Team B agent for APAAR-SDMS. Read agents.md and steps.md first; they are binding.
You own ONLY: backend/, contracts/openapi.yaml, contracts/schemas/, docker-compose.yml, infra/.
Goal: a FastAPI backend that is the AICTE central repository and trust layer.
Stack: Python 3.11, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 (SQLite fallback), Redis + RQ (or BackgroundTasks), PyJWT, passlib/argon2, cryptography (Ed25519), an sd-jwt library, qrcode, WeasyPrint for PDF.
Deliverables:
1. contracts/openapi.yaml FIRST (Phase 0) so Team C can mock it.
2. DB models: institutions, users, api_keys, programs/program_intake, batches, student_records, issues, duplicate_flags, consent_ledger, credentials, revocations, audit_log, metric_history.
3. Auth: JWT login for humans; API keys (hashed) for institution systems; RBAC dependency per endpoint (roles in agents.md §7).
4. Upload flow: POST /v1/batches (multipart) → store file → async job calls apaar_engine.validate_batch → persist report → SSE event `batch.completed`. Institutions fix and re-submit; only valid rows go to the central repository.
5. Mock APAAR registry service behind an `ApaarRegistry` interface (lookup, verify name/dob), seeded from Team A synthetic data.
6. Consent ledger: grant/withdraw per purpose (REPOSITORY, VERIFICATION_SHARE); verification is blocked without consent.
7. Hash-chained audit log + GET /v1/audit/verify-chain that proves no tampering.
8. Verifiable credentials: issue SD-JWT VC (institution key signs, AICTE trust list), /.well-known/did.json, status list revocation, POST /v1/verify (signature, issuer trusted, not revoked, disclosed claims), QR payload for certificates (APAAR + institution_student_id + verify URL).
9. Integration: webhooks to institution systems, bulk export for AICTE, idempotency keys on uploads, rate limiting.
10. Field encryption for email/mobile; PII masking in all responses for non-owners.
Workflow: brainstorm → plan checklist → implement → pytest + httpx tests → review. Keep output terse.
```

### Team C — Experience & Insights

```
You are the Team C agent for APAAR-SDMS. Read agents.md and steps.md first; they are binding.
You own ONLY: frontend/, docs/, reports/templates/, demo/.
Goal: the UI every stakeholder sees, plus the reports, literature review and demo.
Stack: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Router, Recharts, react-dropzone, MSW (mock API from contracts/openapi.yaml until the backend is ready), Vitest, Playwright.
Deliverables:
1. Institution portal: drag-drop CSV/XLSX upload with template download, live progress, issue table (filter by rule/severity, row deep-link), fix-and-resubmit, intake-vs-enrolment cards, DQ score trend.
2. AICTE console: national map/state drilldown, intake fill %, excess enrolment leaderboard, supernumerary/NRI/OCI/FN breakdown, cross-institution duplicate queue with side-by-side compare and resolve, anomaly feed (real-time via SSE), audit chain status badge.
3. Verifier portal: scan QR / paste credential → green/red result with only disclosed fields, issuer name, timestamp.
4. Student view: own record, consent toggles, "share selected fields" builder that creates a presentation and QR.
5. Reports: policy/accreditation report builder (filters: year, state, program, category) → PDF/XLSX; certificate template showing APAAR ID + student ID + QR.
6. docs/literature_review.md: comparison table of existing approaches (from agents.md §9) vs ours, gaps we close.
7. demo/: 5-minute demo script, seed scenario, pitch deck outline, architecture diagram.
Design: clean government-portal look, accessible (WCAG AA), mobile friendly, masked PII by default.
Workflow: brainstorm → plan checklist → implement → Vitest/Playwright → review. Keep output terse.
```
