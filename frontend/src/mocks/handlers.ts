import { http, HttpResponse } from 'msw';
import {
  AuthResponse,
  UserProfile,
  BatchReport,
  BatchListItem,
  Issue,
  ProgramIntake,
  DuplicateCluster,
  AnomalyItem,
  StudentRecord,
  VerificationResult,
  AuditLogEntry,
  AuditChainStatus,
  ConsentRecord,
} from '../api/types';

// Mock users across all 6 roles
export const mockUsers: Record<string, UserProfile> = {
  'institution_admin@aicte.gov.in': {
    id: 'usr-inst-admin-01',
    email: 'institution_admin@aicte.gov.in',
    full_name: 'Dr. Ramesh Sharma',
    role: 'INSTITUTION_ADMIN',
    institution_aicte_id: '1-10293847',
    institution_name: 'Delhi Technological University',
  },
  'institution_staff@aicte.gov.in': {
    id: 'usr-inst-staff-01',
    email: 'institution_staff@aicte.gov.in',
    full_name: 'Priya Verma',
    role: 'INSTITUTION_STAFF',
    institution_aicte_id: '1-10293847',
    institution_name: 'Delhi Technological University',
  },
  'aicte_admin@aicte.gov.in': {
    id: 'usr-aicte-admin-01',
    email: 'aicte_admin@aicte.gov.in',
    full_name: 'Prof. Anil Sahasrabudhe',
    role: 'AICTE_ADMIN',
  },
  'aicte_analyst@aicte.gov.in': {
    id: 'usr-aicte-analyst-01',
    email: 'aicte_analyst@aicte.gov.in',
    full_name: 'Sunita Mehra',
    role: 'AICTE_ANALYST',
  },
  'verifier@infosys.com': {
    id: 'usr-verifier-01',
    email: 'verifier@infosys.com',
    full_name: 'Rajiv Menon (Corporate HR)',
    role: 'VERIFIER',
  },
  'student@dtu.ac.in': {
    id: 'usr-student-01',
    email: 'student@dtu.ac.in',
    full_name: 'Aarav Rajesh Kumar',
    role: 'STUDENT',
    apaar_id: '1234****9012',
    institution_aicte_id: '1-10293847',
    institution_name: 'Delhi Technological University',
  },
};

// Current authenticated user (default to INSTITUTION_ADMIN)
let currentUser: UserProfile = mockUsers['institution_admin@aicte.gov.in'];

export const mockIntake: ProgramIntake[] = [
  {
    institution_aicte_id: '1-10293847',
    program_code: 'CSE-UG-01',
    program_name: 'B.Tech Computer Science & Engineering',
    academic_year: '2026-27',
    approved_intake: 120,
    regular_enrolled: 124,
    supernumerary_enrolled: 14,
    supernumerary_allowed: { TFW: 6, PMSSS: 4, JK: 2, FN_OCI_NRI: 5 },
    approval_letter_ref: 'AICTE/NWRO/2026-27/1-10293847/EOA',
  },
  {
    institution_aicte_id: '1-10293847',
    program_code: 'ECE-UG-02',
    program_name: 'B.Tech Electronics & Communication Engineering',
    academic_year: '2026-27',
    approved_intake: 90,
    regular_enrolled: 88,
    supernumerary_enrolled: 8,
    supernumerary_allowed: { TFW: 4, PMSSS: 3, JK: 2, FN_OCI_NRI: 4 },
    approval_letter_ref: 'AICTE/NWRO/2026-27/1-10293847/EOA',
  },
  {
    institution_aicte_id: '1-10293847',
    program_code: 'AI-DS-UG-03',
    program_name: 'B.Tech Artificial Intelligence & Data Science',
    academic_year: '2026-27',
    approved_intake: 60,
    regular_enrolled: 60,
    supernumerary_enrolled: 5,
    supernumerary_allowed: { TFW: 3, PMSSS: 2, JK: 1, FN_OCI_NRI: 3 },
    approval_letter_ref: 'AICTE/NWRO/2026-27/1-10293847/EOA',
  },
];

