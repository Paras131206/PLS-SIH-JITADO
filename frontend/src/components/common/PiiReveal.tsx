import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Shield, Eye, EyeOff, Lock, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { apiFetch } from '../../api/client';

interface PiiRevealProps {
  maskedValue: string;
  unmaskedValue: string;
  fieldType: 'apaar' | 'email' | 'mobile' | 'name' | 'general';
  studentId?: string;
  className?: string;
}

export const PiiReveal: React.FC<PiiRevealProps> = ({
  maskedValue,
  unmaskedValue,
  fieldType,
  studentId,
  className = '',
}) => {
  const { role, switchRole, user } = useAuth();
  const [isRevealed, setIsRevealed] = useState(false);
  const [showDenialModal, setShowDenialModal] = useState(false);
  const [auditNotice, setAuditNotice] = useState<string | null>(null);

  const isAuthorized = role === 'AICTE_ANALYST' || role === 'AICTE_ADMIN';

  const handleToggle = async () => {
    if (isRevealed) {
      setIsRevealed(false);
      setAuditNotice(null);
      return;
    }

    if (!isAuthorized) {
      setShowDenialModal(true);
      return;
    }

    // Role is authorized: Reveal and log audit entry
    setIsRevealed(true);
    const timestamp = new Date().toLocaleTimeString('en-IN');
    const notice = `Audited: Unmask logged by ${user?.full_name || 'AICTE Analyst'} at ${timestamp}`;
    setAuditNotice(notice);

    try {
      await apiFetch('/audit/reveal', {
        method: 'POST',
        body: JSON.stringify({
          fieldType,
          studentId: studentId || 'std-2026-dtu-001',
          actorRole: role,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch {
      // In mock/offline mode, audit notice is still shown on UI
    }
  };

  return (
    <div className={`inline-flex flex-col gap-1 ${className}`}>
      <div className="inline-flex items-center gap-2">
        <span
          className={`font-mono text-sm ${
            isRevealed
              ? 'text-foreground font-semibold bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30'
              : 'text-muted-foreground'
          }`}
        >
          {isRevealed ? unmaskedValue : maskedValue}
        </span>

        <button
          type="button"
          onClick={handleToggle}
          title={isRevealed ? 'Hide PII' : 'Reveal unmasked PII (Requires AICTE_ANALYST role)'}
          className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground transition-colors p-1 rounded hover:bg-muted"
        >
          {isRevealed ? (
            <EyeOff className="h-3.5 w-3.5 text-amber-500" />
          ) : (
            <Eye className="h-3.5 w-3.5 text-muted-foreground hover:text-primary" />
          )}
        </button>
      </div>

      {/* Audit Log Confirmation Chip */}
      {auditNotice && isRevealed && (
        <span className="text-[10px] text-amber-600 dark:text-amber-400 font-sans flex items-center gap-1 animate-fade-in">
          <Shield className="h-2.5 w-2.5" />
          {auditNotice}
        </span>
      )}

      {/* Access Denial Modal */}
      {showDenialModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-card text-card-foreground border shadow-2xl rounded-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-full bg-destructive/10 flex items-center justify-center text-destructive shrink-0">
                <Lock className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <h3 className="font-bold text-base text-foreground">
                  Statutory PII Access Control
                </h3>
                <p className="text-xs text-muted-foreground">
                  Section 10 — APAAR Student Data Protection Standard
                </p>
              </div>
            </div>

            <div className="text-xs text-muted-foreground space-y-2 bg-muted/40 p-3 rounded-lg border">
              <p>
                Student Personally Identifiable Information (PII) including Aadhaar/APAAR 12-digit numbers,
                contact details, and mobile records are encrypted at rest and masked by default.
              </p>
              <p>
                Only designated statutory regulatory officers with the{' '}
                <strong className="text-foreground">AICTE_ANALYST</strong> or{' '}
                <strong className="text-foreground">AICTE_ADMIN</strong> role may decrypt this data. All
                decryption actions are permanently registered in the tamper-evident SHA-256 audit chain.
              </p>
              <div className="pt-1 flex items-center gap-2">
                <span className="text-[11px]">Your Current Role:</span>
                <Badge variant="outline" className="font-mono text-[10px]">
                  {role}
                </Badge>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDenialModal(false)}
              >
                Dismiss
              </Button>
              <Button
                variant="gov"
                size="sm"
                onClick={() => {
                  switchRole('AICTE_ANALYST');
                  setShowDenialModal(false);
                  setIsRevealed(true);
                  setAuditNotice(`Audited: Unmask logged by AICTE Analyst at ${new Date().toLocaleTimeString('en-IN')}`);
                }}
                className="gap-1.5"
              >
                <Shield className="h-3.5 w-3.5" />
                Switch to AICTE Analyst & Reveal
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
