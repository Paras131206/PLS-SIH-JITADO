# Team A — Frontend · Antigravity prompts

> Owns ONLY: `frontend/`, `docs/`, `demo/`, `reports/templates/`, `.github/workflows/frontend.yml`.
> Paste **A-MASTER** once, then A0 … A7 in order. Each prompt ends with a localhost link.
> Research/doc reading → fast model (Haiku-class). Coding/review → strong model (Sonnet-class).

---

## A-MASTER (paste first, once)

```
You are the Team A (Frontend) agent for EduVerify. Read agents.md, then steps.md, then this file. They are binding.
You write ONLY to: frontend/, docs/, demo/, reports/templates/, .github/workflows/frontend.yml.
Never edit backend/, engine/, data/, contracts/ (read them; request changes via a contract-change PR).
Product: the UI for every stakeholder — Institution portal, AICTE console, Student wallet, Verifier portal, Reports — plus certificate template, literature review and demo kit.
Stack: React 18, Vite, TypeScript (strict), Tailwind CSS, shadcn/ui, TanStack Query, React Router 6, Recharts, react-dropzone, react-i18next (en + hi), openapi-typescript (types generated from contracts/openapi.yaml into src/api/schema.gen.ts via `npm run gen:api`), openapi-fetch, MSW (mocks from the contract until the backend tag lands), @sd-jwt/core + @sd-jwt/sd-jwt-vc + WebCrypto (student wallet), qrcode.react, html5-qrcode (scanner), Vitest + Testing Library, Playwright, ESLint + Prettier.
Structure: src/app (providers, routes.tsx — append one sorted line per feature), src/features/<feature>/ (pages, components, hooks, tests), src/components/ui (shadcn), src/lib (api client, auth, sse, masking, i18n), src/mocks (MSW).
Rules:
- API base URL from import.meta.env.VITE_API_URL (default http://localhost:8000). Toggle mocks with VITE_USE_MOCKS=true.
- Never display raw APAAR/email/mobile unless the API returned them unmasked for this user; default render is masked.
- Every page has loading, empty, error and offline states, each with a Vitest test.
- WCAG AA: keyboard navigation, focus rings, aria labels, colour-contrast ≥ 4.5:1, no colour-only meaning (priority badges have icons + text).
- All user-facing strings through i18n (en, hi).
- Government-portal look: clean, white background, navy/saffron accents, Noto Sans + Noto Sans Devanagari, mobile-friendly.
Workflow per prompt: brainstorm (3 bullets) → plan checklist → implement → vitest + eslint → review your own diff. If /ce-brainstorm, /ce-plan, /ce-work, /caveman skills exist, use them in that order. Keep output terse.
At the end of every prompt: run tests, start `npm run dev` in frontend/ and print the localhost link plus a one-line "what to click".
```

---

## A0 — Scaffold, design system, mocks, i18n

```
Task A0. Scaffold the frontend.
1. Vite React TS app in frontend/ with Tailwind, shadcn/ui (button, card, table, badge, dialog, sheet, tabs, toast, dropdown, form, input, select, checkbox, switch, progress, skeleton, tooltip), React Router, TanStack Query, react-i18next (locales en.json, hi.json; language switcher), ESLint + Prettier, Vitest, Playwright.
2. `npm run gen:api` → openapi-typescript ../contracts/openapi.yaml -o src/api/schema.gen.ts; typed client src/lib/api.ts (openapi-fetch) with auth header + 401 → refresh → retry once.
3. MSW handlers in src/mocks for every endpoint group using example payloads (load data/demo shapes; generate a realistic BatchReport with all USP fields: reason, evidence, suggested_fix, priority, bucket, matched_fields, schema_drift, reconciliation).
4. App shell: top bar (logo, Government-style header, language switch, user menu), role-aware sidebar, breadcrumb, footer with accessibility statement. Pages as placeholders: /login, /institution/*, /aicte/*, /student/*, /verify, /reports, /settings/*.
5. Shared components: PriorityBadge (CRITICAL/HIGH/MEDIUM/LOW with icon), BucketBadge (AUTO_FLAG/HUMAN_REVIEW/INFO), MaskedValue, QualityScoreGauge, EmptyState, ErrorState, OfflineBanner (navigator.onLine).
6. vite.config: dev port 5173, strictPort. public/_redirects not needed (Render rewrite in render.yaml) but add a 404 → index fallback check in Playwright.
7. .github/workflows/frontend.yml (paths frontend/**, contracts/openapi.yaml): npm ci, gen:api, lint, typecheck, vitest, build, Playwright smoke.
Check: http://localhost:5173 → shell renders, language toggles to हिन्दी.
```

