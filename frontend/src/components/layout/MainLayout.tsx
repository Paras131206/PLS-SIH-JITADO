import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ShieldCheck, ExternalLink } from 'lucide-react';

export const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground antialiased selection:bg-amber-500 selection:text-white">
      {/* Official Government Header */}
      <Header />

      {/* Body with Role Sidebar and View Container */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Official Government Footer */}
      <footer className="border-t bg-card text-muted-foreground text-xs py-4 px-6">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-3 text-center md:text-left">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-gov-navy dark:text-blue-400" />
            <span>
              All India Council for Technical Education (AICTE) • National Student Data Management System (APAAR-SDMS)
            </span>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span>DPDP Act 2023 Compliant</span>
            <span>•</span>
            <span>Zero-Gas SD-JWT Verified</span>
            <span>•</span>
            <a
              href="https://apaar.education.gov.in"
              target="_blank"
              rel="noreferrer"
              className="hover:underline flex items-center gap-1 text-primary"
            >
              APAAR Portal <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
