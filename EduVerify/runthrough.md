# runthrough.md — How EduVerify is used, end to end

> A guided tour of the finished app, one actor at a time, in the order the PS pipeline flows:
> `Institution → Upload → APAAR Validation → Data Verification → AICTE Central Repository → Analytics & Monitoring → Authorized Verification`
> Use it as the demo script skeleton (Team A turns it into `demo/demo_script.md`) and as the final acceptance test (rc-1).

---

## 0. Start the stack

```bash
cp .env.example .env
docker compose up -d db mailpit
cd backend && alembic upgrade head && python -m app.seed --if-empty && uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm ci && npm run dev
```

| What | Local URL | Hosted (Render) |
|---|---|---|
| Web app | http://localhost:5173 | `https://eduverify-web.onrender.com` |
| API docs | http://localhost:8000/docs | `https://eduverify-api.onrender.com/docs` |
| Health | http://localhost:8000/healthz | `…/healthz` |
| Email inbox (notifications) | http://localhost:8025 | your SMTP inbox |

**Seeded demo users** (password = `SEED_PASSWORD` from your `.env`):

| Role | Email | Lands on |
|---|---|---|
| AICTE_ADMIN | `aicte.admin@demo.local` | `/aicte` |
| AICTE_ANALYST | `aicte.analyst@demo.local` | `/aicte` |
| INSTITUTION_ADMIN | `inst.admin@demo.local` (Demo Institute of Technology) | `/institution` |
| INSTITUTION_STAFF | `inst.staff@demo.local` | `/institution` |
| INSTITUTION_ADMIN (neighbour) | `inst2.admin@demo.local` | `/institution` |
| DAB_ADMIN | `dab.admin@demo.local` (Demo State University) | `/dab` |
| STUDENT | `student@demo.local` | `/student` |
| VERIFIER | `verifier@demo.local` (employer) | `/verify` |

Demo files: `data/demo/batch_1_clean.csv`, `batch_2_errors.xlsx`, `batch_3_cross_dupes.csv`, `batch_4_anomaly_drift.csv`.

---

## 1. Institution staff: upload student data (PS req 1, 2, USP 6)

1. Open http://localhost:5173/login → sign in as **inst.staff**.
2. Go to **Upload** (`/institution/upload`). Choose academic year **2026-27**.
3. Click **Download template**. Open it: dropdowns for category/quota/seat type, APAAR column formatted as text, Hindi instructions. (Institutions that already have their own sheet can skip this.)
4. Drop **`batch_2_errors.xlsx`**. This file uses the department's own headers: `PRN`, `DOB`, `Dept`, `APAAR No`.
5. **Map columns** screen: EduVerify suggests `PRN → institution_student_id (synonym, 0.98)`, `DOB → dob`, `Dept → department`, `APAAR No → apaar_id`. Tick **Save as my institution's mapping profile** → **Confirm**.
6. **Validate** screen: the progress bar moves live through Parsing → Mapping → Rules → Duplicates → Anomalies → Report (server-sent events).
7. **Summary**: quality score (e.g. 71/100), rows valid/warning/error, issues by priority (CRITICAL/HIGH/MEDIUM/LOW) and by bucket (Auto-flagged / Needs review / Info), intake cards per program (**B.Tech CSE: approved 60, enrolled 63 → excess 3** in red), reconciliation strip (declared 60 vs uploaded 63).

*Behind the scenes:* `POST /v1/batches` → file stored in Postgres → job runs `eduverify_engine.validate_batch` with master data, intake, declared totals, mock APAAR registry, central snapshot and history → BatchReport saved → `batch.validated` event.

---

## 2. Institution: review and fix (USP 1, 3, 4, 8)

1. Click **Review issues** (`/institution/batches/<id>/review`). Issues are already sorted **CRITICAL first**.
2. Open a **CRITICAL** issue: *V002 — APAAR must be 12 digits*. The drawer shows the field, the masked value, the reason, and the evidence. Another: *V023 — APAAR looks Excel-mangled (11 digits)*, with a suggested fix that adds the leading zero back, because the registry confirms the padded value.
3. Open a **HIGH** issue: *V025 — Graduation year 2028 inconsistent: admission 2026 + B.Tech 4 years ⇒ expected 2030*. Suggested fix: 2030. As **staff** you can only **Propose**.
4. Other examples you will see: V014 (OCI student with nationality IN), V015 (supernumerary seat without scheme), V018 (minor without guardian consent), V026 (same roll number with two departments), V024 (ambiguous date `03/04/2026` with both readings in the evidence).
5. **Info** tab: formatting fixes (extra spaces, ALL CAPS names). Staff can propose all of them in bulk.
6. Sign out, sign in as **inst.admin**. Open the same batch → **Approve** the proposed fixes (each approval stored with who/when/old/new). Nothing in the data changed before this step.
7. **Duplicates** tab: cluster *"Rahul Sharma" vs "Rahul S. Sharma"*, score 0.88 → **Needs human review**. Side-by-side view: name 0.91, DOB 1.0, gender 1.0, mobile hash match. Choose **Same person** (or **Different people**).
8. Click **Re-validate** → **Before/After**: quality score **71 → 96**, resolved 38, pending 2, per-priority bars. **Download DQ report** (XLSX/PDF) for the institution's records (USP 5).
9. **Commit** becomes enabled once no CRITICAL issue is open. Confirm → rows with unresolved errors are listed as excluded → batch **COMMITTED** → records enter the **AICTE Central Repository**.
10. Check http://localhost:8025: "Batch committed" email. If a webhook is registered, the institution's ERP receives a signed `batch.committed` event.

