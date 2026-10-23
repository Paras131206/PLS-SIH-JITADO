import React from 'react';
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
  BarChart2,
  Users,
  ShieldCheck,
} from 'lucide-react';
import { BatchReport, BatchListItem } from '../../api/types';

export const InstitutionView: React.FC = () => {
  const { data: report, isLoading: reportLoading } = useQuery<BatchReport>({
    queryKey: ['batchReport', 'latest'],
    queryFn: async () => {
      const res = await fetch('/v1/batches/batch-2026-dtu-001/report');
      return res.json();
    },
  });

  const { data: batches } = useQuery<BatchListItem[]>({
    queryKey: ['batches'],
    queryFn: async () => {
      const res = await fetch('/v1/batches');
      return res.json();
    },
  });

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Institution Intake & Admissions Dashboard
          </h2>
          <p className="text-sm text-muted-foreground">
            Delhi Technological University (AICTE ID: 1-10293847) • Academic Year 2026-27
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/institution/upload">
            <Button variant="gov" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Upload New Batch
            </Button>
          </Link>
          <Link to="/institution/issues">
            <Button variant="outline" className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Review Issues (8)
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
            <div className="text-2xl font-bold">{report?.rows_total || 285}</div>
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
              {report?.rows_valid || 268}
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
              {report?.rows_error || 8}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {report?.rows_warning || 9} warnings flagged
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
              {report?.quality_score || 94.04}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Deequ completeness & uniqueness index
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Program Intake vs Enrolment Analysis */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Program Intake vs. Enrolment (Rule V012 / V013)</CardTitle>
              <CardDescription>
                Approved statutory capacity vs actual registered regular & supernumerary candidates
              </CardDescription>
            </div>
            <Badge variant="outline" className="font-mono text-xs">
              AICTE Handbook 2026-27
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-5">
            {report?.intake_summary.map(prog => {
              const maxTotal = prog.approved * 1.25;
              const approvedPct = (prog.approved / maxTotal) * 100;
              const enrolledPct = (prog.enrolled / maxTotal) * 100;
              const isExcess = prog.excess > 0;

              return (
                <div key={prog.program_code} className="space-y-2 p-3 rounded-lg border bg-muted/10">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between text-sm gap-1">
                    <span className="font-semibold text-foreground">
                      {prog.program_code}
                    </span>
                    <div className="flex items-center gap-3 text-xs">
                      <span>Approved: <strong className="text-foreground">{prog.approved}</strong></span>
                      <span>Enrolled: <strong className={isExcess ? 'text-destructive font-bold' : 'text-foreground'}>{prog.enrolled}</strong></span>
                      <span>Supernumerary: <strong className="text-gov-navy dark:text-blue-400">{prog.supernumerary}</strong></span>
                      {isExcess && (
                        <Badge variant="destructive" className="text-[10px] uppercase">
                          Excess +{prog.excess} (V012)
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Visual Progress Bar */}
                  <div className="h-3 w-full bg-secondary rounded-full overflow-hidden flex relative">
                    <div
                      className="bg-primary h-full transition-all"
                      style={{ width: `${Math.min(approvedPct, 100)}%` }}
                      title={`Approved Capacity: ${prog.approved}`}
                    />
                    {isExcess && (
                      <div
                        className="bg-destructive h-full transition-all animate-pulse"
                        style={{ width: `${Math.min(((prog.excess) / maxTotal) * 100, 30)}%` }}
                        title={`Excess Over Intake: +${prog.excess}`}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Batch Upload History */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Batch Submissions</CardTitle>
          <CardDescription>
            Audit log of uploaded CSV/XLSX files and their validation status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-muted/50 text-muted-foreground border-b">
                <tr>
                  <th className="py-3 px-4">Batch ID / Filename</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-4">Total Rows</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Quality Score</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {batches?.map(b => (
                  <tr key={b.batch_id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-medium text-foreground">{b.filename}</div>
                      <div className="font-mono text-xs text-muted-foreground">{b.batch_id}</div>
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground">
                      {new Date(b.uploaded_at).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </td>
                    <td className="py-3 px-4 font-mono">{b.rows_total}</td>
                    <td className="py-3 px-4">
                      <Badge variant={b.status === 'COMPLETED' ? 'success' : 'secondary'}>
                        {b.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        {b.quality_score}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link to="/institution/issues">
                        <Button variant="outline" size="sm" className="text-xs">
                          View Report
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
    </div>
  );
};
