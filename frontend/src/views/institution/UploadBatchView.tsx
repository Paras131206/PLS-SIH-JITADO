import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Link } from 'react-router-dom';
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ShieldCheck,
  RefreshCw,
  ArrowRight,
  TrendingUp,
  XCircle,
  Users,
} from 'lucide-react';
import { BatchReport } from '../../api/types';
import { apiFetch } from '../../api/client';

export const UploadBatchView: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [progressStage, setProgressStage] = useState('');
  const [batchReport, setBatchReport] = useState<BatchReport | null>(null);

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setBatchReport(null);
      setUploadProgress(0);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
  });

  const downloadCsvTemplate = () => {
    // Canonical 26 headers from student_record.json (§5.1)
    const headers = [
      'apaar_id',
      'institution_aicte_id',
      'institution_student_id',
      'full_name',
      'dob',
      'gender',
      'category',
      'pwd',
      'program_code',
      'course_level',
      'academic_year',
      'admission_date',
      'admission_type',
      'seat_type',
      'supernumerary_scheme',
      'quota',
      'nationality',
      'nri_status',
      'oci_status',
      'fn_status',
      'enrolment_status',
      'consent_status',
      'consent_date',
      'guardian_consent',
      'email',
      'mobile',
    ];

    const sampleRow = [
      '223005401501',
      '1-10293847',
      '2026/DTU/CSE/001',
      'Krishna Joshi',
      '2005-04-02',
      'M',
      'SC',
      'false',
      'CSE-UG-01',
      'UG',
      '2026-27',
      '2026-07-09',
      'REGULAR',
      'REGULAR',
      '',
      'NONE',
      'IN',
      'false',
      'false',
      'false',
      'ACTIVE',
      'GRANTED',
      '2026-07-07',
      '',
      'krishna.joshi@example.edu.in',
      '9876543210',
    ];

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), sampleRow.join(',')].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'aicte_student_record_template.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleUploadSubmit = async () => {
    if (!file) return;
    setIsUploading(true);
    setUploadProgress(15);
    setProgressStage('Uploading file payload...');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('academic_year', '2026-27');
      formData.append('institution_aicte_id', '1-10293847');

      // Progress animation simulation
      setTimeout(() => {
        setUploadProgress(45);
        setProgressStage('Header normalisation & format verification...');
      }, 300);

      setTimeout(() => {
        setUploadProgress(75);
        setProgressStage('Vectorised rules V001–V020 & dedup check...');
      }, 700);

      const report = await apiFetch<BatchReport>('/batches', {
        method: 'POST',
        body: formData,
      });

      setTimeout(() => {
        setUploadProgress(100);
        setProgressStage('Batch validation complete!');
        setIsUploading(false);
        setBatchReport(report);
      }, 1100);
    } catch {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title & Guidance */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Upload Student Admission Batch
          </h2>
          <p className="text-sm text-muted-foreground">
            Canonical schema ingestion keyed by 12-digit APAAR ID with instant Deequ constraint reporting
          </p>
        </div>
        <Button
          variant="outline"
          onClick={downloadCsvTemplate}
          id="download-template-btn"
          className="flex items-center gap-2 text-xs"
        >
          <Download className="h-4 w-4 text-primary" />
          Download CSV Template (student_record.json)
        </Button>
      </div>

      {/* Metadata Context */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <label className="text-xs font-semibold text-muted-foreground uppercase">
            Active Institution (Uploader)
          </label>
          <div className="mt-1 font-mono font-medium text-sm text-foreground">
            Delhi Technological University (AICTE ID: 1-10293847)
          </div>
        </Card>
        <Card className="p-4">
          <label className="text-xs font-semibold text-muted-foreground uppercase">
            Admission Window & Intake Scope
          </label>
          <div className="mt-1 font-mono font-medium text-sm text-foreground">
            Academic Year 2026-27 • Rules V001–V020 Active
          </div>
        </Card>
      </div>

      {/* Drag & Drop Upload Zone */}
      {!batchReport && (
        <Card className="border-2 border-dashed">
          <CardContent className="pt-6">
            <div
              {...getRootProps()}
              id="dropzone-area"
              className={`p-10 flex flex-col items-center justify-center text-center cursor-pointer rounded-lg transition-colors ${
                isDragActive ? 'bg-primary/5 border-primary' : 'hover:bg-muted/30'
              }`}
            >
              <input {...getInputProps()} id="file-upload-input" />
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
                <UploadCloud className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-semibold text-foreground">
                {file ? file.name : 'Drag & drop student admissions file here'}
              </h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-sm">
                Supports CSV, XLSX files with 26 canonical columns matching student_record.json.
              </p>
              {file && (
                <div className="mt-4 flex items-center gap-2 text-xs font-mono bg-secondary px-3 py-1.5 rounded-full">
                  <FileSpreadsheet className="h-4 w-4 text-emerald-600" />
                  <span>{(file.size / 1024).toFixed(1)} KB</span>
                  <Badge variant="outline" className="text-[10px]">
                    Ready to Validate
                  </Badge>
                </div>
              )}
            </div>

            {/* Upload Progress Bar */}
            {isUploading && (
              <div className="mt-6 space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground font-mono">
                  <span>{progressStage}</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Action Submit */}
      {!batchReport && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span>Automatic PII masking & sha256 audit chaining active</span>
          </div>

          <Button
            variant="gov"
            id="start-upload-btn"
            disabled={!file || isUploading}
            onClick={handleUploadSubmit}
            className="min-w-[170px]"
          >
            {isUploading ? (
              <span className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Validating Rules...
              </span>
            ) : (
              'Run Validation Engine'
            )}
          </Button>
        </div>
      )}

      {/* Requirement 2: BatchReport Summary Cards */}
      {batchReport && (
        <div className="space-y-6 animate-in fade-in">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
              <div>
                <h3 className="font-bold text-base text-foreground">
                  Batch Validation Completed Successfully
                </h3>
                <p className="text-xs text-muted-foreground font-mono">
                  Batch ID: {batchReport.batch_id} • Status: {batchReport.status}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setBatchReport(null);
                  setFile(null);
                }}
                className="text-xs"
              >
                Upload Another File
              </Button>
              <Link to="/institution/issues">
                <Button variant="gov" size="sm" id="view-issues-btn" className="text-xs flex items-center gap-1.5">
                  <span>Inspect Issues Table ({batchReport.issues.length})</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>

          {/* Summary Cards: total / valid / warning / error, quality score */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <Card className="border-l-4 border-l-gov-navy dark:border-l-blue-500">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                  Total Rows
                </CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono" id="stat-total-rows">
                  {batchReport.rows_total}
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  100% processed
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-emerald-500">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                  Valid Records
                </CardTitle>
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400" id="stat-valid-rows">
                  {batchReport.rows_valid}
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Eligible for AICTE commit
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-amber-500">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                  Warnings
                </CardTitle>
                <AlertTriangle className="h-4 w-4 text-amber-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400" id="stat-warning-rows">
                  {batchReport.rows_warning}
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Non-blocking notifications
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-destructive">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                  Errors
                </CardTitle>
                <XCircle className="h-4 w-4 text-destructive" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono text-destructive" id="stat-error-rows">
                  {batchReport.rows_error}
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Require fix & resubmission
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-purple-500">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-xs font-semibold text-muted-foreground uppercase">
                  Quality Score
                </CardTitle>
                <TrendingUp className="h-4 w-4 text-purple-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold font-mono text-purple-600 dark:text-purple-400" id="stat-quality-score">
                  {batchReport.quality_score}%
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Deequ completeness metric
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