export const mockIssues: Issue[] = [
  {
    row: 14,
    field: 'apaar_id',
    rule_id: 'V002',
    severity: 'ERROR',
    message: 'APAAR ID must be exactly 12 numeric digits; found alphanumeric token.',
    value_masked: '1234****901X',
  },
  {
    row: 27,
    field: 'apaar_id',
    rule_id: 'V007',
    severity: 'ERROR',
    message: 'Duplicate APAAR ID encountered within the same upload batch at rows 12 and 27.',
    value_masked: '2345****8901',
  },
  {
    row: 42,
    field: 'program_code',
    rule_id: 'V012',
    severity: 'ERROR',
    message: 'Regular-seat enrolment exceeds approved intake (enrolled 124 > approved 120) for CSE-UG-01.',
    value_masked: 'CSE-UG-01',
  },
  {
    row: 58,
    field: 'quota',
    rule_id: 'V014',
    severity: 'ERROR',
    message: 'Inconsistency: OCI status flagged true but student nationality is recorded as IN (India).',
    value_masked: 'IN / OCI:true',
  },
  {
    row: 83,
    field: 'guardian_consent',
    rule_id: 'V018',
    severity: 'ERROR',
    message: 'Minor student (age 17) lacks verified guardian consent record.',
    value_masked: 'DOB: 2009-04-12',
  },
  {
    row: 91,
    field: 'full_name',
    rule_id: 'V004',
    severity: 'WARN',
    message: 'Uploaded name "Karthik S. Raman" deviates from APAAR registry record "Karthik Subramanian Raman" (fuzzy score 0.88).',
    value_masked: 'Ka****an',
  },
  {
    row: 104,
    field: 'admission_date',
    rule_id: 'V017',
    severity: 'ERROR',
    message: 'Admission date (2026-11-20) falls outside prescribed AICTE academic-year window.',
    value_masked: '2026-11-20',
  },
  {
    row: 118,
    field: 'apaar_id',
    rule_id: 'V010',
    severity: 'ERROR',
    message: 'Cross-Institution Conflict: Student APAAR active at College of Engineering Pune (1-92837465).',
    value_masked: '9876****2109',
  },
];

export const mockBatchReport: BatchReport = {
  batch_id: 'batch-2026-dtu-001',
  institution_aicte_id: '1-10293847',
  institution_name: 'Delhi Technological University',
  academic_year: '2026-27',
  created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
  status: 'COMPLETED',
  rows_total: 285,
  rows_valid: 268,
  rows_warning: 9,
  rows_error: 8,
  quality_score: 94.04,
  metrics: {
    completeness: {
      apaar_id: 1.0,
      full_name: 1.0,
      dob: 0.99,
      gender: 1.0,
      program_code: 1.0,
      category: 0.98,
      consent_status: 0.97,
    },
    uniqueness: {
      apaar_id: 0.99,
      institution_student_id: 1.0,
    },
  },
  issues: mockIssues,
  intake_summary: [
    { program_code: 'CSE-UG-01', approved: 120, enrolled: 124, supernumerary: 14, excess: 4 },
    { program_code: 'ECE-UG-02', approved: 90, enrolled: 88, supernumerary: 8, excess: 0 },
    { program_code: 'AI-DS-UG-03', approved: 60, enrolled: 60, supernumerary: 5, excess: 0 },
  ],
  duplicate_clusters: [
    {
      cluster_id: 'dup-cl-01',
      apaar_ids: ['9876****2109'],
      score: 0.98,
      scope: 'CROSS_INSTITUTION',
      institution_aicte_ids: ['1-10293847', '1-92837465'],
      status: 'PENDING',
      match_reasons: ['Exact APAAR 12-digit collision', 'DOB Match', 'Name Normalization Match'],
    },
    {
      cluster_id: 'dup-cl-02',
      apaar_ids: ['3456****7890', '7654****0987'],
      score: 0.89,
      scope: 'INTRA',
      institution_aicte_ids: ['1-10293847'],
      status: 'PENDING',
      match_reasons: ['Phonetic name match (Indic Soundex)', 'DOB match', 'Different APAAR entered'],
    },
  ],
  anomalies: [
    {
      id: 'anom-01',
      institution_aicte_id: '1-10293847',
      institution_name: 'Delhi Technological University',
      metric: 'nri_share',
      value: 0.14,
      baseline: 0.03,
      z: 4.8,
      reason: 'NRI quota proportion surged 366% compared to 3-year historical average.',
      timestamp: new Date().toISOString(),
      status: 'NEW',
    },
  ],
};

