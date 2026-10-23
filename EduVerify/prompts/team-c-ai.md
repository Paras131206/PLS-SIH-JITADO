# Team C — AI / Data Engine · Antigravity prompts

> Owns ONLY: `engine/`, `data/`, `contracts/rule_catalog.yaml`, `contracts/column_synonyms.yaml`, `.github/workflows/engine.yml`.
> Paste **C-MASTER** once when you open the workspace, then paste C0 … C7 in order. Each prompt ends with a localhost link to check your work.
> Research/doc reading → fast model (Haiku-class). Coding/review → strong model (Sonnet-class).

---

## C-MASTER (paste first, once)

```
You are the Team C (AI / Data) agent for EduVerify. Read agents.md, then steps.md, then this file. They are binding.
You write ONLY to: engine/, data/, contracts/rule_catalog.yaml, contracts/column_synonyms.yaml, .github/workflows/engine.yml.
Never edit backend/, frontend/, docs/, render.yaml, or other teams' workflows. Contract files outside your list change only via a PR labelled contract-change.
Product: pure Python package `eduverify_engine` (no DB, no HTTP in the library) that turns an uploaded CSV/XLSX + master data + intake + declared totals + registry + history into a BatchReport (agents.md §5.3), implementing rules V001–V035 (agents.md §6) with explainable issues (reason, evidence, suggested_fix, severity, priority, confidence, bucket).
Stack: Python 3.11, pandas, pandera, openpyxl, charset-normalizer, rapidfuzz, jellyfish (+ indic-soundex if it installs cleanly), scikit-learn, pydantic v2, pytest, ruff. Optional extra [splink] = splink 4.x + duckdb (never required).
Public API (freeze at engine-v0.1, change only with a contract-change PR):
  suggest_mapping(headers, synonyms, saved_profile=None) -> list[ColumnMapping]
  validate_batch(file_or_df, *, mapping, master, intake, declared_totals, registry, central_snapshot, history, previous_batch_profile, transfers) -> BatchReport
  compare_reports(before: BatchReport, after: BatchReport, decisions) -> DQComparison
  export_report(report, fmt: "json"|"xlsx") -> bytes
`registry` is a Protocol (lookup(apaar)->RegistryEntry|None); Team B passes its own implementation.
Rules: one function per rule, registered by ID from rule_catalog.yaml; vectorised pandas; never crash on a bad row; never log raw APAAR (use mask_apaar).
Every BatchReport carries engine_version and rule_catalog_version.
Workflow per prompt: brainstorm (3 bullets) → plan checklist → implement → pytest + ruff → review your own diff. If /ce-brainstorm, /ce-plan, /ce-work, /caveman skills exist, use them in that order. Keep output terse.
At the end of every prompt: run tests, start the dev harness (`uvicorn devserver:app --app-dir engine --port 8100`), and print the localhost link plus a one-line "what to click".
```

---

## C0 — Scaffold the engine package and contracts

