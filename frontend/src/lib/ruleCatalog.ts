/**
 * Rule Catalog Dictionary from contracts/rule_catalog.yaml
 * Shared contract for V001–V020 descriptions, severities and parameters
 */

export interface RuleDefinition {
  id: string;
  severity: 'ERROR' | 'WARN';
  description: string;
  fields: string[];
  paramsDescription?: string;
  name?: string;
  statutoryBasis?: string;
}

export const RULE_CATALOG: Record<string, RuleDefinition> = {
  V001: {
    id: 'V001',
    severity: 'ERROR',
    description: 'Required column missing from file header',
    fields: ['file_header'],
    paramsDescription: 'Checks all 20 required canonical columns from student_record.json',
  },
  V002: {
    id: 'V002',
    severity: 'ERROR',
    description: 'apaar_id missing or not 12 digits',
    fields: ['apaar_id'],
    paramsDescription: 'Exactly 12 numeric digits (pattern: ^[0-9]{12}$)',
  },
  V003: {
    id: 'V003',
    severity: 'ERROR',
    description: 'apaar_id not found in the (mock) APAAR registry',
    fields: ['apaar_id'],
    paramsDescription: 'Verified against national APAAR registry adapter',
  },
  V004: {
    id: 'V004',
    severity: 'WARN',
    description: 'APAAR registry name/DOB does not match the uploaded name/DOB (fuzzy)',
    fields: ['full_name', 'dob'],
    paramsDescription: 'Token-set ratio name similarity threshold >= 0.85',
  },
  V005: {
    id: 'V005',
    severity: 'ERROR',
    description: 'Required field null or empty',
    fields: ['apaar_id', 'full_name', 'dob', 'gender', 'program_code', 'course_level'],
    paramsDescription: 'Non-null check on required canonical student fields',
  },
  V006: {
    id: 'V006',
    severity: 'ERROR',
    description: 'Invalid format (date, enum, email, mobile, ISO country)',
    fields: ['dob', 'admission_date', 'gender', 'category', 'quota'],
    paramsDescription: 'Enforces ISO dates, standard enums, and valid country codes',
  },
  V007: {
    id: 'V007',
    severity: 'ERROR',
    description: 'Duplicate apaar_id within the batch',
    fields: ['apaar_id'],
    paramsDescription: 'Uniqueness check of apaar_id within the same upload batch',
  },
  V008: {
    id: 'V008',
    severity: 'ERROR',
    description: 'Duplicate institution_student_id within institution and year',
    fields: ['institution_student_id'],
    paramsDescription: 'Unique roll number per academic year at this institution',
  },
  V009: {
    id: 'V009',
    severity: 'WARN',
    description: 'Probable duplicate person in the batch with a different APAAR (fuzzy name + DOB)',
    fields: ['full_name', 'dob', 'gender'],
    paramsDescription: 'Fellegi-Sunter probabilistic linkage score >= 0.75',
  },
  V010: {
    id: 'V010',
    severity: 'ERROR',
    description: 'Same APAAR ACTIVE at another institution in the same academic year',
    fields: ['apaar_id'],
    paramsDescription: 'Cross-institution duplicate active enrolment collision',
  },
  V011: {
    id: 'V011',
    severity: 'WARN',
    description: 'Probable same person at another institution under a different APAAR',
    fields: ['full_name', 'dob'],
    paramsDescription: 'Cross-institution phonetic / fuzzy matching queue',
  },
  V012: {
    id: 'V012',
    severity: 'ERROR',
    description: 'Regular-seat enrolment > approved_intake for the program',
    fields: ['program_code', 'seat_type'],
    paramsDescription: 'Enforces statutory approved intake limits per AICTE approval letter',
  },
  V013: {
    id: 'V013',
    severity: 'ERROR',
    description: 'Supernumerary count > allowed for that scheme',
    fields: ['supernumerary_scheme'],
    paramsDescription: 'Validates scheme caps for TFW, PMSSS, J&K, NE, and FN/OCI/NRI',
  },
  V014: {
    id: 'V014',
    severity: 'ERROR',
    description: 'Quota/nationality inconsistent (OCI or FN with IN, NRI flag mismatch)',
    fields: ['quota', 'nationality', 'oci_status', 'fn_status'],
    paramsDescription: 'OCI/FN requires nationality != IN; NRI requires nri_status=true',
  },
  V015: {
    id: 'V015',
    severity: 'ERROR',
    description: 'seat_type=SUPERNUMERARY with no scheme, or a scheme on a regular seat',
    fields: ['seat_type', 'supernumerary_scheme'],
    paramsDescription: 'Mutual consistency of seat_type and supernumerary_scheme',
  },
  V016: {
    id: 'V016',
    severity: 'WARN',
    description: 'Age implausible for course_level',
    fields: ['dob', 'course_level'],
    paramsDescription: 'e.g. age < 16 for UG, or age < 20 for PhD',
  },
  V017: {
    id: 'V017',
    severity: 'ERROR',
    description: 'admission_date outside the academic-year window',
    fields: ['admission_date'],
    paramsDescription: 'Must fall within designated AICTE academic calendar cutoff',
  },
  V018: {
    id: 'V018',
    severity: 'ERROR',
    description: 'consent_status missing; or under 18 without guardian_consent',
    fields: ['consent_status', 'guardian_consent'],
    paramsDescription: 'DPDP 2023 statutory mandate: minor students require guardian consent',
  },
  V019: {
    id: 'V019',
    severity: 'ERROR',
    description: 'program_code not in approved programs',
    fields: ['program_code'],
    paramsDescription: 'Program must be listed in program_intake for this institution',
  },
  V020: {
    id: 'V020',
    severity: 'WARN',
    description: 'Batch metric anomaly vs. institution history (null rate, NRI share, intake fill jump)',
    fields: ['batch_metrics'],
    paramsDescription: 'Isolation Forest and z-score drift detection (sigma > 3.0)',
  },
};