**What it does:** sets up a consistent, accessible, bilingual UI shell with types generated from the shared API contract and full mocks, so the team never waits for the backend.

---

## A1 — Login and role-based routing (uses B1 Auth)

```
Task A1. Auth UI. Works with MSW first; switch to the real API when tag api-v0.1 exists.
1. /login: email + password, show/hide password, error message without user enumeration, lockout message, optional TOTP step when API asks for MFA. Demo-user quick picker visible only when VITE_DEMO_MODE=true (fills email; password still typed or from .env.local — never committed).
2. src/lib/auth.tsx: AuthProvider holding access token in memory only (never localStorage), refresh via HttpOnly cookie endpoint on load and on 401, logout clears everything, idle timeout warning at 14 min.
3. Route guards: <RequireRole roles=[...]> per route; redirect each role to its home (AICTE → /aicte, institution → /institution, DAB → /dab, student → /student, verifier → /verify).
4. Settings for INSTITUTION_ADMIN: /settings/api-keys (create → show key once with copy button + warning, list, revoke), /settings/users (list, invite stub).
5. Tests: login success/failure, guard redirects per role, token not in localStorage, API-key shown once.
Check: http://localhost:5173/login → log in as institution admin → lands on /institution.
```

**What it does:** secure sign-in and per-role navigation, plus self-service API keys for institution system integration.

---

## A2 — Institution upload flow with smart column mapping (USP 6)

```
Task A2. Upload wizard at /institution/upload.
Step 1 Choose: academic year select (from master), "Download template" button (GET /v1/templates/student-upload.xlsx), dropzone for CSV/XLSX (react-dropzone, 10 MB), optional "replaces previous batch" picker (supersedes_batch_id). Send Idempotency-Key (uuid) with upload.
Step 2 Map columns: table Source column → Suggested field (select from canonical fields) with confidence bar and method chip (synonym/fuzzy/pattern/saved); sample values preview (masked APAAR); required fields still unmapped shown in red with V001 explanation; "Save as my institution's mapping profile" checkbox; Confirm.
Step 3 Validate: live progress via SSE (GET ticket → EventSource /v1/events?ticket=) with stage labels (Parsing, Mapping, Rules, Duplicates, Anomalies, Report); fallback to polling if SSE fails.
Step 4 Result summary: quality score gauge, rows valid/warning/error, counts by priority and bucket, intake cards (approved vs enrolled vs supernumerary vs excess per program, red when excess), reconciliation strip (declared vs uploaded), schema-drift banner if any, buttons "Review issues" and "Download report (XLSX/PDF)".
Batch list at /institution/batches with state chips (UPLOADED…COMMITTED/SUPERSEDED), open batch conflict (409) handled with a link to the open batch.
Tests: mapping UI with PRN/DOB/Dept headers, 409 handling, SSE fallback, empty/error/offline states.
Check: http://localhost:5173/institution/upload → upload data/demo/batch_2_errors.xlsx (mock or real) → confirm mapping → see summary.
```

**What it does:** lets institutions upload spreadsheets in any column naming, confirm the mapping, and watch validation happen live.

---

## A3 — Review workspace: explainable issues, duplicates, before/after report (USP 1, 2, 4, 5, 8)