```
Task C0. Scaffold Team C.
1. engine/pyproject.toml (package eduverify_engine, version 0.0.1, python>=3.11, extras: [splink], [dev]). engine/eduverify_engine/__init__.py exposes __version__.
2. engine/eduverify_engine/models.py: Pydantic v2 models exactly per agents.md §5.3: ColumnMapping, Issue (issue_id, row, record_key, field, rule_id, severity, priority, confidence, bucket, message, reason, evidence, suggested_fix{value,rationale,requires_approval}, value_masked), DuplicateCluster, SchemaDrift, Anomaly, IntakeSummary, ReconciliationRow, BatchReport, DQComparison. Export JSON Schema to engine/schema_out/batch_report.json (Team B copies it into contracts/schemas/).
3. engine/eduverify_engine/masking.py: mask_apaar, mask_email, mask_mobile + tests.
4. contracts/rule_catalog.yaml: catalog_version: 0.1.0, owner: team-c, all rules V001–V035 with id, name, severity, default_priority, bucket_policy, since_version, description, fix_hint (from agents.md §6). Loader + validation test.
5. contracts/column_synonyms.yaml: for every canonical field list synonyms (e.g. institution_student_id: [PRN, Student_ID, Enrollment_No, Enrolment No, Roll No, Reg No]; dob: [DOB, Date_of_Birth, Birth Date]; department: [Dept, Department_Name]; apaar_id: [APAAR, APAAR ID, ABC ID]...). Include Hindi headers where obvious.
6. engine/devserver.py: tiny FastAPI app (dev only, not deployed) on port 8100 with GET /healthz, GET /catalog, POST /validate (multipart file) returning BatchReport JSON using in-repo demo master data. Add it to .gitignore? No — commit it, but it must not be imported by the package.
7. .github/workflows/engine.yml: on paths engine/** data/** contracts/rule_catalog.yaml contracts/column_synonyms.yaml → ruff, pytest, bandit -r engine.
8. engine/README.md: install (`pip install -e engine[dev]`), run tests, run harness.
Done when: pytest green, ruff clean, harness up.
Check: http://localhost:8100/docs  → GET /catalog lists 35 rules.
```

**What it does:** creates the package skeleton, the frozen data models, the rule catalog and synonym dictionary (contracts Team A/B read), and a local dev harness so Team C can test without the backend.

---

## C1 — Master data + synthetic data generator (Team B and A depend on this)

```
Task C1. Master data and synthetic data.
1. data/master/: states.csv + districts.csv (LGD codes; real state names and codes, a subset of districts is fine), degree_awarding_bodies.csv (6 synthetic universities incl. 1 autonomous), institutions.csv (40 synthetic, AICTE-style IDs like 1-1234567890, state, district, type, affiliated_dab_id, onboarding_level with 6 AGGREGATE_ONLY), programs.csv (≈25 program codes across DIPLOMA/UG/PG/PGDM/PHD with department, duration_years, lateral_allowed), academic_years.csv (2024-25, 2025-26, 2026-27 current, windows), enums.csv (from contracts/schemas/enums.json if present, else from models; label_en + label_hi).
2. data/generator/generate.py (deterministic, --seed 42, --students 20000): produce into data/synthetic/ (gitignored):
   registry.csv (mock APAAR registry: apaar_id, full_name, dob, gender), intake.csv (program_intake incl. supernumerary_allowed JSON), declared_totals.csv (with some deliberate mismatches), central_snapshot.csv (already-committed records at other institutions, for cross-institution dedup), history_metrics.csv (6 past batches/institution), transfers.csv (some approved, some open).
   Indian names: generate from curated first/last name lists across regions; produce transliteration variants (Mohammad/Mohammed/Md., Lakshmi/Laxmi, initials "R. S. Sharma"), honorifics, case/whitespace noise.
3. Seeded defects with ground_truth.csv (row, file, rule_id, field): bad/missing APAAR, Excel-mangled APAAR (scientific notation, dropped leading zero), nulls, bad dates incl. ambiguous 03/04/2026 and MM/DD style, intra-batch dup APAAR, fuzzy dup different APAAR, cross-institution active dup, approved-transfer case (must NOT be flagged V010), open-transfer case (V032), over-intake, supernumerary over limit, OCI with IN, NRI flag mismatch, missing consent, minor without guardian consent, graduation-year mismatch, conflicting department, lateral with year 1, program not approved, renamed/missing columns.
4. data/demo/ (committed, small): batch_1_clean.csv, batch_2_errors.xlsx (with non-standard headers PRN/DOB/Dept to exercise column mapping), batch_3_cross_dupes.csv, batch_4_anomaly_drift.csv (NRI spike + a removed column + new category), plus demo_registry.csv, demo_intake.csv, demo_declared_totals.csv, demo_central_snapshot.csv, demo_transfers.csv, demo_history.csv — all for ONE demo institution + 3 neighbours. Document in data/demo/README.md which defects each batch contains.
5. data/adapters/: universityintake.py and synedu.py mapping public dataset columns to our schema for fixtures (download instructions in README; don't commit the raw datasets).
6. Tests: generator is deterministic (same seed → same hash), ground truth row counts match.
Tag request: when merged, ask the lead to tag data-v0.1 (Team B seeds from it).
Check: http://localhost:8100/docs → POST /validate with data/demo/batch_1_clean.csv returns rows_error = 0.
```