export const mockBatchList: BatchListItem[] = [
  {
    batch_id: 'batch-2026-dtu-001',
    institution_aicte_id: '1-10293847',
    institution_name: 'Delhi Technological University',
    filename: 'DTU_Admissions_2026_UG_Final.csv',
    academic_year: '2026-27',
    uploaded_at: '2026-10-23T14:30:00Z',
    status: 'COMPLETED',
    rows_total: 285,
    rows_valid: 268,
    rows_error: 8,
    quality_score: 94.04,
  },
  {
    batch_id: 'batch-2026-coep-002',
    institution_aicte_id: '1-92837465',
    institution_name: 'College of Engineering Pune',
    filename: 'COEP_Batch_BTech_2026.xlsx',
    academic_year: '2026-27',
    uploaded_at: '2026-10-22T11:15:00Z',
    status: 'COMPLETED',
    rows_total: 420,
    rows_valid: 418,
    rows_error: 2,
    quality_score: 99.52,
  },
  {
    batch_id: 'batch-2026-nitk-003',
    institution_aicte_id: '1-56473829',
    institution_name: 'National Institute of Technology Karnataka',
    filename: 'NITK_Admissions_Upload_v1.csv',
    academic_year: '2026-27',
    uploaded_at: '2026-10-21T09:40:00Z',
    status: 'COMPLETED',
    rows_total: 310,
    rows_valid: 305,
    rows_error: 5,
    quality_score: 98.38,
  },
];

export const mockStudentRecord: StudentRecord = {
  apaar_id: '1234****9012',
  institution_aicte_id: '1-10293847',
  institution_student_id: '2026/DTU/CSE/042',
  full_name: 'Aarav Rajesh Kumar',
  name_norm: 'aarav rajesh kumar',
  dob: '2005-08-14',
  gender: 'M',
  category: 'GEN',
  pwd: false,
  program_code: 'CSE-UG-01',
  course_level: 'UG',
  academic_year: '2026-27',
  admission_date: '2026-07-28',
  admission_type: 'REGULAR',
  seat_type: 'REGULAR',
  quota: 'NONE',
  nationality: 'IN',
  nri_status: false,
  oci_status: false,
  fn_status: false,
  enrolment_status: 'ACTIVE',
  consent_status: 'GRANTED',
  consent_date: '2026-07-28',
  guardian_consent: true,
  email: 'aa***@dtu.ac.in',
  mobile: '+91 98****3210',
};

export const mockAuditChain: AuditChainStatus = {
  chain_valid: true,
  total_blocks: 1482,
  latest_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  genesis_hash: '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f',
  broken_link_index: null,
  last_verified_at: new Date().toISOString(),
};

export const mockAuditLogs: AuditLogEntry[] = [
  {
    id: 'log-1482',
    timestamp: new Date().toISOString(),
    actor_id: 'usr-inst-admin-01',
    actor_role: 'INSTITUTION_ADMIN',
    action: 'BATCH_UPLOAD',
    resource_type: 'BATCH',
    resource_id: 'batch-2026-dtu-001',
    details_masked: { filename: 'DTU_Admissions_2026_UG_Final.csv', rows_total: 285 },
    prev_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  },
  {
    id: 'log-1481',
    timestamp: new Date(Date.now() - 150000).toISOString(),
    actor_id: 'usr-verifier-01',
    actor_role: 'VERIFIER',
    action: 'CREDENTIAL_VERIFY',
    resource_type: 'CREDENTIAL',
    resource_id: 'cred-sdjwt-77192',
    details_masked: { apaar_masked: '1234****9012', verifier_org: 'Infosys Ltd' },
    prev_hash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
  },
  {
    id: 'log-1480',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    actor_id: 'usr-student-01',
    actor_role: 'STUDENT',
    action: 'CONSENT_UPDATE',
    resource_type: 'CONSENT',
    resource_id: '1234****9012',
    details_masked: { status: 'GRANTED', disclosed_count: 5 },
    prev_hash: '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
    hash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
  },
];

