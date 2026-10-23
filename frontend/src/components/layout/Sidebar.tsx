import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { cn } from '../../lib/utils';
import {
  Upload,
  AlertTriangle,
  BarChart3,
  Building2,
  FileCheck2,
  GitCompare,
  Activity,
  ShieldAlert,
  User,
  SlidersHorizontal,
  Share2,
  QrCode,
  History,
  Lock,
  Layers,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';

interface NavItem {
  title: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export const Sidebar: React.FC = () => {
  const { role, user } = useAuth();

  const getNavItems = (): { section: string; items: NavItem[] }[] => {
    switch (role) {
      case 'INSTITUTION_ADMIN':
      case 'INSTITUTION_STAFF':
        return [
          {
            section: 'Institution Admissions',
            items: [
              { title: 'Intake Dashboard', path: '/institution', icon: BarChart3 },
              { title: 'Upload Batch', path: '/institution/upload', icon: Upload, badge: 'New' },
              { title: 'Issues & Quality', path: '/institution/issues', icon: AlertTriangle, badge: '8 Flags' },
              { title: 'Approved Intake', path: '/institution/intake', icon: Building2 },
            ],
          },
        ];

      case 'AICTE_ADMIN':
      case 'AICTE_ANALYST':
        return [
          {
            section: 'AICTE National Oversight',
            items: [
              { title: 'National Console', path: '/aicte', icon: BarChart3 },
              { title: 'Batch Feed', path: '/aicte/batches', icon: Layers },
              { title: 'Duplicate Review', path: '/aicte/duplicates', icon: GitCompare, badge: '2 Pending' },
              { title: 'Anomaly Feed', path: '/aicte/anomalies', icon: Activity, badge: '1 Alert' },
              { title: 'Audit Chain', path: '/aicte/audit', icon: ShieldAlert },
            ],
          },
        ];

      case 'VERIFIER':
        return [
          {
            section: 'Third-Party Verification',
            items: [
              { title: 'Verify Credential', path: '/verifier', icon: QrCode },
              { title: 'Verification Log', path: '/verifier/history', icon: History },
            ],
          },
        ];

      case 'STUDENT':
        return [
          {
            section: 'Student DigiLocker & APAAR',
            items: [
              { title: 'My Record', path: '/student', icon: User },
              { title: 'Consent Ledger', path: '/student/consent', icon: Lock },
              { title: 'Share Builder', path: '/student/share', icon: Share2 },
            ],
          },
        ];

      default:
        return [];
    }
  };

  const navSections = getNavItems();

  return (
    <aside className="w-64 border-r bg-card/60 backdrop-blur-md flex flex-col justify-between shrink-0 min-h-[calc(100vh-4.25rem)]">
      <div className="p-4 space-y-6">
        {/* Role Identity Pill */}
        <div className="rounded-lg border bg-background/50 p-3 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            Portal Scope
          </div>
          <div className="mt-1 font-bold text-sm text-foreground">
            {role === 'INSTITUTION_ADMIN' && 'Institution Admin'}
            {role === 'INSTITUTION_STAFF' && 'Institution Staff'}
            {role === 'AICTE_ADMIN' && 'AICTE Central Admin'}
            {role === 'AICTE_ANALYST' && 'AICTE Intelligence Analyst'}
            {role === 'VERIFIER' && 'Authorized Verifier'}
            {role === 'STUDENT' && 'Student Credential Holder'}
          </div>
          {user?.institution_name && (
            <div className="mt-0.5 text-xs text-muted-foreground truncate" title={user.institution_name}>
              {user.institution_name}
            </div>
          )}
        </div>

        {/* Dynamic Navigation Links */}
        <nav className="space-y-4">
          {navSections.map((section, idx) => (
            <div key={idx} className="space-y-1">
              <h2 className="px-2 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                {section.section}
              </h2>
              <div className="space-y-1">
                {section.items.map(item => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      end={item.path === '/institution' || item.path === '/aicte'}
                      className={({ isActive }) =>
                        cn(
                          'flex items-center justify-between rounded-md px-3 py-2 text-sm font-medium transition-all group',
                          isActive
                            ? 'bg-primary text-primary-foreground shadow-xs font-semibold'
                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                        )
                      }
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon className="h-4 w-4 shrink-0 transition-transform group-hover:scale-110" />
                        <span>{item.title}</span>
                      </div>
                      {item.badge && (
                        <span className="rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 px-2 py-0.5 text-[10px] font-bold">
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Research & System Reference Links */}
          <div className="pt-2 border-t space-y-1">
            <h2 className="px-2 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              Research & Specs
            </h2>
            <NavLink
              to="/literature-review"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-all group',
                  isActive
                    ? 'bg-primary text-primary-foreground font-semibold'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )
              }
            >
              <BookOpen className="h-4 w-4 shrink-0 text-gov-gold" />
              <span>Lit Review (§9)</span>
            </NavLink>
          </div>
        </nav>
      </div>

      {/* System Status Banner at bottom */}
      <div className="p-4 border-t bg-muted/20">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            <span className="font-medium">MSW Mock Engine</span>
          </div>
          <span className="font-mono text-[10px] bg-secondary px-1.5 py-0.5 rounded">
            v0.1.0
          </span>
        </div>
        <p className="mt-1 text-[11px] text-muted-foreground leading-tight">
          PII Masked • DPDP 2023 Compliant • SHA-256 Audit Chain
        </p>
      </div>
    </aside>
  );
};