**What it does:** gives every team the same realistic test world — master tables, registry, intake, declared totals, central snapshot, history, transfers — and 4 demo batches that tell the demo story.

---

## C2 — Parser + smart column mapping (USP 6) + date/ID policy

```
Task C2. Parser and smart column mapping.
1. eduverify_engine/parse.py: read CSV/XLSX → DataFrame of strings ONLY (dtype=str, keep_default_na=False; openpyxl read with data_only=True, record original cell type per column). Encoding detection with charset-normalizer, BOM strip, trim, header normalisation (lower, strip, collapse spaces/underscores). Row-level error capture: unreadable rows become V006 issues, never exceptions. Size guard 10 MB / 100k rows.
2. eduverify_engine/mapping.py: suggest_mapping(headers, synonyms, saved_profile): exact synonym → normalised synonym → rapidfuzz token_set_ratio + Jaro-Winkler ≥ 85 → value-pattern sniffing (12-digit column ⇒ apaar_id, date-like ⇒ dob/admission_date). Return confidence + method per column, unmapped columns, and missing required fields (→ V001 if still missing after user confirmation). Saved profiles: a dict the backend persists per institution and passes back.
3. eduverify_engine/normalize.py: date policy from agents.md §8.9 (ISO, DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY, Excel serial when cell was date-typed; never MM/DD; ambiguous → V024 with candidates in evidence). APAAR: strip spaces/hyphens; detect scientific notation, ".0" suffix, 11-digit numeric → V023 with suggested_fix (left-pad only if registry confirms the padded value). Name normalisation → name_norm (strip honorifics Mr/Ms/Dr/Shri/Smt/Kumari, punctuation, collapse initials, lowercase, common transliteration map). Booleans Y/N/Yes/No/1/0/True/False/हाँ/नहीं.
4. Devserver: POST /map (headers) and POST /parse (file) endpoints.
5. Minimal validate_batch(): wire parse → mapping → normalize → V001, V002, V005, V023, V024 → BatchReport with a provisional quality_score. Full signature from C-MASTER, unused arguments accepted and ignored for now. This lets Team B build the upload pipeline while you write C3.
6. Tests: batch_2_errors.xlsx maps PRN→institution_student_id, DOB→dob, Dept→department with confidence ≥ 0.9; a CSV with APAAR "012345678901" keeps the leading zero; "03/04/2026" parses as 3 April 2026; "2026-13-01" → V024.
Tag request: ask the lead to tag engine-v0.1 (API signatures frozen; rules grow behind them).
Check: http://localhost:8100/docs → POST /map with ["PRN","DOB","Dept","APAAR No"] shows the suggested mapping.
```

**What it does:** turns messy spreadsheets from different departments into the canonical schema safely (no lost leading zeros, no US-date confusion) and proposes a column mapping the user confirms.

---

## C3 — Explainable rule engine (USP 1, 3, 4, 8)

