import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Link } from 'react-router-dom';
import {
  Building2,
  Users,
  AlertTriangle,
  TrendingUp,
  GitCompare,
  Activity,
  ShieldCheck,
  ArrowUpRight,
} from 'lucide-react';

export const AicteConsoleView: React.FC = () => {
  const excessLeaderboard = [
    { institution: 'Delhi Technological University', aicte_id: '1-10293847', state: 'Delhi', program: 'CSE-UG-01', approved: 120, enrolled: 124, excess: 4 },
    { institution: 'Apex Institute of Technology', aicte_id: '1-44928172', state: 'Uttar Pradesh', program: 'IT-UG-01', approved: 60, enrolled: 63, excess: 3 },
    { institution: 'Shri Ram Engineering Academy', aicte_id: '1-88273619', state: 'Maharashtra', program: 'MECH-UG-02', approved: 60, enrolled: 62, excess: 2 },
  ];

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            AICTE National Admissions & Intake Console
          </h2>
          <p className="text-sm text-muted-foreground">
            Centralized Real-Time Surveillance & Statutory Intake Compliance Engine
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success" className="gap-1 text-xs">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
            Live Monitoring (2026-27)
          </Badge>
        </div>
      </div>

      {/* National KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-gov-navy dark:border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Institutions Reporting
            </CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,248</div>
            <p className="text-xs text-muted-foreground mt-1">
              Out of 3,420 accredited institutions
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-emerald-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Verified Student Admissions
            </CardTitle>
            <Users className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              482,910
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Keyed with 12-digit APAAR ID
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              National Avg DQ Score
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              96.8%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Deequ constraint compliance
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-destructive">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Over-Intake Violations
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">14</div>
            <p className="text-xs text-muted-foreground mt-1">
              Programs exceeding statutory intake
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Excess Enrolment Leaderboard */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg text-destructive flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Excess Enrolment Leaderboard (Rule V012)
              </CardTitle>
              <CardDescription>
                Institutions reporting regular-seat student admissions exceeding approved AICTE capacity
              </CardDescription>
            </div>
            <Badge variant="destructive">Statutory Breach</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-muted/50 text-muted-foreground border-b">
                <tr>
                  <th className="py-3 px-4">Institution Name</th>
                  <th className="py-3 px-4">AICTE ID</th>
                  <th className="py-3 px-4">State</th>
                  <th className="py-3 px-4">Program</th>
                  <th className="py-3 px-4">Approved</th>
                  <th className="py-3 px-4">Enrolled</th>
                  <th className="py-3 px-4 text-destructive font-bold">Excess Seats</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {excessLeaderboard.map((item, idx) => (
                  <tr key={idx} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4 font-medium text-foreground">{item.institution}</td>
                    <td className="py-3 px-4 font-mono text-xs">{item.aicte_id}</td>
                    <td className="py-3 px-4 text-xs">{item.state}</td>
                    <td className="py-3 px-4 font-mono text-xs">{item.program}</td>
                    <td className="py-3 px-4">{item.approved}</td>
                    <td className="py-3 px-4 font-semibold">{item.enrolled}</td>
                    <td className="py-3 px-4 text-destructive font-bold">+{item.excess}</td>
                    <td className="py-3 px-4 text-right">
                      <Button variant="outline" size="sm" className="text-xs">
                        Audit Notice
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Quick Action Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/aicte/duplicates" className="group">
          <Card className="h-full border hover:border-primary/50 transition-all p-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:scale-105 transition-transform">
                <GitCompare className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                  Duplicate Review Queue
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  2 cross-institution duplicate clusters pending resolution
                </p>
              </div>
            </div>
          </Card>
        </Link>

        <Link to="/aicte/anomalies" className="group">
          <Card className="h-full border hover:border-primary/50 transition-all p-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-600 group-hover:scale-105 transition-transform">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                  Anomaly Feed
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  1 statistical surge flagged by Isolation Forest
                </p>
              </div>
            </div>
          </Card>
        </Link>

        <Link to="/aicte/audit" className="group">
          <Card className="h-full border hover:border-primary/50 transition-all p-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-600 group-hover:scale-105 transition-transform">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                  Tamper-Evident Audit Chain
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  1,482 blocks verified • Zero chain breaks
                </p>
              </div>
            </div>
          </Card>
        </Link>
      </div>
    </div>
  );
};
