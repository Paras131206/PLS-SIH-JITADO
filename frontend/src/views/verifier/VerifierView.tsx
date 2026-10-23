import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import {
  QrCode,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  FileKey,
  Building,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { VerificationResult } from '../../api/types';

export const VerifierView: React.FC = () => {
  const [tokenInput, setTokenInput] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);

  const handleVerify = async (testToken?: string) => {
    const payloadToTest = testToken !== undefined ? testToken : tokenInput;
    setIsVerifying(true);
    setResult(null);

    try {
      const res = await fetch('/v1/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credential_jwt: payloadToTest || 'eyJhbGciOiJFZERTQS12YWxpZ...mock',
          qr_payload: payloadToTest,
        }),
      });
      const data: VerificationResult = await res.json();
      setResult(data);
      setIsVerifying(false);
    } catch {
      setIsVerifying(false);
    }
  };

  const loadGenuineSample = () => {
    const genuineJwt = 'eyJhbGciOiJFZERTQSI...genuine_sd_jwt_aarav_kumar...valid_signature';
    setTokenInput(genuineJwt);
    handleVerify(genuineJwt);
  };

  const loadTamperedSample = () => {
    const tamperedJwt = 'INVALID_SIGNATURE_TAMPERED_PAYLOAD_TOKEN';
    setTokenInput(tamperedJwt);
    handleVerify(tamperedJwt);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Third-Party Academic Credential Verifier Portal
          </h2>
          <p className="text-sm text-muted-foreground">
            Instantly verify SD-JWT credentials & QR codes issued by AICTE-accredited institutions with selective disclosure
          </p>
        </div>
        <Badge variant="gov" className="text-xs">
          Role: VERIFIER (Authorized)
        </Badge>
      </div>

      {/* Input / Scanner Card */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <QrCode className="h-5 w-5 text-primary" />
                Scan or Paste Verifiable Presentation
              </CardTitle>
              <CardDescription>
                Accepts W3C SD-JWT tokens or raw JSON payloads scanned from the student certificate QR
              </CardDescription>
            </div>
            {/* Quick Demo Pre-sets */}
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadGenuineSample}
                className="text-xs"
              >
                Load Genuine Sample
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={loadTamperedSample}
                className="text-xs text-destructive hover:bg-destructive/10"
              >
                Load Tampered Sample
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <textarea
            value={tokenInput}
            onChange={e => setTokenInput(e.target.value)}
            placeholder="Paste raw SD-JWT string, DID signature, or scanned QR payload here..."
            className="w-full h-24 p-3 text-xs font-mono bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
          />

          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              Verification runs zero-gas offline Ed25519 signature checks in &lt;50ms
            </span>
            <Button
              variant="gov"
              onClick={() => handleVerify()}
              disabled={isVerifying}
              className="min-w-[140px]"
            >
              {isVerifying ? (
                <span className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Verifying...
                </span>
              ) : (
                'Verify Credential'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Verification Result Display */}
      {result && (
        <Card
          className={`border-2 animate-in fade-in ${
            result.verified
              ? 'border-emerald-500 bg-emerald-500/5'
              : 'border-destructive bg-destructive/5'
          }`}
        >
          <CardHeader>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div
                  className={`h-12 w-12 rounded-full flex items-center justify-center text-white ${
                    result.verified ? 'bg-emerald-600' : 'bg-destructive'
                  }`}
                >
                  {result.verified ? (
                    <CheckCircle2 className="h-7 w-7" />
                  ) : (
                    <XCircle className="h-7 w-7" />
                  )}
                </div>
                <div>
                  <h3
                    className={`text-xl font-extrabold tracking-wide uppercase ${
                      result.verified ? 'text-emerald-700 dark:text-emerald-400' : 'text-destructive'
                    }`}
                  >
                    {result.verified ? 'Credential Verified Genuine' : 'Verification Failed / Tampered'}
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {result.verified
                      ? 'Cryptographic digital signature valid • Issuer AICTE trust accredited'
                      : result.reason}
                  </p>
                </div>
              </div>

              <Badge variant={result.verified ? 'success' : 'destructive'} className="text-xs font-bold uppercase">
                {result.verified ? 'STATUS: VALID' : 'STATUS: INVALID'}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Cryptographic Sub-Checks */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-medium">
              <div className="p-2.5 rounded bg-background border flex items-center gap-2">
                {result.checks.signature_valid ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-destructive shrink-0" />
                )}
                <span>Ed25519 Signature</span>
              </div>
              <div className="p-2.5 rounded bg-background border flex items-center gap-2">
                {result.checks.issuer_trusted ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-destructive shrink-0" />
                )}
                <span>AICTE Issuer Trusted</span>
              </div>
              <div className="p-2.5 rounded bg-background border flex items-center gap-2">
                {result.checks.not_revoked ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-destructive shrink-0" />
                )}
                <span>Not Revoked</span>
              </div>
              <div className="p-2.5 rounded bg-background border flex items-center gap-2">
                {!result.checks.expired ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-destructive shrink-0" />
                )}
                <span>Not Expired</span>
              </div>
            </div>

            {/* Disclosed Claims (Selective Disclosure Demonstration) */}
            {result.verified && (
              <div className="mt-4 pt-4 border-t space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    Selectively Disclosed Student Claims
                  </h4>
                  <span className="text-[11px] text-muted-foreground font-mono">
                    Protected PII (Category, DOB, Mobile) Blinded
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-background p-4 rounded-lg border">
                  <div>
                    <span className="text-muted-foreground block">Student APAAR ID:</span>
                    <strong className="font-mono text-sm text-foreground">
                      {result.disclosed_fields.apaar_id_masked}
                    </strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Student Full Name:</span>
                    <strong className="text-sm text-foreground">
                      {result.disclosed_fields.student_name}
                    </strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Issuing Accredited Institution:</span>
                    <strong className="text-foreground">
                      {result.disclosed_fields.institution_name}
                    </strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Enrolled Program & Code:</span>
                    <strong className="text-foreground">
                      {result.disclosed_fields.program_code}
                    </strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Academic Year:</span>
                    <strong className="text-foreground">
                      {result.disclosed_fields.academic_year}
                    </strong>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Enrolment Status:</span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                      {result.disclosed_fields.enrolment_status}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