```
Task C3. Rule engine.
1. eduverify_engine/rules/registry.py: @rule("V0xx") decorator; loads metadata from rule_catalog.yaml; each rule fn(df, ctx) -> list[Issue]. ctx holds master, intake, declared_totals, registry, central_snapshot, history, transfers, academic_year config.
2. Implement row/field rules: V001, V002, V003, V004 (rapidfuzz name + exact dob vs registry), V005, V006, V014, V015, V016, V017, V018, V019, V021 (for status values in upload vs previous committed status), V023, V024, V025 (admission year + duration − lateral), V026 (same student_id with different program/department/level across rows), V027, V031, V033, V035.
3. Aggregate rules: V012 (regular-seat count per program vs approved_intake), V013 (supernumerary per scheme vs allowed).
4. Every Issue: plain-English message, reason with the actual numbers, evidence dict with the fields used, suggested_fix only when deterministic (e.g. V025 expected year, V031 normalised text, V023 padded APAAR), value_masked. Priority from catalog, escalated by context (e.g. V005 on identity field → HIGH). Bucket: deterministic → AUTO_FLAG (confidence 1.0), heuristic → HUMAN_REVIEW, cosmetic → INFO.
5. eduverify_engine/score.py: quality_score per agents.md §5.3; metrics: completeness, validity, uniqueness per column (Deequ-style).
6. validate_batch() wires parse → mapping → normalize → rules → score, sorted issues by priority then row.
7. Tests per rule with tiny fixtures in data/fixtures/; one test asserting reason/evidence present on every issue. Precision/recall vs ground_truth.csv for rule-based defects; print a table; fail if recall < 0.95 for deterministic rules.
Check: http://localhost:8100/docs → POST /validate with data/demo/batch_2_errors.xlsx → issues sorted CRITICAL first, each with reason + evidence.
```

**What it does:** the core validator — every finding says which field, why, with what evidence, how serious, how confident, and (if safe) what the fix would be.

---

## C4 — Intelligent duplicate detection (USP 2) + lifecycle-aware cross-institution checks

```
Task C4. Dedup.
1. eduverify_engine/dedup.py:
   a. Exact: V007 dup apaar in batch, V008 dup institution_student_id within institution+year.
   b. Blocking (Christen 2012): blocks by dob + gender, and by phonetic key of last name (jellyfish metaphone / indic-soundex) + birth year. Cap block size.
   c. Compare: name_norm Jaro-Winkler, token_set_ratio (handles "Rahul S. Sharma" vs "Rahul Sharma"), initials match, dob exact / day-month swap, gender, mobile/email hash equality (if present). Weighted score (Fellegi-Sunter-style weights in config). matched_fields dict with per-field similarity.
   d. Thresholds: ≥ 0.92 AUTO_FLAG, 0.75–0.92 HUMAN_REVIEW, < 0.75 ignore. V009 intra-batch (different APAAR).
   e. Cross-institution against central_snapshot: V010 same APAAR ACTIVE elsewhere same year — EXCLUDE when transfers has APPROVED for that APAAR; open transfer → V032 instead; source status TRANSFERRED_OUT/WITHDRAWN/COMPLETED/GRADUATED → no flag. V011 fuzzy different APAAR elsewhere.
   f. Cluster with union-find → DuplicateCluster(scope, members with masked APAAR, score, matched_fields, bucket).
2. Optional splink path (extra installed): same interface, used when rows > 50k; default rapidfuzz path must handle 50k rows < 60 s on a laptop.
3. Tests: Mohammed/Mohd./Md. variants found; Lakshmi/Laxmi found; twins (same dob, different first names) NOT auto-flagged; approved transfer not flagged; open transfer → V032. Print precision/recall for dedup vs ground truth (target precision ≥ 0.9 on AUTO_FLAG).
Check: http://localhost:8100/docs → POST /validate with data/demo/batch_3_cross_dupes.csv → duplicate_clusters show matched_fields and scores.
```

**What it does:** finds the same student even when spelling differs, explains the match field by field, and stops genuine transfers from being reported as duplicates.

---

## C5 — Anomaly detection, schema drift (USP 7), reconciliation