export const handlers = [
  // Auth Login
  http.post('/v1/auth/login', async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as Record<string, string>;
    const email = body.email || 'institution_admin@aicte.gov.in';
    const user = mockUsers[email] || {
      id: 'usr-dynamic',
      email,
      full_name: 'Authorized Portal User',
      role: (body.role as any) || 'INSTITUTION_ADMIN',
    };
    currentUser = user;

    const response: AuthResponse = {
      access_token: 'mock-jwt-token-' + btoa(user.email),
      token_type: 'Bearer',
      expires_in: 86400,
      user,
    };
    return HttpResponse.json(response);
  }),

  // Auth Me
  http.get('/v1/auth/me', () => {
    return HttpResponse.json(currentUser);
  }),

  // Batches Upload
  http.post('/v1/batches', async () => {
    return HttpResponse.json(mockBatchReport, { status: 201 });
  }),

  // Batches List
  http.get('/v1/batches', () => {
    return HttpResponse.json(mockBatchList);
  }),

  // Batch Report
  http.get('/v1/batches/:batch_id/report', () => {
    return HttpResponse.json(mockBatchReport);
  }),

  // Batch Detail
  http.get('/v1/batches/:batch_id', () => {
    return HttpResponse.json(mockBatchReport);
  }),

  // Batch Issues with filter query support
  http.get('/v1/batches/:batch_id/issues', ({ request }) => {
    const url = new URL(request.url);
    const ruleId = url.searchParams.get('rule_id');
    const severity = url.searchParams.get('severity');
    const search = url.searchParams.get('search')?.toLowerCase();

    let filtered = [...mockIssues];
    if (ruleId) {
      filtered = filtered.filter(i => i.rule_id === ruleId);
    }
    if (severity) {
      filtered = filtered.filter(i => i.severity === severity);
    }
    if (search) {
      filtered = filtered.filter(
        i =>
          i.value_masked.toLowerCase().includes(search) ||
          i.message.toLowerCase().includes(search) ||
          i.field.toLowerCase().includes(search)
      );
    }

    return HttpResponse.json({
      total: filtered.length,
      items: filtered,
    });
  }),

  // Programs & Intake
  http.get('/v1/programs/intake', () => {
    return HttpResponse.json(mockIntake);
  }),

  // Students - Single Record (Masked PII)
  http.get('/v1/students/:apaar_id', ({ params }) => {
    const { apaar_id } = params;
    return HttpResponse.json({
      ...mockStudentRecord,
      apaar_id: typeof apaar_id === 'string' && apaar_id.includes('****') ? apaar_id : '1234****9012',
    });
  }),

  // Duplicates Review List
  http.get('/v1/duplicates', () => {
    return HttpResponse.json(mockBatchReport.duplicate_clusters);
  }),

  // Duplicate Resolve
  http.post('/v1/duplicates/:cluster_id/resolve', async ({ request, params }) => {
    const body = (await request.json().catch(() => ({}))) as Record<string, string>;
    return HttpResponse.json({
      cluster_id: params.cluster_id,
      status: 'RESOLVED',
      resolved_at: new Date().toISOString(),
      note: body.note || 'Resolved by AICTE Analyst',
    });
  }),

  // Anomaly Feed
  http.get('/v1/anomalies', () => {
    return HttpResponse.json(mockBatchReport.anomalies);
  }),

  // Anomaly Acknowledge
  http.post('/v1/anomalies/:id/acknowledge', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      status: 'ACKNOWLEDGED',
      acknowledged_at: new Date().toISOString(),
    });
  }),

  // Consent Status & History
  http.get('/v1/consent/:apaar_id', ({ params }) => {
    const record: ConsentRecord = {
      apaar_id: (params.apaar_id as string) || '1234****9012',
      purpose: 'VERIFICATION_SHARE',
      status: 'GRANTED',
      granted_at: '2026-07-28T10:00:00Z',
      disclosed_fields: [
        'full_name',
        'apaar_id',
        'program_code',
        'course_level',
        'academic_year',
        'enrolment_status',
      ],
      guardian_consent_verified: true,
    };
    return HttpResponse.json(record);
  }),

  // Update Consent
  http.post('/v1/consent', async ({ request }) => {
    const body = (await request.json()) as Record<string, any>;
    return HttpResponse.json({
      ...body,
      updated_at: new Date().toISOString(),
    });
  }),

  // Credentials Issuance (SD-JWT)
  http.post('/v1/credentials/issue', async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as Record<string, any>;
    return HttpResponse.json({
      credential_jwt: 'eyJhbGciOiJFZERTQSI...sd-jwt-payload...signature',
      qr_payload: JSON.stringify({
        t: 'APAAR-SDMS-VC',
        apaar: body.apaar_id || '1234****9012',
        inst: '1-10293847',
        url: 'https://aicte.gov.in/v1/verify?vc=mock-sd-jwt-token',
        exp: '2028-06-30',
      }),
      expires_at: '2028-06-30T23:59:59Z',
    });
  }),

  // Verification Portal: POST /v1/verify
  http.post('/v1/verify', async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as Record<string, any>;
    const isInvalid = body.qr_payload?.includes('INVALID') || body.credential_jwt?.includes('INVALID');

    if (isInvalid) {
      const failedResult: VerificationResult = {
        verified: false,
        reason: 'Tampered Signature: Cryptographic hash does not match issuer root of trust.',
        issuer_did: 'did:web:untrusted-entity.org',
        issuer_name: 'Unknown / Untrusted Issuer',
        issuance_timestamp: '2025-01-01T00:00:00Z',
        checks: {
          signature_valid: false,
          issuer_trusted: false,
          not_revoked: true,
          expired: false,
        },
        disclosed_fields: {
          apaar_id_masked: '1234****9012',
          student_name: 'Unknown Entity',
          institution_name: 'Unverified Entity',
          program_code: 'UNKNOWN',
          academic_year: '2026-27',
          course_level: 'UG',
          enrolment_status: 'UNVERIFIED',
        },
      };
      return HttpResponse.json(failedResult);
    }

    const successResult: VerificationResult = {
      verified: true,
      issuer_did: 'did:web:aicte.gov.in:institutions:1-10293847',
      issuer_name: 'Delhi Technological University (AICTE Accredited)',
      issuance_timestamp: '2026-08-01T12:00:00Z',
      checks: {
        signature_valid: true,
        issuer_trusted: true,
        not_revoked: true,
        expired: false,
      },
      disclosed_fields: {
        apaar_id_masked: '1234****9012',
        student_name: 'Aarav Rajesh Kumar',
        institution_name: 'Delhi Technological University',
        program_code: 'B.Tech Computer Science & Engineering (CSE-UG-01)',
        academic_year: '2026-27',
        course_level: 'UG (Four Year Degree)',
        enrolment_status: 'ACTIVE (Verified Genuine)',
      },
    };
    return HttpResponse.json(successResult);
  }),

  // Audit Logs
  http.get('/v1/audit', () => {
    return HttpResponse.json(mockAuditLogs);
  }),

  // Audit Chain Integrity
  http.get('/v1/audit/verify-chain', () => {
    return HttpResponse.json(mockAuditChain);
  }),

  // Reports Generation
  http.post('/v1/reports/generate', async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as Record<string, string>;
    return HttpResponse.json({
      report_id: 'rep-' + Date.now(),
      title: `${body.type || 'Intake-Compliance'}-Report-2026`,
      download_url: `/reports/export-${Date.now()}.${body.format || 'pdf'}`,
      generated_at: new Date().toISOString(),
    });
  }),

  // Audit PII Reveal Action (Section 10)
  http.post('/v1/audit/reveal', async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as Record<string, any>;
    const newEntry: AuditLogEntry = {
      id: `log-${Date.now()}`,
      timestamp: new Date().toISOString(),
      actor_id: currentUser.id,
      actor_role: currentUser.role,
      action: 'PII_REVEAL',
      resource_type: 'STUDENT_PII',
      resource_id: body.studentId || 'std-2026-dtu-001',
      details_masked: {
        fieldType: body.fieldType,
        purpose: 'Regulatory Statutory Compliance Audit',
      },
      prev_hash: mockAuditChain.latest_hash,
      hash: 'sha256-block-' + Math.random().toString(36).substring(2, 10),
    };

    mockAuditLogs.unshift(newEntry);
    mockAuditChain.total_blocks += 1;
    mockAuditChain.latest_hash = newEntry.hash;

    return HttpResponse.json({
      success: true,
      entry: newEntry,
    });
  }),
];