---

## 3. Cross-institution duplicate and transfer (PS req 3, lifecycle gap)

1. Sign in as **inst2.admin** (neighbour institution) and upload **`batch_3_cross_dupes.csv`**.
2. Result: **V010 CRITICAL** — an APAAR in this file is already ACTIVE at Demo Institute of Technology for 2026-27. One more row gives **V011** (probably the same person under a different APAAR, score 0.94). And one row gives **V032** (a transfer request is already open, so it is a warning and not a duplicate).
3. The genuine mover: go to **Transfers** (`/institution/transfers`) → **New request** (APAAR + source institution).
4. Sign in as **inst.admin** → Transfers → Incoming → **Approve**. The source record becomes `TRANSFERRED_OUT`.
5. Back as **inst2.admin** → **Re-validate**. The V010 for that student is gone, so the system no longer reports a false duplicate. Commit.
6. Also try the lifecycle: Students → pick a student → **Change status**. The dialog offers only allowed transitions (ACTIVE → WITHDRAWN/DEFERRED/TRANSFERRED_OUT/COMPLETED). GRADUATED → ACTIVE is impossible (V021).

---

## 4. AICTE console: real-time monitoring and analytics (PS req 4, 9, innovation)

1. Sign in as **aicte.analyst** in a second browser window and open http://localhost:5173/aicte.
2. **KPI cards**: institutions, **coverage %** (student-level vs aggregate-only), students, average fill %, excess seats, average DQ score.
3. **Live ticker**: as the institution commits in the other window, `batch.committed` appears in about 1 second.
4. **India map** (official boundaries; tile-grid fallback): colour by fill % / excess / DQ / coverage. Click a state to drill down to institutions.
5. **Leaderboards**: top excess enrolment (Demo Institute of Technology +3 in B.Tech CSE), lowest DQ, most cross-duplicates.
6. **Quota breakdown**: supernumerary by scheme (TFW/PMSSS/JK/NE/FN-OCI-NRI), NRI/OCI/FN share by state.
7. Upload **`batch_4_anomaly_drift.csv`** as inst.admin → in the **Anomaly & drift feed**: *NRI share 0.40 vs baseline 0.05 (z = 6.1)*, *column `category` removed* (V028), *new seat_type value "MGMT"* (V029). Each entry links to the batch.
8. **Reconciliation**: declared totals from the approval process vs uploaded counts; mismatches flagged (V022). Aggregate-only institutions show their submitted totals.
9. **Cross-institution duplicate queue**: resolve the V011 case side by side (Same person → raise to both institutions).
10. **Audit badge** (header): "Audit chain intact ✓" from `GET /v1/audit/verify-chain`.
11. **Reports** (`/reports`): POLICY report, year 2026-27, state = Maharashtra → PDF. ACCREDITATION report for one institution → XLSX.
12. As **aicte.admin**: master data browser, **Rollover** wizard 2026-27 → 2027-28 (dry run shows counts first), trust list of issuer DIDs, full audit log.

---

## 5. Aggregate-only institution (statistical totals gap)

1. An institution flagged `AGGREGATE_ONLY` signs in → **Aggregates** form: per program total, supernumerary, NRI, OCI, FN.
2. AICTE sees it in coverage % and reconciliation. When that institution later uploads student-level data, V022 compares the two.

---

## 6. Student: consent and selective sharing (PS req 5, 6, 8)