```
Task C5. Monitoring intelligence.
1. eduverify_engine/profile.py: batch profile = columns, inferred types, null rates, category sets, row count, key metrics (fill ratio per program, supernumerary share, NRI/OCI/FN share, duplicate rate, missing-ID rate). Serialisable dict; backend stores it as metric_history.
2. eduverify_engine/drift.py: compare with previous_batch_profile → V028 (required column removed / type changed), V029 (new category values), V030 (missing-ID or null-rate jump > 3× or +10 pts). Output SchemaDrift entries.
3. eduverify_engine/anomaly.py: (a) Deequ-style per-institution history: z-score and rate-of-change per metric (min 3 history points, else skip with INFO); (b) IsolationForest (scikit-learn, fixed random_state) on institution-level feature vectors across all institutions in history → anomaly score; V020 issues with method + baseline + reason sentence.
4. eduverify_engine/reconcile.py: compare per-program counts (total, supernumerary, NRI, OCI, FN) with declared_totals → ReconciliationRow + V022 if beyond tolerance (configurable, default ±2 % or ±2). Also a function reconcile_aggregate(declared, aggregate_submission) for AGGREGATE_ONLY institutions.
5. Rollover helper: rollover_preview(previous_year_records, programs) → provisional next-year rows; V034 for previous ACTIVE students missing in the new batch.
6. Tests with data/demo/batch_4_anomaly_drift.csv: drift detects removed column + new category; anomaly flags NRI share spike with z > 3.
Tag request: ask the lead to tag engine-v0.5 (Team B wires rollover in B7).
Check: http://localhost:8100/docs → POST /validate with batch_4_anomaly_drift.csv → schema_drift + anomalies populated.
```

**What it does:** catches problems that no single row shows — sudden spikes, disappearing columns, totals that don't match what the institution declared to AICTE.

---

## C6 — Before/after data-quality report (USP 5) + exports

```
Task C6. DQ reports.
1. eduverify_engine/report.py: compare_reports(before, after, decisions) → DQComparison: rows scanned, errors found, duplicates found, resolved (accepted fix / dismissed / merged), pending, quality_score_before/after, per-rule and per-priority deltas, per-column completeness before/after.
2. export_report(report|comparison, "json"|"xlsx"): XLSX via openpyxl with sheets Summary, Issues (sorted by priority, with reason/evidence/suggested fix/decision), Duplicates, Intake, Reconciliation, Drift & Anomalies, Column mapping. Conditional formatting by priority. Masked APAAR only.
3. JSON is stable for the backend PDF renderer (WeasyPrint is Team B's job).
4. Devserver: POST /report/compare (two reports + decisions) and GET /report/demo.xlsx.
5. Final metrics script data/eval/evaluate.py: runs all 4 demo batches + 20k synthetic, prints precision/recall/F1 per rule family and runtime; writes data/eval/RESULTS.md (Team A uses it in the pitch).
6. Bump engine to 1.0.0, catalog to 1.0.0. Ask the lead to tag engine-v1.0.
Check: http://localhost:8100/report/demo.xlsx downloads; http://localhost:8100/docs → POST /report/compare.
```

**What it does:** proves value with numbers — quality score before vs after review, what was fixed, what is pending — as a downloadable report.

---

## C7 — Hardening, performance and handoff

```
Task C7. Hardening.
1. Profile validate_batch on 50k rows (neuralsorcerer sample mapped via adapter + synthetic). Target < 60 s, < 400 MB RSS (Render free has 512 MB). Optimise with vectorisation and block caps; document numbers in engine/README.md.
2. Property-based tests (hypothesis) for parser and masking: never raises, never emits raw 12-digit APAAR in messages.
3. Fuzz test with random garbage CSV/XLSX: validate_batch always returns a BatchReport.
4. engine/README.md: public API, rule list, thresholds, how to add a rule (catalog entry + @rule fn + fixture + test), versioning policy.
5. Verify `pip install ./engine` (without [splink]) works from repo root on a clean Python 3.11 venv — this is exactly what Render runs.
Check: http://localhost:8100/healthz returns engine_version 1.0.x and catalog_version 1.0.x.
```

**What it does:** makes the engine fast, memory-safe for Render, crash-proof, and documented so others can extend it.