```
Task A3. /institution/batches/:id/review.
1. Issue queue: default sort by priority (CRITICAL→LOW) then row; filters rule, field, severity, priority, bucket, status; tabs "Auto-flagged", "Needs human review", "Info". Virtualised table for 20k rows.
2. Issue card/drawer: field, rule ID + name, message, reason sentence, evidence table (the values used), suggested fix with rationale, actions Accept fix / Edit value / Dismiss with note (STAFF sees "Propose" only; ADMIN approves). Row deep link shows the full row (masked) with the offending cell highlighted.
3. Bulk actions: accept all INFO normalisations; dismiss selected with reason.
4. Duplicates tab: clusters with score, side-by-side compare (fields aligned, per-field similarity bars from matched_fields, differences highlighted), decisions Same person / Different people / Transfer.
5. Re-validate button → progress → Before/After panel: quality score before vs after, resolved vs pending, per-priority and per-rule deltas (Recharts bar), download DQ comparison XLSX/PDF.
6. Commit button: disabled with explanation while CRITICAL issues are open; confirm dialog listing excluded rows.
7. Tests: sorting, decision flow for staff vs admin, side-by-side compare renders matched fields, commit disabled state, empty/error/offline.
Check: http://localhost:5173/institution/batches/demo-2/review → accept a suggested fix → re-validate → see score improve.
```

**What it does:** the heart of the human-in-the-loop design — staff see exactly what is wrong and why, approve fixes, confirm duplicates, and see the measurable improvement.

---

## A4 — Lifecycle, transfers, aggregate mode, integrations settings

```
Task A4. Institution operations.
1. /institution/students: searchable list (masked), student detail with version history and lifecycle timeline; "Change status" dialog offering only allowed transitions (agents.md §8.1) with effective date, reason, evidence ref.
2. /institution/transfers: Incoming requests (approve/reject with note), Outgoing (create request: APAAR + source institution search), status chips, 15-day AICTE override note.
3. /institution/aggregates: form for AGGREGATE_ONLY institutions (per program: total, supernumerary, NRI, OCI, FN) + reconciliation view declared vs submitted.
4. /settings/webhooks: register URL, choose events, secret shown once, send test, delivery log with status codes and retry count; copyable signature-verification snippet.
5. /institution/dashboard: KPI cards (students, fill %, DQ score), DQ trend line, intake-vs-enrolment per program, open issues by priority, notifications list.
6. Tests incl. transition dialog only shows allowed options.
Check: http://localhost:5173/institution/transfers → create a transfer request.
```

**What it does:** handles real-world student movement (withdrawal, transfer, lateral entry), lets partially-onboarded institutions submit totals, and lets IT teams wire up webhooks.

---

## A5 — AICTE console (real-time monitoring)

```
Task A5. /aicte.
1. Overview: KPI cards (institutions, coverage % student-level vs aggregate-only, students, avg fill %, excess seats, avg DQ), SSE live ticker (batch committed, anomaly detected, cross-dupe found).
2. India map by state (metric selector: fill %, excess, DQ score, coverage) using official boundaries per agents.md §12 from frontend/public/geo/ keyed by LGD code; if file missing, render a state tile-grid fallback. Click state → district/institution drilldown table.
3. Leaderboards: excess enrolment, lowest DQ, most cross-institution duplicates.
4. Quota/seat breakdown: supernumerary by scheme, NRI/OCI/FN shares by state/program (Recharts stacked bars).
5. Cross-institution duplicate queue with side-by-side compare and resolve (reuse A3 component).
6. Anomaly & drift feed: each item with metric, value vs baseline, z/method, reason, link to batch.
7. Reconciliation view: declared vs uploaded per institution/program, mismatch filter.
8. Audit chain badge in header: calls /v1/audit/verify-chain, green "Audit chain intact" / red with first broken id. Audit log viewer (AICTE_ADMIN).
9. Admin: master data browser, rollover wizard (dry run → confirm), trust list view.
10. Tests: map fallback, SSE ticker, empty/error/offline.
Check: http://localhost:5173/aicte → map + live ticker; upload a batch in another tab and watch it appear.
```