1. Sign in as **student** → http://localhost:5173/student. See your own record (unmasked for you only) and its version history.
2. **Consent**: REPOSITORY ✓, VERIFICATION_SHARE ✓, ANALYTICS_AGGREGATE ✓, each with a plain-language explanation.
3. First visit creates a **device key** (WebCrypto, non-exportable). Banner: "This device holds your key".
4. Sign in as **inst.admin** → student → **Issue enrolment credential**. (As **dab.admin** you can issue the **degree credential** for graduates of affiliated institutions.)
5. Back as **student** → **Credentials** → **Share selected fields**: tick only **Full name**, **Program**, **Enrolment status**; audience "Acme Corp HR" → QR + link (valid 5 min).
6. **Certificate**: download PDF → it shows the **APAAR ID + institution student ID + verification QR** (PS req 10).

---

## 7. Employer / regulator: verify (PS req 5)

1. Open http://localhost:5173/verify (signed in as **verifier**, or public with rate limit). **Scan** the QR or **paste** the link.
2. Result: **VALID ✓**: issuer *Demo Institute of Technology* (trusted by AICTE), issued and checked timestamps, and **only the 3 disclosed fields**. No DOB, category or full APAAR is shown.
3. Tamper test: change one character of the presentation → **INVALID ✗**, reason "disclosure digest mismatch".
4. **Correction → superseded:** inst.admin corrects the student's program (`PUT /v1/students/{apaar}`) → verify the old QR again → **SUPERSEDED**: "a newer version exists".
5. **Consent withdrawn → suspended:** student withdraws VERIFICATION_SHARE → verify → **SUSPENDED**: "holder has withdrawn consent". No data is revealed. Re-grant → VALID again.
6. Every verification appears in the audit log, with the APAAR masked.

---

## 8. System integration (PS req 7)

1. inst.admin → **Settings → API keys** → create key `evk_…` (shown once).
2. From the institution ERP:
   ```bash
   curl -X POST http://localhost:8000/v1/batches -H "X-API-Key: evk_xxx" -H "Idempotency-Key: 7b1c…" -F academic_year=2026-27 -F file=@data/demo/batch_1_clean.csv
   ```
   The same call again with the same Idempotency-Key returns the same batch and does not create a duplicate.
3. **Settings → Webhooks**: register `https://erp.example/hooks` for `batch.validated`, `batch.committed` and `credential.revoked` → **Send test** → delivery log shows 200, signature header `X-EduVerify-Signature`.
4. AICTE bulk export: `GET /v1/exports/students?year=2026-27&format=csv` (masked by default).
5. Full API reference: http://localhost:8000/docs (generated from `contracts/openapi.yaml`, contract-tested with schemathesis).

---

## 9. Security spot-checks (PS req 8)

| Check | How | Expected |
|---|---|---|
| RBAC | As inst.staff call `GET /v1/dashboards/aicte/summary` | 403 |
| Tenant isolation | inst2.admin opens inst.admin's batch URL | 403/404 |
| Lockout | 5 wrong passwords | Locked 15 min, generic message |
| Token storage | DevTools → Application → localStorage | No tokens |
| PII masking | aicte.analyst opens a student | `1234****9012`, email masked |
| Audit tamper | Edit one audit row in DB → `GET /v1/audit/verify-chain` | `valid:false`, first broken id |
| Logs | grep backend logs for a raw 12-digit APAAR | none |

---

## 10. What each part does (map for judges)

| Part | Owner | Role in pipeline |
|---|---|---|
| Upload wizard + column mapping | A + C | Institution → Upload |
| Mock APAAR registry + V002/V003/V004/V023 | B + C | APAAR Validation |
| Rule engine, dedup, drift, anomaly, reconciliation | C | Data Verification |
| Review workspace (human-in-the-loop) + before/after report | A + B + C | Data Verification |
| Commit, versions, lifecycle, transfers | B | AICTE Central Repository |
| AICTE console, institution dashboard, reports, SSE | A + B | Analytics & Monitoring |
| SD-JWT credentials, consent, verifier portal, certificates | B + A | Authorized Verification |
| Auth, RBAC, audit chain, encryption | B | Cross-cutting security |

---

## 11. Demo timing (5 minutes)

| Time | Scene |
|---|---|
| 0:00–0:30 | Problem: totals only, no student-level truth → our pipeline slide |
| 0:30–1:30 | §1 Upload `batch_2` with odd headers → mapping → live validation |
| 1:30–2:30 | §2 Explainable issue, approve fix, duplicate side-by-side, before/after 71 → 96, commit |
| 2:30–3:15 | §3 + §4 Cross-institution duplicate → transfer clears it; AICTE ticker, map, anomaly feed |
| 3:15–4:15 | §6 + §7 Student shares 3 fields → verifier VALID → correction → SUPERSEDED |
| 4:15–5:00 | Audit chain intact, security, metrics from `data/eval/RESULTS.md`, roadmap (ZK predicates, Merkle anchoring, real APAAR API) |
