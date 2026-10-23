import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../api/types';
import {
  ShieldCheck,
  Moon,
  Sun,
  Building2,
  GraduationCap,
  FileCheck,
  Building,
  UserCheck,
  BookOpen,
} from 'lucide-react';

export const Header: React.FC = () => {
  const { user, role, switchRole, theme, toggleTheme } = useAuth();

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    switchRole(e.target.value as UserRole);
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 shadow-sm">
      {/* Official Government Tricolor Top Stripe */}
      <div className="tricolor-stripe" />

      {/* Primary Government Header */}
      <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6">
        {/* Emblem & Portal Title */}
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-gov-navy text-white shadow dark:bg-blue-600">
            <ShieldCheck className="h-7 w-7 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold tracking-wider uppercase text-gov-gold dark:text-amber-400">
                AICTE • Ministry of Education (MoE)
              </span>
              <span className="rounded bg-gov-navy/10 dark:bg-blue-900/40 px-1.5 py-0.2 text-[10px] font-semibold text-gov-navy dark:text-blue-300">
                Govt. of India
              </span>
            </div>
            <h1 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
              APAAR-SDMS
              <span className="text-xs font-normal text-muted-foreground hidden md:inline">
                | Student Data Management & Verification Portal
              </span>
            </h1>
          </div>
        </div>

        {/* Right Action Tools: Role Switcher, Theme & User */}
        <div className="flex items-center gap-3">
          {/* Documentation Link */}
          <a
            href="/literature-review"
            className="hidden lg:flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground border rounded-md px-2.5 py-1.5 bg-muted/30 transition-colors"
            title="Read Literature Review & Research Basis"
          >
            <BookOpen className="h-3.5 w-3.5 text-gov-blue dark:text-blue-400" />
            <span>Lit Review (§9)</span>
          </a>

          {/* Role Switcher (Crucial for Demo & Testing all RBAC Views) */}
          <div className="flex items-center gap-2 bg-secondary/80 rounded-lg p-1 border">
            <span className="text-xs font-medium text-muted-foreground pl-2 hidden sm:inline">
              Role:
            </span>
            <select
              value={role}
              onChange={handleRoleChange}
              className="bg-background text-foreground text-xs font-medium rounded-md px-2.5 py-1.5 border border-border focus:outline-none focus:ring-1 focus:ring-ring cursor-pointer"
              aria-label="Switch User Role"
            >
              <option value="INSTITUTION_ADMIN">🏛️ Institution Admin</option>
              <option value="INSTITUTION_STAFF">📋 Institution Staff</option>
              <option value="AICTE_ADMIN">🇮🇳 AICTE Admin</option>
              <option value="AICTE_ANALYST">📊 AICTE Analyst</option>
              <option value="VERIFIER">🔍 Verifier (Employer/HR)</option>
              <option value="STUDENT">🎓 Student (Aarav Kumar)</option>
            </select>
          </div>

          {/* Theme Switcher */}
          <button
            onClick={toggleTheme}
            className="flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background text-foreground hover:bg-muted transition-colors"
            aria-label="Toggle theme"
            title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
          >
            {theme === 'light' ? (
              <Moon className="h-4 w-4 text-slate-700" />
            ) : (
              <Sun className="h-4 w-4 text-amber-400" />
            )}
          </button>

          {/* User Profile Pill */}
          <div className="hidden sm:flex items-center gap-2 pl-2 border-l">
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs">
              {user?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="text-left text-xs leading-tight">
              <p className="font-semibold text-foreground truncate max-w-[130px]">
                {user?.full_name}
              </p>
              <p className="text-[10px] text-muted-foreground">
                {user?.institution_aicte_id
                  ? `AICTE: ${user.institution_aicte_id}`
                  : role.replace('_', ' ')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