**What it does:** gives AICTE the national, live picture — where intake is exceeded, where data quality is poor, where the same student appears twice — and proof the logs are untampered.

---

## A6 — Student wallet, verifier portal, certificate template (needs api-v1.0)

```
Task A6. Trust UIs.
1. /student: own record (unmasked for self), version history, consent toggles per purpose with plain-language explanation and consequences (withdrawing VERIFICATION_SHARE suspends credentials), consent history.
2. Holder key: on first visit generate ECDSA P-256 key with WebCrypto (extractable:false) stored in IndexedDB; register public JWK (POST /v1/credentials/holder-key). Show "This device holds your key; if you clear browser data you must request re-issue".
3. Credentials list (status VALID/SUPERSEDED/SUSPENDED/REVOKED). "Share selected fields" builder: checkboxes per disclosable claim, audience (verifier name/URL), fetch nonce, build presentation with @sd-jwt/core (only chosen disclosures + KB-JWT signed with WebCrypto key), show QR (qrcode.react) + copy link + expiry countdown.
4. /verify (public + VERIFIER): scan QR (html5-qrcode) or paste presentation/link → POST /v1/verify → big green VALID / red INVALID / amber SUPERSEDED / grey SUSPENDED card with only disclosed fields, issuer name, issued/checked timestamps, reasons list. Nothing else about the student is ever shown.
5. /dab (DAB_ADMIN): list graduates of affiliated institutions, issue degree credential.
6. reports/templates/certificate.html (+ CSS, A4, print-ready, WeasyPrint-compatible — no JS): institution/DAB name and logo slot, student name, program, APAAR ID, institution student ID, issue date, credential id, QR image placeholder {{qr_data_uri}}, signature line, Hindi + English labels. Also policy_report.html and dq_report.html templates with Jinja2 placeholders agreed with Team B.
7. Tests: share builder includes only selected claims (decode and assert), verifier screen states, key never extractable.
Check: http://localhost:5173/student → share name + program only → open the QR link in http://localhost:5173/verify → VALID with 2 fields.
```

**What it does:** students control what they reveal; employers and regulators verify instantly without seeing the full record; certificates carry APAAR + student ID + QR (PS requirement 10).

---

## A7 — Reports UI, docs, demo kit, E2E

```
Task A7. Finish.
1. /reports: builder (type POLICY/ACCREDITATION/MONITORING/REGULATORY; filters year, state, program, category; format PDF/XLSX) → job status → download; history of generated reports.
2. docs/literature_review.md: summary of each source in agents.md §13 (paraphrased, cite properly), comparison table (existing approaches: blockchain cert verification, centralised registries, ZKP systems, Deequ-style DQ tools, record-linkage tools) vs EduVerify on: student-level ingestion, validation depth, fuzzy dedup, explainability, human review, selective disclosure, consent, audit, cost; gaps we close.
3. docs/architecture.md with a Mermaid diagram of the pipeline and deploy topology; docs/user_guide.md per role (EN + HI headings).
4. demo/demo_script.md (5-minute script following runthrough.md), demo/pitch_outline.md (problem, PS mapping, USPs, live demo, metrics from data/eval/RESULTS.md, security, roadmap), demo/seed_scenario.md.
5. Playwright e2e (frontend/e2e/): login as institution → upload batch_2 → map → review → accept fix → re-validate → commit; login as student → share → verifier VALID; AICTE sees committed batch in ticker. Run against docker compose stack.
6. Lighthouse/axe pass: no critical a11y violations on main pages.
Check: http://localhost:5173/reports → generate a policy report PDF.
```

**What it does:** delivers the reports PS requirement 9 asks for, the written research and demo materials judges see, and an end-to-end test proving the whole flow works.
