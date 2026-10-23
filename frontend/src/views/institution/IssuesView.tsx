import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import {
  AlertTriangle,
  AlertOctagon,
  Search,
  Filter,
  Download,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
} from 'lucide-react';
import { Issue, RuleSeverity } from '../../api/types';

// Rule descriptions catalog (§6)
const ruleCatalogDescriptions: Record<string, string> = {
  V001: 'Required column missing from file header',
  V002: 'apaar_id missing or not 12 digits',
  V003: 'apaar_id not found in the (mock) APAAR registry',
  V004: 'APAAR registry name/DOB does not match uploaded name/DOB (fuzzy)',
  V005: 'Required field null or empty',
  V006: 'Invalid format (date, enum, email, mobile, ISO country)',
  V007: 'Duplicate apaar_id within the batch',
  V008: 'Duplicate institution_student_id within institution and year',
  V009: 'Probable duplicate person in batch with different APAAR (fuzzy name + DOB)',
  V010: 'Same APAAR ACTIVE at another institution in same academic year',
  V011: 'Probable same person at another institution under different APAAR',
  V012: 'Regular-seat enrolment > approved_intake for program',
  V013: 'Supernumerary count > allowed for that scheme',
  V014: 'Quota/nationality inconsistent (OCI or FN with IN, NRI mismatch)',
  V015: 'seat_type=SUPERNUMERARY with no scheme, or scheme on regular seat',
  V016: 'Age implausible for course_level',
  V017: 'admission_date outside academic-year window',
  V018: 'consent_status missing; or under 18 without guardian_consent',
  V019: 'program_code not in approved programs',
  V020: 'Batch metric anomaly vs history (null rate, NRI share, intake fill jump)',
};

export const IssuesView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedRule, setSelectedRule] = useState<string>('ALL');

  const { data, isLoading } = useQuery<{ total: number; items: Issue[] }>({
    queryKey: ['issues', selectedSeverity, selectedRule, searchTerm],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedSeverity !== 'ALL') params.append('severity', selectedSeverity);
      if (selectedRule !== 'ALL') params.append('rule_id', selectedRule);
      if (searchTerm) params.append('search', searchTerm);

      const res = await fetch(`/v1/batches/batch-2026-dtu-001/issues?${params.toString()}`);
      return res.json();
    },
  });

  const exportIssuesCsv = () => {
    if (!data?.items) return;
    const headers = ['row', 'rule_id', 'severity', 'field', 'message', 'value_masked'];
    const rows = data.items.map(i => [
      i.row,
      i.rule_id,
      i.severity,
      i.field,
      `"${i.message.replace(/"/g, '""')}"`,
      `"${i.value_masked}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'batch_validation_issues.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Batch Validation Issues
            <Badge variant="destructive" className="text-xs">
              {data?.total || 0} Issues Flagged
            </Badge>
          </h2>
          <p className="text-sm text-muted-foreground">
            Batch: <span className="font-mono font-medium">batch-2026-dtu-001</span> • Delhi Technological University
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={exportIssuesCsv}
            className="flex items-center gap-2 text-xs"
          >
            <Download className="h-4 w-4" />
            Export Issues CSV
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by masked APAAR (e.g. 1234****9012), rule ID or field..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
              Severity:
            </span>
            <select
              value={selectedSeverity}
              onChange={e => setSelectedSeverity(e.target.value)}
              className="text-xs bg-background border rounded-md px-3 py-2 font-medium focus:outline-none"
            >
              <option value="ALL">All Severities</option>
              <option value="ERROR">Errors (Blocking)</option>
              <option value="WARN">Warnings (Non-blocking)</option>
            </select>
          </div>

          {/* Rule Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
              Rule:
            </span>
            <select
              value={selectedRule}
              onChange={e => setSelectedRule(e.target.value)}
              className="text-xs bg-background border rounded-md px-3 py-2 font-medium focus:outline-none"
            >
              <option value="ALL">All Rules (V001–V020)</option>
              {Object.keys(ruleCatalogDescriptions).map(r => (
                <option key={r} value={r}>
                  {r} - {ruleCatalogDescriptions[r].slice(0, 32)}...
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Issues Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs uppercase bg-muted/60 text-muted-foreground border-b">
                <tr>
                  <th className="py-3 px-4">Row</th>
                  <th className="py-3 px-4">Rule ID</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Field</th>
                  <th className="py-3 px-4">Masked Value</th>
                  <th className="py-3 px-4">Validation Message</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-muted-foreground">
                      Loading issues...
                    </td>
                  </tr>
                ) : data?.items?.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-muted-foreground">
                      No issues match the selected filters.
                    </td>
                  </tr>
                ) : (
                  data?.items.map((issue, idx) => (
                    <tr key={idx} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4 font-mono text-xs text-muted-foreground">
                        #{issue.row}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className="font-mono font-bold text-xs bg-secondary px-2 py-0.5 rounded cursor-help inline-flex items-center gap-1"
                          title={ruleCatalogDescriptions[issue.rule_id] || issue.rule_id}
                        >
                          {issue.rule_id}
                          <HelpCircle className="h-3 w-3 text-muted-foreground" />
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant={issue.severity === 'ERROR' ? 'destructive' : 'warning'}
                          className="text-[10px] uppercase font-bold"
                        >
                          {issue.severity}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 font-mono text-xs font-semibold text-foreground">
                        {issue.field}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-muted-foreground">
                        {issue.value_masked}
                      </td>
                      <td className="py-3 px-4 text-xs text-foreground max-w-md">
                        {issue.message}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
