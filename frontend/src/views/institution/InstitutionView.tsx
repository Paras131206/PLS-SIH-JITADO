import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Link } from 'react-router-dom';
import {
  Upload,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  FileText,
  Users,
  ShieldCheck,
  RefreshCw,
  Radio,
  FileSpreadsheet,
  Globe,
  PieChart as PieIcon,
  Sparkles,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { BatchReport, BatchListItem } from '../../api/types';
import { apiFetch } from '../../api/client';
import { FixResubmitModal } from './FixResubmitModal';
import { mockBatchReport } from '../../mocks/handlers';

export const InstitutionView: React.FC = () => {
  const [fixModalOpen, setFixModalOpen] = useState(false);
  const [activeReport, setActiveReport] = useState<BatchReport>(mockBatchReport);
  const [sseActive, setSseActive] = useState(true);
  const [lastSseEventTime, setLastSseEventTime] = useState<string>('Just now');

  const { data: report } = useQuery<BatchReport>({
    queryKey: ['batchReport', 'latest'],
    queryFn: async () => {
      return apiFetch<BatchReport>('/batches/batch-2026-dtu-001/report');
    },
    initialData: activeReport,
  });

  const [batches, setBatches] = useState<BatchListItem[]>([
    {
      batch_id: 'batch-2026-dtu-001',
      institution_aicte_id: '1-10293847',
      institution_name: 'Delhi Technological University',
      filename: 'DTU_Admissions_2026_UG_Final.csv',
      academic_year: '2026-27',
      uploaded_at: '2026-10-23T14:30:00Z',
      status: 'COMPLETED',
      rows_total: 285,
      rows_valid: 268,
      rows_error: 8,
      quality_score: 94.04,
    },
    {
      batch_id: 'batch-2026-dtu-002',
      institution_aicte_id: '1-10293847',
      institution_name: 'Delhi Technological University',
      filename: 'DTU_MTech_Admissions_Round1.csv',
      academic_year: '2026-27',
      uploaded_at: '2026-10-23T18:15:00Z',
      status: 'PROCESSING',
      rows_total: 140,
      rows_valid: 135,
      rows_error: 1,
      quality_score: 97.5,
    },
    {
      batch_id: 'batch-2026-dtu-000',
      institution_aicte_id: '1-10293847',
      institution_name: 'Delhi Technological University',
      filename: 'DTU_Lateral_Entry_Intake.xlsx',
      academic_year: '2026-27',
      uploaded_at: '2026-10-21T09:40:00Z',
      status: 'COMPLETED',
      rows_total: 65,
      rows_valid: 65,
      rows_error: 0,
      quality_score: 100.0,
    },
  ]);

  // Live SSE listener simulation: updates batch status chips dynamically in real time
  useEffect(() => {
    if (!sseActive) return;

    const interval = setInterval(() => {
      setLastSseEventTime(new Date().toLocaleTimeString('en-IN'));
      setBatches(prev =>
        prev.map(b => {
          if (b.status === 'PROCESSING') {
            return {
              ...b,
              status: 'COMPLETED',
              rows_valid: 139,
              quality_score: 99.28,
            };
          }
          return b;
        })
      );
    }, 12000);

    return () => clearInterval(interval);
  }, [sseActive]);

  // Historical DQ score trend data across submissions
  const dqTrendData = [
    { batch: 'Batch 0 (Prelim)', score: 88.5, completeness: 91.0, uniqueness: 94.2 },
    { batch: 'Batch 1 (DTU-001)', score: 94.04, completeness: 96.5, uniqueness: 98.1 },
    { batch: 'Batch 2 (MTech)', score: 97.5, completeness: 98.2, uniqueness: 99.4 },
    { batch: 'Batch 3 (Resubmit)', score: activeReport.quality_score > 95 ? activeReport.quality_score : 99.28, completeness: 99.8, uniqueness: 100.0 },
  ];

  // Quota breakdown data (NRI, OCI, FN, PIO)
  const quotaBreakdown = [
    { quota: 'NRI (Non-Resident Indian)', code: 'NRI', enrolled: 18, statutoryLimit: 25, sharePct: 6.3, status: 'Compliant' },
    { quota: 'OCI (Overseas Citizen of India)', code: 'OCI', enrolled: 6, statutoryLimit: 15, sharePct: 2.1, status: 'Compliant' },
    { quota: 'FN (Foreign Nationals)', code: 'FN', enrolled: 5, statutoryLimit: 15, sharePct: 1.7, status: 'Compliant' },
    { quota: 'PIO / CIWG (Gulf Ward)', code: 'PIO', enrolled: 4, statutoryLimit: 10, sharePct: 1.4, status: 'Compliant' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              Institution Intake & Admissions Dashboard
            </h2>
            <Badge variant="outline" className="gap-1 font-mono text-[10px] bg-emerald-500/10 text-emerald-600 border-emerald-500/30">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
              Live SSE Sync: {lastSseEventTime}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Delhi Technological University (AICTE ID: 1-10293847) • Academic Year 2026-27
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFixModalOpen(true)}
            className="flex items-center gap-2 border-gov-saffron text-gov-saffron hover:bg-gov-saffron/10"
          >
            <RefreshCw className="h-4 w-4" />
            Fix & Resubmit Batch
          </Button>
          <Link to="/institution/upload">
            <Button variant="gov" size="sm" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Upload Batch
            </Button>
          </Link>
          <Link to="/institution/issues">
            <Button variant="outline" size="sm" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Issues ({activeReport.rows_error})
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-gov-navy dark:border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Enrolment
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeReport.rows_total}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Active student admission records
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-emerald-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Valid Clean Records
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {activeReport.rows_valid}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Ready for AICTE Central Repository
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Validation Issues
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {activeReport.rows_error}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {activeReport.rows_warning} warnings flagged
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Data Quality Score
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {activeReport.quality_score}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Deequ completeness & uniqueness index
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Program Intake vs Enrolment Bars (Rule V012 / V013) with Red Excess */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                Program Intake vs. Enrolment Bars (Approved / Regular / Supernumerary / Excess)
              </CardTitle>
              <CardDescription>
                Statutory AICTE approved capacity compared against enrolled regular, supernumerary and over-intake candidates
              </CardDescription>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-primary" /> Regular Enrolled</span>
              <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-gov-saffron" /> Supernumerary</span>
              <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-destructive" /> Excess (Violation)</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-5">
            {activeReport.intake_summary.map(prog => {
              const maxScale = Math.max(prog.approved * 1.3, prog.enrolled + prog.supernumerary + 10);
              const approvedWidth = (prog.approved / maxScale) * 100;
              const regularWidth = (Math.min(prog.enrolled, prog.approved) / maxScale) * 100;
              const supernumeraryWidth = (prog.supernumerary / maxScale) * 100;
              const excessWidth = prog.excess > 0 ? (prog.excess / maxScale) * 100 : 0;
              const isExcess = prog.excess > 0;

              return (
                <div key={prog.program_code} className="space-y-2 p-3.5 rounded-lg border bg-muted/10">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-sm gap-2">
                    <div>
                      <span className="font-bold text-foreground">{prog.program_code}</span>
                      <span className="text-xs text-muted-foreground ml-2">
                        Approved Statutory Intake: <strong className="text-foreground">{prog.approved}</strong>
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs">
                      <span>Regular: <strong className={isExcess ? 'text-destructive font-bold' : 'text-foreground'}>{prog.enrolled}</strong></span>
                      <span>Supernumerary: <strong className="text-gov-saffron font-semibold">{prog.supernumerary}</strong></span>
                      {isExcess ? (
                        <Badge variant="destructive" className="text-[10px] uppercase font-bold animate-pulse">
                          Excess +{prog.excess} (Rule V012)
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/40">
                          Capacity OK
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Multi-Segment Stacked Progress Bar */}
                  <div className="h-4 w-full bg-secondary rounded-full overflow-hidden flex relative shadow-inner">
                    {/* Regular Capacity Enrolled */}
                    <div
                      className="bg-primary h-full transition-all"
                      style={{ width: `${regularWidth}%` }}
                      title={`Regular Enrolled: ${Math.min(prog.enrolled, prog.approved)}`}
                    />
                    {/* Supernumerary Enrolled */}
                    <div
                      className="bg-gov-saffron h-full transition-all opacity-90"
                      style={{ width: `${supernumeraryWidth}%` }}
                      title={`Supernumerary Seats: ${prog.supernumerary}`}
                    />
                    {/* Excess Over Intake (In RED) */}
                    {isExcess && (
                      <div
                        className="bg-destructive h-full transition-all animate-pulse"
                        style={{ width: `${excessWidth}%` }}
                        title={`Excess Over Statutory Intake: +${prog.excess} (V012 Breach)`}
                      />
                    )}
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                    <span>Approved Benchmark: {prog.approved} seats</span>
                    <span className={isExcess ? 'text-destructive font-semibold' : ''}>
                      Total Registered: {prog.enrolled + prog.supernumerary} seats (Fill Rate: {(((prog.enrolled + prog.supernumerary) / prog.approved) * 100).toFixed(1)}%)
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Grid: Quota Breakdown & DQ Score Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quota Breakdown (NRI / OCI / FN / PIO) */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Globe className="h-5 w-5 text-gov-navy dark:text-blue-400" />
                  Statutory Quota Breakdown (NRI / OCI / FN / PIO)
                </CardTitle>
                <CardDescription>
                  Admissions admitted under special international and NRI quotas (Rule V014 compliance)
                </CardDescription>
              </div>
              <Badge variant="outline" className="font-mono text-xs">
                AICTE §5 Quotas
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {quotaBreakdown.map(q => (
                <div key={q.code} className="space-y-1.5 p-3 rounded-lg border bg-muted/20">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-foreground">{q.quota}</span>
                    <span className="font-mono text-muted-foreground">
                      <strong className="text-foreground">{q.enrolled}</strong> / {q.statutoryLimit} seats max
                    </span>
                  </div>
                  <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                    <div
                      className="bg-gov-navy dark:bg-blue-500 h-full rounded-full transition-all"
                      style={{ width: `${(q.enrolled / q.statutoryLimit) * 100}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-0.5">
                    <span>{q.sharePct}% of total batch enrolment</span>
                    <span className="text-emerald-600 font-medium">✓ {q.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* DQ Score Trend Across Batches (Deequ Metrics) */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-purple-500" />
                  Data Quality (DQ) Score Trend Across Batches
                </CardTitle>
                <CardDescription>
                  Batch-wise Deequ verification curve tracking completeness, consistency and deduplication
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-xs text-purple-600 border-purple-300">
                Deequ 3.0
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dqTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#9333ea" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#9333ea" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="batch" tick={{ fontSize: 11 }} />
                  <YAxis domain={[80, 100]} tick={{ fontSize: 11 }} unit="%" />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', borderRadius: '8px', fontSize: '12px' }}
                    formatter={(val: number) => [`${val}%`, 'DQ Score']}
                  />
                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#9333ea"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#scoreGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="flex items-center justify-around border-t pt-3 text-xs text-muted-foreground">
              <div className="text-center">
                <div className="font-bold text-foreground text-sm">99.8%</div>
                <div>Completeness</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-foreground text-sm">99.9%</div>
                <div>Uniqueness</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-emerald-600 text-sm">98.5%</div>
                <div>Avg Clean Ratio</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Batch History List with Status Chips Updated Live via SSE */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                Batch History List & Real-Time SSE Status Feed
              </CardTitle>
              <CardDescription>
                Server-Sent Events (SSE) streaming updates batch status chips live upon validation completion
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setBatches(prev => [
                    {
                      batch_id: `batch-2026-dtu-${Date.now().toString().slice(-3)}`,
                      institution_aicte_id: '1-10293847',
                      institution_name: 'Delhi Technological University',
                      filename: 'Admissions_Stream_Live_v3.csv',
                      academic_year: '2026-27',
                      uploaded_at: new Date().toISOString(),
                      status: 'PROCESSING',
                      rows_total: 95,
                      rows_valid: 90,
                      rows_error: 0,
                      quality_score: 98.9,
                    },
                    ...prev,
                  ]);
                }}
                className="text-xs gap-1.5 h-8"
              >
                <Radio className="h-3 w-3 text-amber-500 animate-pulse" />
                Simulate SSE Event
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-muted/50 text-muted-foreground border-b">
                <tr>
                  <th className="py-3 px-4">Batch ID / Filename</th>
                  <th className="py-3 px-4">Uploaded At</th>
                  <th className="py-3 px-4">Total Rows</th>
                  <th className="py-3 px-4">Live Status (SSE)</th>
                  <th className="py-3 px-4">DQ Score</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {batches.map(b => (
                  <tr key={b.batch_id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-medium text-foreground">{b.filename}</div>
                      <div className="font-mono text-xs text-muted-foreground">{b.batch_id}</div>
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground">
                      {new Date(b.uploaded_at).toLocaleString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3 px-4 font-mono">{b.rows_total}</td>
                    <td className="py-3 px-4">
                      {b.status === 'PROCESSING' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-600 border border-amber-500/30 animate-pulse">
                          <RefreshCw className="h-3 w-3 animate-spin" />
                          PROCESSING (SSE)
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-600 border border-emerald-500/30">
                          <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                          COMPLETED
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        {b.quality_score}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setFixModalOpen(true)}
                        className="text-xs h-8 text-gov-saffron hover:bg-gov-saffron/10 border-gov-saffron/30"
                      >
                        Fix & Resubmit
                      </Button>
                      <Link to="/institution/issues">
                        <Button variant="outline" size="sm" className="text-xs h-8">
                          Issues Table
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Fix and Resubmit Flow Modal */}
      <FixResubmitModal
        isOpen={fixModalOpen}
        onClose={() => setFixModalOpen(false)}
        originalBatchId="batch-2026-dtu-001"
        originalReport={activeReport}
        onBatchUpdated={newReport => setActiveReport(newReport)}
      />
    </div>
  );
};
