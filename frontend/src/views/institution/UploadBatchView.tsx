import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';

export const UploadBatchView: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const navigate = useNavigate();

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
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
      '123456789012',
      '1-10293847',
      '2026/DTU/CSE/001',
      'Aarav Kumar',
      '2005-08-14',
      'M',
      'GEN',
      'false',
      'CSE-UG-01',
      'UG',
      '2026-27',
      '2026-07-28',
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
      '2026-07-28',
      'true',
      'aarav@example.com',
      '+919876543210',
    ];

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), sampleRow.join(',')].join('\n');
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

    // Call MSW /v1/batches endpoint
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('academic_year', '2026-27');
      formData.append('institution_aicte_id', '1-10293847');

      await fetch('/v1/batches', {
        method: 'POST',
        body: formData,
      });

      setIsUploading(false);
      setUploadComplete(true);
      setTimeout(() => {
        navigate('/institution/issues');
      }, 1500);
    } catch {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Title & Guidance */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Upload Student Admission Batch
          </h2>
          <p className="text-sm text-muted-foreground">
            Validate CSV/Excel batch against AICTE intake rules, APAAR registry & dedup algorithms
          </p>
        </div>
        <Button
          variant="outline"
          onClick={downloadCsvTemplate}
          className="flex items-center gap-2 text-xs"
        >
          <Download className="h-4 w-4" />
          Download CSV Template
        </Button>
      </div>

      {/* Metadata Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <label className="text-xs font-semibold text-muted-foreground uppercase">
            Institution AICTE ID
          </label>
          <div className="mt-1 font-mono font-medium text-sm text-foreground">
            1-10293847 (Delhi Technological University)
          </div>
        </Card>
        <Card className="p-4">
          <label className="text-xs font-semibold text-muted-foreground uppercase">
            Academic Year
          </label>
          <div className="mt-1 font-mono font-medium text-sm text-foreground">
            2026-27 (Mandatory Window)
          </div>
        </Card>
      </div>

      {/* Drag & Drop Zone */}
      <Card className="border-2 border-dashed">
        <CardContent className="pt-6">
          <div
            {...getRootProps()}
            className={`p-10 flex flex-col items-center justify-center text-center cursor-pointer rounded-lg transition-colors ${
              isDragActive ? 'bg-primary/5 border-primary' : 'hover:bg-muted/30'
            }`}
          >
            <input {...getInputProps()} />
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
              <UploadCloud className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold text-foreground">
              {file ? file.name : 'Drag & drop student admissions file here'}
            </h3>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm">
              Supports CSV, XLSX files with up to 20,000 records. Required canonical fields include 12-digit APAAR ID, program code, and consent status.
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
        </CardContent>
      </Card>

      {/* Upload Action / Progress */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          <span>Automatic PII masking & sha256 batch audit logging active</span>
        </div>

        <Button
          variant="gov"
          disabled={!file || isUploading || uploadComplete}
          onClick={handleUploadSubmit}
          className="min-w-[160px]"
        >
          {isUploading ? (
            <span className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" />
              Validating Rules...
            </span>
          ) : uploadComplete ? (
            <span className="flex items-center gap-2 text-white">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              Validated!
            </span>
          ) : (
            'Run Validation Engine'
          )}
        </Button>
      </div>
    </div>
  );
};
