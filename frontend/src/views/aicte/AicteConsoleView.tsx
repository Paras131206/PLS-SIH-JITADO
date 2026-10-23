import React, { useState } from 'react';
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
  ChevronDown,
  ChevronRight,
  Radio,
  Clock,
  Layers,
  ArrowRight,
  MapPin,
  CheckCircle2,
} from 'lucide-react';

interface StateDrilldownData {
  state: string;
  institutionsCount: number;
  totalStudents: number;
  approvedIntake: number;
  excessCount: number;
  institutions: {
    name: string;
    aicte_id: string;
    totalEnrolled: number;
    approvedCapacity: number;
    excessPrograms: number;
    programs: {
      code: string;
      name: string;
      approved: number;
      enrolled: number;
      supernumerary: number;
      excess: number;
    }[];
  }[];
}

export const AicteConsoleView: React.FC = () => {
  const [expandedState, setExpandedState] = useState<string | null>('Delhi');
  const [expandedInst, setExpandedInst] = useState<string | null>('1-10293847');

  const excessLeaderboard = [
    { institution: 'Delhi Technological University', aicte_id: '1-10293847', state: 'Delhi', program: 'CSE-UG-01', approved: 120, enrolled: 124, excess: 4 },
    { institution: 'Apex Institute of Technology', aicte_id: '1-44928172', state: 'Uttar Pradesh', program: 'IT-UG-01', approved: 60, enrolled: 63, excess: 3 },
    { institution: 'Shri Ram Engineering Academy', aicte_id: '1-88273619', state: 'Maharashtra', program: 'MECH-UG-02', approved: 60, enrolled: 62, excess: 2 },
    { institution: 'Kalinga Institute of Tech', aicte_id: '1-33829104', state: 'Odisha', program: 'ECE-UG-01', approved: 90, enrolled: 92, excess: 2 },
  ];

  // State-wise hierarchical drilldown data: State → Institution → Program
  const stateData: StateDrilldownData[] = [
    {
      state: 'Delhi',
      institutionsCount: 42,
      totalStudents: 18450,
      approvedIntake: 18200,
      excessCount: 4,
      institutions: [
        {
          name: 'Delhi Technological University',
          aicte_id: '1-10293847',
          totalEnrolled: 285,
          approvedCapacity: 270,
          excessPrograms: 1,
          programs: [
            { code: 'CSE-UG-01', name: 'B.Tech Computer Science', approved: 120, enrolled: 124, supernumerary: 14, excess: 4 },
            { code: 'ECE-UG-02', name: 'B.Tech Electronics & Comm.', approved: 90, enrolled: 88, supernumerary: 8, excess: 0 },
            { code: 'AI-DS-UG-03', name: 'B.Tech Artificial Intelligence', approved: 60, enrolled: 60, supernumerary: 5, excess: 0 },
          ],
        },
        {
          name: 'Indira Gandhi Delhi Technical University for Women',
          aicte_id: '1-20938471',
          totalEnrolled: 210,
          approvedCapacity: 210,
          excessPrograms: 0,
          programs: [
            { code: 'IT-UG-01', name: 'B.Tech Information Technology', approved: 120, enrolled: 120, supernumerary: 10, excess: 0 },
            { code: 'MAE-UG-01', name: 'B.Tech Mechanical & Auto', approved: 90, enrolled: 85, supernumerary: 6, excess: 0 },
          ],
        },
      ],
    },
    {
      state: 'Maharashtra',
      institutionsCount: 312,
      totalStudents: 84200,
      approvedIntake: 84050,
      excessCount: 3,
      institutions: [
        {
          name: 'College of Engineering Pune (COEP)',
          aicte_id: '1-92837465',
          totalEnrolled: 420,
          approvedCapacity: 420,
          excessPrograms: 0,
          programs: [
            { code: 'COMP-UG-01', name: 'B.Tech Computer Engineering', approved: 150, enrolled: 150, supernumerary: 15, excess: 0 },
            { code: 'ELEC-UG-01', name: 'B.Tech Electrical Engineering', approved: 120, enrolled: 118, supernumerary: 12, excess: 0 },
          ],
        },
        {
          name: 'Shri Ram Engineering Academy',
          aicte_id: '1-88273619',
          totalEnrolled: 182,
          approvedCapacity: 180,
          excessPrograms: 1,
          programs: [
            { code: 'MECH-UG-02', name: 'B.Tech Mechanical Engineering', approved: 60, enrolled: 62, supernumerary: 4, excess: 2 },
          ],
        },
      ],
    },
    {
      state: 'Karnataka',
      institutionsCount: 228,
      totalStudents: 69400,
      approvedIntake: 69400,
      excessCount: 1,
      institutions: [
        {
          name: 'National Institute of Technology Karnataka (NITK)',
          aicte_id: '1-56473829',
          totalEnrolled: 310,
          approvedCapacity: 310,
          excessPrograms: 0,
          programs: [
            { code: 'CSE-UG-01', name: 'B.Tech Computer Science', approved: 110, enrolled: 110, supernumerary: 10, excess: 0 },
            { code: 'ECE-UG-01', name: 'B.Tech Electronics', approved: 100, enrolled: 98, supernumerary: 8, excess: 0 },
          ],
        },
      ],
    },
    {
      state: 'Uttar Pradesh',
      institutionsCount: 340,
      totalStudents: 78500,
      approvedIntake: 78200,
      excessCount: 4,
      institutions: [
        {
          name: 'Apex Institute of Technology',
          aicte_id: '1-44928172',
          totalEnrolled: 183,
          approvedCapacity: 180,
          excessPrograms: 1,
          programs: [
            { code: 'IT-UG-01', name: 'B.Tech Information Technology', approved: 60, enrolled: 63, supernumerary: 3, excess: 3 },
          ],
        },
      ],
    },
  ];

  // Live Batch Feed stream
  const [liveBatches] = useState([
    { id: 'feed-1', institution: 'Delhi Technological University', aicte_id: '1-10293847', batch: 'DTU_UG_Final.csv', rows: 285, score: 94.04, time: '2 mins ago', status: 'COMPLETED' },
    { id: 'feed-2', institution: 'College of Engineering Pune', aicte_id: '1-92837465', batch: 'COEP_Batch_2026.xlsx', rows: 420, score: 99.52, time: '14 mins ago', status: 'COMPLETED' },
    { id: 'feed-3', institution: 'NIT Karnataka Surathkal', aicte_id: '1-56473829', batch: 'NITK_Admissions_v1.csv', rows: 310, score: 98.38, time: '38 mins ago', status: 'COMPLETED' },
    { id: 'feed-4', institution: 'Apex Institute of Tech', aicte_id: '1-44928172', batch: 'Apex_Intake_2026.csv', rows: 183, score: 91.20, time: '1 hr ago', status: 'FLAGGED' },
  ]);

  return (
    <div className="space-y-6">
      {/* Title Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              AICTE National Admissions & Intake Surveillance Console v1
            </h2>
            <Badge variant="outline" className="gap-1 font-mono text-[10px] bg-emerald-500/10 text-emerald-600 border-emerald-500/30">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
              Surveillance Engine Active
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Centralized Real-Time Regulatory Surveillance & Statutory Intake Enforcement Engine (2026-27)
          </p>
        </div>
      </div>

      {/* KPI Tiles (Institutions, Students, Avg DQ Score, Excess Count) */}
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
              Out of 3,420 accredited institutions (36.5%)
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-emerald-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Students Admitted
            </CardTitle>
            <Users className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              482,910
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Keyed with 12-digit APAAR ID registry
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Average DQ Score
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              96.8%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              National Deequ rule validation index
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-destructive">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Excess-Enrolment Count
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">14</div>
            <p className="text-xs text-muted-foreground mt-1">
              Programs exceeding statutory intake (V012)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Excess Enrolment Leaderboard (Rule V012) */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-lg text-destructive flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Excess Enrolment Leaderboard (Rule V012 Breaches)
              </CardTitle>
              <CardDescription>
                Institutions reporting regular-seat student admissions exceeding approved AICTE intake limits
              </CardDescription>
            </div>
            <Badge variant="destructive" className="font-mono text-xs">
              Statutory Non-Compliance
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-muted/50 text-muted-foreground border-b">
                <tr>
                  <th className="py-3 px-4">Rank / Institution</th>
                  <th className="py-3 px-4">AICTE ID</th>
                  <th className="py-3 px-4">State</th>
                  <th className="py-3 px-4">Program Code</th>
                  <th className="py-3 px-4">Approved</th>
                  <th className="py-3 px-4">Enrolled</th>
                  <th className="py-3 px-4 text-destructive font-bold">Excess Seats</th>
                  <th className="py-3 px-4 text-right">Statutory Action</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {excessLeaderboard.map((item, idx) => (
                  <tr key={idx} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-muted-foreground">
                          #{idx + 1}
                        </span>
                        <span className="font-medium text-foreground">{item.institution}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-muted-foreground">{item.aicte_id}</td>
                    <td className="py-3 px-4 text-xs">{item.state}</td>
                    <td className="py-3 px-4 font-mono text-xs font-semibold">{item.program}</td>
                    <td className="py-3 px-4">{item.approved}</td>
                    <td className="py-3 px-4 font-semibold">{item.enrolled}</td>
                    <td className="py-3 px-4 text-destructive font-bold">+{item.excess}</td>
                    <td className="py-3 px-4 text-right">
                      <Button variant="outline" size="sm" className="text-xs border-destructive/40 text-destructive hover:bg-destructive/10 h-7">
                        Issue Notice
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* State-Wise Hierarchical Drilldown: State → Institution → Program */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <MapPin className="h-5 w-5 text-primary" />
                State-Wise Intake & Enrolment Drilldown (State → Institution → Program)
              </CardTitle>
              <CardDescription>
                Click any state row to expand constituent institutions, then click an institution to inspect per-program capacity
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-xs font-mono">
              36 States & UTs
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {stateData.map(st => {
              const isStateExpanded = expandedState === st.state;

              return (
                <div key={st.state} className="border rounded-lg overflow-hidden bg-card transition-all">
                  {/* Level 1: State Row */}
                  <div
                    onClick={() => setExpandedState(isStateExpanded ? null : st.state)}
                    className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3.5 bg-muted/30 hover:bg-muted/60 cursor-pointer gap-2 select-none"
                  >
                    <div className="flex items-center gap-2.5">
                      {isStateExpanded ? (
                        <ChevronDown className="h-4 w-4 text-primary shrink-0" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                      )}
                      <div>
                        <span className="font-bold text-base text-foreground">{st.state}</span>
                        <span className="text-xs text-muted-foreground ml-3">
                          {st.institutionsCount} Institutions Reporting
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-xs">
                      <span>Total Enrolled: <strong className="font-mono">{st.totalStudents.toLocaleString('en-IN')}</strong></span>
                      <span>Approved: <strong className="font-mono text-muted-foreground">{st.approvedIntake.toLocaleString('en-IN')}</strong></span>
                      {st.excessCount > 0 ? (
                        <Badge variant="destructive" className="text-[10px]">
                          {st.excessCount} Over-Intake
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-400">
                          100% Compliant
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Level 2: Institutions in State */}
                  {isStateExpanded && (
                    <div className="p-4 bg-muted/10 border-t space-y-3 animate-fade-in">
                      <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                        Accredited Institutions in {st.state}
                      </div>

                      {st.institutions.map(inst => {
                        const isInstExpanded = expandedInst === inst.aicte_id;

                        return (
                          <div key={inst.aicte_id} className="border rounded-lg bg-background overflow-hidden">
                            {/* Institution Header */}
                            <div
                              onClick={() => setExpandedInst(isInstExpanded ? null : inst.aicte_id)}
                              className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 hover:bg-muted/40 cursor-pointer gap-2"
                            >
                              <div className="flex items-center gap-2">
                                {isInstExpanded ? (
                                  <ChevronDown className="h-3.5 w-3.5 text-primary shrink-0" />
                                ) : (
                                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                                )}
                                <div>
                                  <span className="font-semibold text-sm text-foreground">{inst.name}</span>
                                  <span className="font-mono text-xs text-muted-foreground ml-2">({inst.aicte_id})</span>
                                </div>
                              </div>

                              <div className="flex items-center gap-3 text-xs">
                                <span>Intake Fill: <strong>{inst.totalEnrolled} / {inst.approvedCapacity}</strong></span>
                                {inst.excessPrograms > 0 && (
                                  <Badge variant="destructive" className="text-[10px]">
                                    {inst.excessPrograms} Excess Program
                                  </Badge>
                                )}
                              </div>
                            </div>

                            {/* Level 3: Programs in Institution */}
                            {isInstExpanded && (
                              <div className="p-3 bg-muted/20 border-t space-y-2 text-xs">
                                <div className="font-medium text-muted-foreground">Departmental Program Allocations:</div>
                                <div className="space-y-2">
                                  {inst.programs.map(prog => (
                                    <div
                                      key={prog.code}
                                      className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-2 rounded bg-background border gap-2"
                                    >
                                      <div>
                                        <span className="font-bold text-foreground font-mono">{prog.code}</span>
                                        <span className="text-muted-foreground ml-2">{prog.name}</span>
                                      </div>
                                      <div className="flex items-center gap-3">
                                        <span>Approved: <strong className="text-foreground">{prog.approved}</strong></span>
                                        <span>Enrolled: <strong>{prog.enrolled}</strong></span>
                                        <span>Supernumerary: <strong className="text-gov-saffron">{prog.supernumerary}</strong></span>
                                        {prog.excess > 0 ? (
                                          <Badge variant="destructive" className="text-[10px]">
                                            +{prog.excess} EXCESS
                                          </Badge>
                                        ) : (
                                          <Badge variant="outline" className="text-[10px] text-emerald-600">
                                            Normal
                                          </Badge>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Live Batch Feed Stream */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                <Radio className="h-5 w-5 text-emerald-500 animate-pulse" />
                National Live Batch Feed (Surveillance Stream)
              </CardTitle>
              <CardDescription>
                Real-time incoming batch submissions streaming from accredited institutions across India
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-xs font-mono bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-400">
              ● Active SSE Socket
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {liveBatches.map(feed => (
              <div
                key={feed.id}
                className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3.5 rounded-lg border bg-muted/10 hover:bg-muted/30 transition-all gap-2"
              >
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0">
                    <Building2 className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-foreground">{feed.institution}</div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                      <span className="font-mono">{feed.aicte_id}</span>
                      <span>•</span>
                      <span>{feed.batch}</span>
                      <span>•</span>
                      <span>{feed.rows} records</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs">
                  <span className="text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {feed.time}
                  </span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    DQ {feed.score}%
                  </span>
                  <Badge variant={feed.status === 'COMPLETED' ? 'success' : 'destructive'} className="text-[10px]">
                    {feed.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
