import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import {
  GraduationCap,
  ShieldCheck,
  Lock,
  Share2,
  QrCode,
  CheckCircle2,
  Copy,
  Calendar,
  Building,
} from 'lucide-react';
import { StudentRecord } from '../../api/types';

export const StudentView: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const [repositoryConsent, setRepositoryConsent] = useState(true);
  const [verificationConsent, setVerificationConsent] = useState(true);

  // Selective disclosure field toggles
  const [selectedFields, setSelectedFields] = useState<Record<string, boolean>>({
    full_name: true,
    apaar_id: true,
    institution_name: true,
    program_code: true,
    academic_year: true,
    enrolment_status: true,
    dob: false,
    category: false,
    mobile: false,
  });

  const { data: student } = useQuery<StudentRecord>({
    queryKey: ['student', 'me'],
    queryFn: async () => {
      const res = await fetch('/v1/students/1234****9012');
      return res.json();
    },
  });

  const toggleField = (key: string) => {
    setSelectedFields(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText('https://aicte.gov.in/v1/verify?vc=mock-sd-jwt-token-aarav');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Student Academic Identity & DigiLocker Credential
          </h2>
          <p className="text-sm text-muted-foreground">
            APAAR Lifelong Academic Registry • DPDP Act 2023 Consent-Gated Self-Sovereign Record
          </p>
        </div>
        <Badge variant="gov" className="text-xs">
          Role: STUDENT
        </Badge>
      </div>

      {/* Student Identity Card */}
      <Card className="border-l-4 border-l-gov-navy dark:border-l-blue-500">
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-lg">
                {student?.full_name?.charAt(0) || 'A'}
              </div>
              <div>
                <h3 className="text-xl font-bold text-foreground">
                  {student?.full_name}
                </h3>
                <p className="text-xs font-mono text-muted-foreground">
                  Permanent APAAR ID: <strong className="text-foreground">{student?.apaar_id}</strong>
                </p>
              </div>
            </div>
            <Badge variant="success" className="text-xs">
              Status: {student?.enrolment_status || 'ACTIVE'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
            <div className="p-3 rounded-lg bg-muted/30">
              <span className="text-muted-foreground block">Enrolled Institution:</span>
              <strong className="text-foreground">Delhi Technological University</strong>
              <span className="text-[10px] text-muted-foreground block font-mono">
                AICTE ID: {student?.institution_aicte_id}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-muted/30">
              <span className="text-muted-foreground block">Program & Level:</span>
              <strong className="text-foreground">{student?.program_code}</strong>
              <span className="text-[10px] text-muted-foreground block">
                {student?.course_level} (Four Year B.Tech)
              </span>
            </div>
            <div className="p-3 rounded-lg bg-muted/30">
              <span className="text-muted-foreground block">Academic Year & Admission:</span>
              <strong className="text-foreground">{student?.academic_year}</strong>
              <span className="text-[10px] text-muted-foreground block">
                Enrolled: {student?.admission_date} ({student?.seat_type})
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Consent Ledger & DPDP Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Lock className="h-4 w-4 text-primary" />
            Statutory Consent Ledger (DPDP 2023)
          </CardTitle>
          <CardDescription>
            You hold statutory control over who can query or verify your academic record. Consent may be revoked anytime.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-lg border bg-background">
            <div>
              <p className="font-semibold text-sm text-foreground">AICTE Central Repository Sync</p>
              <p className="text-xs text-muted-foreground">
                Authorize institution to commit clean admission record to national AICTE repository.
              </p>
            </div>
            <Button
              variant={repositoryConsent ? 'emerald' : 'outline'}
              size="sm"
              onClick={() => setRepositoryConsent(!repositoryConsent)}
              className="text-xs"
            >
              {repositoryConsent ? 'Consent Active' : 'Withdrawn'}
            </Button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg border bg-background">
            <div>
              <p className="font-semibold text-sm text-foreground">Third-Party Verifier Query Access</p>
              <p className="text-xs text-muted-foreground">
                Permit authorized employers and accreditation bodies to verify presented SD-JWT credentials.
              </p>
            </div>
            <Button
              variant={verificationConsent ? 'emerald' : 'outline'}
              size="sm"
              onClick={() => setVerificationConsent(!verificationConsent)}
              className="text-xs"
            >
              {verificationConsent ? 'Consent Active' : 'Withdrawn'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Selective Disclosure Presentation Builder */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Share2 className="h-4 w-4 text-primary" />
            Selective Disclosure Credential Builder (SD-JWT)
          </CardTitle>
          <CardDescription>
            Choose exactly which claims to disclose to third parties. Undisclosed attributes remain cryptographically blinded.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Claim Pickers */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[
              { key: 'full_name', label: 'Full Legal Name' },
              { key: 'apaar_id', label: 'Masked APAAR ID' },
              { key: 'institution_name', label: 'Institution Name' },
              { key: 'program_code', label: 'Enrolled Program' },
              { key: 'academic_year', label: 'Academic Year' },
              { key: 'enrolment_status', label: 'Enrolment Status' },
              { key: 'dob', label: 'Date of Birth (Sensitive)' },
              { key: 'category', label: 'Social Category (Sensitive)' },
              { key: 'mobile', label: 'Mobile Number (PII)' },
            ].map(item => (
              <label
                key={item.key}
                className={`flex items-center gap-2 p-2.5 rounded-lg border text-xs cursor-pointer transition-colors ${
                  selectedFields[item.key]
                    ? 'bg-primary/10 border-primary font-semibold text-primary dark:text-blue-300'
                    : 'bg-muted/30 border-border text-muted-foreground'
                }`}
              >
                <input
                  type="checkbox"
                  checked={!!selectedFields[item.key]}
                  onChange={() => toggleField(item.key)}
                  className="rounded text-primary focus:ring-primary h-3.5 w-3.5"
                />
                <span>{item.label}</span>
              </label>
            ))}
          </div>

          {/* Generated Verifiable Presentation Box */}
          <div className="p-4 rounded-lg bg-muted/40 border space-y-3">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
                <QrCode className="h-4 w-4 text-primary" />
                <span>Ed25519 Signed Presentation Token</span>
              </div>
              <span className="text-[11px] text-muted-foreground font-mono">
                Valid until: 2028-06-30 (2 Years)
              </span>
            </div>

            <div className="p-3 bg-background rounded border font-mono text-[11px] text-muted-foreground break-all">
              eyJhbGciOiJFZERTQSI...sd_jwt_salt_blinded_claims[
              {Object.keys(selectedFields).filter(k => selectedFields[k]).join(', ')}
              ]...sig
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyLink}
                className="text-xs flex items-center gap-1.5"
              >
                <Copy className="h-3.5 w-3.5" />
                {copied ? 'Copied to Clipboard!' : 'Copy Verification URL'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
