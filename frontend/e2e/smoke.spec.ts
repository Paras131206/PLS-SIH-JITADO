import { Buffer } from 'node:buffer';
import { test, expect } from '@playwright/test';

test.describe('Phase 1 Smoke Test: Login → Upload Batch → Issues Table', () => {
  test('end-to-end flow from login to batch upload and issues review', async ({ page }) => {
    // 1. Visit Login Page
    await page.goto('/login');
    await expect(page).toHaveTitle(/APAAR-SDMS/i);
    await expect(page.getByRole('heading', { name: /APAAR-SDMS Portal/i })).toBeVisible();

    // 2. Perform Login as Institution Admin
    const emailInput = page.locator('#email-input');
    await emailInput.fill('institution_admin@aicte.gov.in');
    const passwordInput = page.locator('#password-input');
    await passwordInput.fill('password123');

    // Submit login form
    await page.locator('#login-submit-btn').click();

    // 3. Verify Role-Based Redirect to Institution Dashboard
    await page.waitForURL('**/institution');
    await expect(page.getByRole('heading', { name: /Institution Intake/i })).toBeVisible();

    // 4. Navigate to Upload Batch Page
    await page.goto('/institution/upload');
    await expect(page.getByRole('heading', { name: /Upload Student Admission Batch/i })).toBeVisible();

    // Verify Template Download button exists
    const downloadBtn = page.locator('#download-template-btn');
    await expect(downloadBtn).toBeVisible();

    // 5. Upload File
    const sampleCsvContent = `apaar_id,institution_aicte_id,institution_student_id,full_name,dob,gender,category,pwd,program_code,course_level,academic_year,admission_date,admission_type,seat_type,supernumerary_scheme,quota,nationality,nri_status,oci_status,fn_status,enrolment_status,consent_status,consent_date,guardian_consent,email,mobile
223005401501,1-10293847,2026-CSE-0001,Krishna Joshi,2005-04-02,M,SC,false,CSE-UG-01,UG,2026-27,2026-07-09,REGULAR,REGULAR,,NONE,IN,false,false,false,ACTIVE,GRANTED,2026-07-07,,krishna.joshi@example.edu.in,9876543210`;

    // Set file on file input
    const fileInput = page.locator('#file-upload-input');
    await fileInput.setInputFiles({
      name: 'admissions_batch_test.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(sampleCsvContent),
    });

    // 6. Click Run Validation Engine
    const validateBtn = page.locator('#start-upload-btn');
    await expect(validateBtn).toBeEnabled();
    await validateBtn.click();

    // 7. Verify BatchReport Summary Cards appear
    await expect(page.locator('#stat-total-rows')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#stat-valid-rows')).toBeVisible();
    await expect(page.locator('#stat-warning-rows')).toBeVisible();
    await expect(page.locator('#stat-error-rows')).toBeVisible();
    await expect(page.locator('#stat-quality-score')).toBeVisible();

    // 8. Click Inspect Issues Table button
    const viewIssuesBtn = page.locator('#view-issues-btn');
    await viewIssuesBtn.click();

    // 9. Verify Issues Table and Filter Functionality
    await page.waitForURL('**/institution/issues');
    await expect(page.locator('#issues-table')).toBeVisible();

    // Test Search input
    const searchInput = page.locator('#search-apaar-input');
    await searchInput.fill('1234****901X');
    await expect(page.locator('#issues-table')).toContainText('1234****901X');

    // Test Severity Filter
    const severitySelect = page.locator('#severity-filter');
    await severitySelect.selectOption('ERROR');
    await expect(page.locator('#issues-table')).toContainText('ERROR');
  });
});
