import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import * as XLSX from 'xlsx';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import {
  AlertTriangle,
  Search,
  Filter,
  Download,
  HelpCircle,
  XCircle,
  FileSpreadsheet,
  ChevronLeft,
  ChevronRight,
  Info,
  RefreshCw,
  Shield,
  FileText,
} from 'lucide-react';
import { Issue, RuleSeverity } from '../../api/types';
import { RULE_CATALOG } from '../../lib/ruleCatalog';
import { apiFetch } from '../../api/client';
import { PiiReveal } from '../../components/common/PiiReveal';
import { FixResubmitModal } from './FixResubmitModal';
import { mockBatchReport } from '../../mocks/handlers';

export const IssuesView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedRule, setSelectedRule] = useState<string>('ALL');
  const [selectedField, setSelectedField] = useState<string>('ALL');
  const [hoveredRule, setHoveredRule] = useState<string | null>(null);
  const [fixModalOpen, setFixModalOpen] = useState(false);
  const [currentReport, setCurrentReport] = useState(mockBatchReport);

  // Pagination / virtualised window state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading } = useQuery<{ total: number; items: Issue[] }>({
    queryKey: ['issues', selectedSeverity, selectedRule, selectedField, searchTerm, currentReport.batch_id],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedSeverity !== 'ALL') params.append('severity', selectedSeverity);
      if (selectedRule !== 'ALL') params.append('rule_id', selectedRule);
      if (searchTerm) params.append('search', searchTerm);

      const res = await apiFetch<{ total: number; items: Issue[] }>(
        `/batches/${currentReport.batch_id}/issues?${params.toString()}`
      );
      return res;
    },
    initialData: { total: currentReport.issues.length, items: currentReport.issues },
  });

  // Extract all distinct fields present in issues for field filter dropdown
  const allFields = useMemo(() => {
    const fields = new Set<string>();
    data?.items?.forEach(i => fields.add(i.field));
    return Array.from(fields).sort();
  }, [data?.items]);

  // Client-side filtering including field and search by masked APAAR
  const filteredIssues = useMemo(() => {
    if (!data?.items) return [];
    return data.items.filter(issue => {
      // Field filter
      if (selectedField !== 'ALL' && issue.field !== selectedField) {
        return false;
      }
      // Masked APAAR or text search
      if (searchTerm) {
        const term = searchTerm.trim().toLowerCase();
        const matchesApaar = issue.value_masked.toLowerCase().includes(term);
        const matchesMsg = issue.message.toLowerCase().includes(term);
        const matchesField = issue.field.toLowerCase().includes(term);
        const matchesRule = issue.rule_id.toLowerCase().includes(term);
        if (!matchesApaar && !matchesMsg && !matchesField && !matchesRule) {
          return false;
        }
      }
      return true;
    });
  }, [data?.items, selectedField, searchTerm]);

  // Virtualised / windowed page slice
  const totalItems = filteredIssues.length;
  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  const paginatedIssues = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredIssues.slice(start, start + pageSize);
  }, [filteredIssues, currentPage, pageSize]);

  // Download Issues in genuine Excel XLSX format (Phase 2 Requirement 3)
  const downloadIssuesXlsx = () => {
    if (filteredIssues.length === 0) return;
    const worksheetData = filteredIssues.map(issue => {
      const catalog = RULE_CATALOG[issue.rule_id];
      return {
        'Row': issue.row,
        'Rule ID': issue.rule_id,
        'Severity': issue.severity,
        'Field': issue.field,
        'Masked Value': issue.value_masked,
        'Message': issue.message,
        'Rule Name': catalog?.name || 'Statutory Validation',
        'Statutory Reference': catalog?.statutoryBasis || 'AICTE APH 2026-27',
      };
    });

    const worksheet = XLSX.utils.json_to_sheet(worksheetData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Issues_Report');
    XLSX.writeFile(workbook, `Batch_${currentReport.batch_id}_Issues.xlsx`);
  };

  const exportIssuesCsv = () => {
    if (filteredIssues.length === 0) return;
    const headers = ['row', 'rule_id', 'severity', 'field', 'message', 'value_masked'];
    const rows = filteredIssues.map(i => [
      i.row,
      i.rule_id,
      i.severity,
      i.field,
      `"${i.message.replace(/"/g, '""')}"`,
      `"${i.value_masked}"`,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `batch_issues_${selectedRule}_${selectedSeverity}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const clearAllFilters = () => {
    setSearchTerm('');
    setSelectedSeverity('ALL');
    setSelectedRule('ALL');
    setSelectedField('ALL');
    setCurrentPage(1);
  };

  const getUnmaskedValueForIssue = (issue: Issue): string => {
    switch (issue.rule_id) {
      case 'V002':
        return '12345678901X';
      case 'V007':
        return '234567898901';
      case 'V004':
        return 'Karthik Subramanian Raman';
      case 'V010':
        return '987654322109';
      case 'V014':
        return 'IN (India) / OCI: true';
      case 'V018':
        return 'DOB: 2009-04-12 (Aarav Verma)';
      default:
        return issue.value_masked;
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Batch Validation Issues
            <Badge variant="destructive" className="text-xs" id="issues-count-badge">
              {filteredIssues.length} Issues Shown
            </Badge>
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Batch: <span className="font-mono font-medium text-foreground">{currentReport.batch_id}</span> • Verified against contracts/rule_catalog.yaml
          </p>
        </div>
        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant="gov"
            size="sm"
            onClick={() => setFixModalOpen(true)}
            className="flex items-center gap-1.5 text-xs bg-gov-saffron hover:bg-gov-saffron/90 text-white"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Fix & Resubmit Batch
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={downloadIssuesXlsx}
            disabled={filteredIssues.length === 0}
            className="flex items-center gap-1.5 text-xs border-emerald-500/40 text-emerald-600 hover:bg-emerald-500/10"
          >
            <FileSpreadsheet className="h-3.5 w-3.5 text-emerald-600" />
            Download Issue XLSX
          </Button>
          <Button
            variant="outline"
            size="sm"
            id="export-csv-btn"
            onClick={exportIssuesCsv}
            disabled={filteredIssues.length === 0}
            className="flex items-center gap-1.5 text-xs"
          >
            <Download className="h-3.5 w-3.5" />
            Export Issues CSV
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar Controls */}
      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Search Input */}
            <div className="relative">
              <label htmlFor="search-apaar-input" className="sr-only">
                Search by masked APAAR
              </label>
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                id="search-apaar-input"
                type="text"
                placeholder="Search masked APAAR or message..."
                value={searchTerm}
                onChange={e => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-9 pr-4 py-2 rounded-md border text-sm bg-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground"
                >
                  <XCircle className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Severity Filter */}
            <div>
              <label htmlFor="severity-filter" className="sr-only">
                Filter by Severity
              </label>
              <div className="relative">
                <select
                  id="severity-filter"
                  aria-label="Filter by Severity"
                  value={selectedSeverity}
                  onChange={e => {
                    setSelectedSeverity(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full py-2 px-3 rounded-md border text-sm bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="ALL">All Severities</option>
                  <option value="ERROR">ERROR only</option>
                  <option value="WARN">WARN only</option>
                </select>
              </div>
            </div>

            {/* Rule ID Filter */}
            <div>
              <label htmlFor="rule-filter" className="sr-only">
                Filter by Rule ID
              </label>
              <div className="relative">
                <select
                  id="rule-filter"
                  aria-label="Filter by Rule ID"
                  value={selectedRule}
                  onChange={e => {
                    setSelectedRule(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full py-2 px-3 rounded-md border text-sm bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="ALL">All Rules (V001–V020)</option>
                  {Object.keys(RULE_CATALOG).map(ruleId => (
                    <option key={ruleId} value={ruleId}>
                      {ruleId}: {RULE_CATALOG[ruleId].name || RULE_CATALOG[ruleId].description}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Field Filter */}
            <div>
              <label htmlFor="field-filter" className="sr-only">
                Filter by Field
              </label>
              <div className="relative">
                <select
                  id="field-filter"
                  aria-label="Filter by Field"
                  value={selectedField}
                  onChange={e => {
                    setSelectedField(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="w-full py-2 px-3 rounded-md border text-sm bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="ALL">All Fields</option>
                  {allFields.map(f => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Active Filter Tags */}
          {(selectedSeverity !== 'ALL' || selectedRule !== 'ALL' || selectedField !== 'ALL' || searchTerm) && (
            <div className="flex items-center justify-between text-xs pt-2 border-t text-muted-foreground">
              <div className="flex items-center gap-2 flex-wrap">
                <span>Active Filters:</span>
                {selectedSeverity !== 'ALL' && (
                  <Badge variant="outline" className="text-xs">
                    Severity: {selectedSeverity}
                  </Badge>
                )}
                {selectedRule !== 'ALL' && (
                  <Badge variant="outline" className="text-xs font-mono">
                    Rule: {selectedRule}
                  </Badge>
                )}
                {selectedField !== 'ALL' && (
                  <Badge variant="outline" className="text-xs font-mono">
                    Field: {selectedField}
                  </Badge>
                )}
                {searchTerm && (
                  <Badge variant="outline" className="text-xs">
                    Search: "{searchTerm}"
                  </Badge>
                )}
              </div>
              <button
                onClick={clearAllFilters}
                className="text-primary hover:underline font-medium text-xs cursor-pointer"
              >
                Reset filters
              </button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Issues Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto min-h-[300px]">
            <table className="w-full text-sm text-left" id="issues-table">
              <thead className="text-xs uppercase bg-muted/60 text-muted-foreground border-b select-none">
                <tr>
                  <th className="py-3 px-4 w-16">Row</th>
                  <th className="py-3 px-4 w-28">Rule ID</th>
                  <th className="py-3 px-4 w-24">Severity</th>
                  <th className="py-3 px-4 w-36">Field</th>
                  <th className="py-3 px-4 w-52">Student PII (Masked / Reveal)</th>
                  <th className="py-3 px-4">Validation Message & Remediation Guidance</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-muted-foreground">
                      Loading issues from validation engine...
                    </td>
                  </tr>
                ) : paginatedIssues.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-muted-foreground">
                      <div className="flex flex-col items-center justify-center space-y-1">
                        <Info className="h-6 w-6 text-muted-foreground" />
                        <span className="font-medium">No validation issues match your selected filters.</span>
                        <span className="text-xs">Try resetting or broadening your filter criteria.</span>
                      </div>
                    </td>
                  </tr>
                ) : (
                  paginatedIssues.map((issue, idx) => {
                    const ruleDef = RULE_CATALOG[issue.rule_id];

                    return (
                      <tr
                        key={`${issue.row}-${issue.rule_id}-${idx}`}
                        className="hover:bg-muted/30 transition-colors"
                        data-testid="issue-row"
                        data-severity={issue.severity}
                        data-rule={issue.rule_id}
                        data-field={issue.field}
                      >
                        <td className="py-3 px-4 font-mono text-xs text-muted-foreground font-semibold">
                          #{issue.row}
                        </td>
                        <td className="py-3 px-4">
                          {/* Rule ID with Interactive Rich Tooltip */}
                          <div className="relative inline-block">
                            <button
                              type="button"
                              onMouseEnter={() => setHoveredRule(issue.rule_id)}
                              onMouseLeave={() => setHoveredRule(null)}
                              onClick={() => setSelectedRule(issue.rule_id)}
                              className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-muted hover:bg-primary/20 hover:text-primary transition-colors flex items-center gap-1 cursor-pointer"
                              title={`Click to filter by ${issue.rule_id}`}
                            >
                              {issue.rule_id}
                              <HelpCircle className="h-3 w-3 text-muted-foreground" />
                            </button>

                            {/* Hover Tooltip from rule_catalog.yaml */}
                            {hoveredRule === issue.rule_id && ruleDef && (
                              <div className="absolute z-30 left-0 top-7 w-80 p-3 bg-popover text-popover-foreground border shadow-xl rounded-lg text-xs space-y-1.5 animate-fade-in pointer-events-none">
                                <div className="flex items-center justify-between border-b pb-1 font-bold">
                                  <span>{issue.rule_id}: {ruleDef.name || ruleDef.description}</span>
                                  <Badge variant={ruleDef.severity === 'ERROR' ? 'destructive' : 'warning'} className="text-[9px]">
                                    {ruleDef.severity}
                                  </Badge>
                                </div>
                                <p className="font-semibold text-foreground">{ruleDef.description}</p>
                                {ruleDef.paramsDescription && (
                                  <p className="text-[11px] text-muted-foreground font-mono bg-muted/40 p-1 rounded">
                                    {ruleDef.paramsDescription}
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
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
                        <td className="py-3 px-4">
                          {/* Gated PII Reveal Component */}
                          <PiiReveal
                            maskedValue={issue.value_masked}
                            unmaskedValue={getUnmaskedValueForIssue(issue)}
                            fieldType={
                              issue.field.includes('apaar')
                                ? 'apaar'
                                : issue.field.includes('mail')
                                ? 'email'
                                : issue.field.includes('mobile')
                                ? 'mobile'
                                : issue.field.includes('name')
                                ? 'name'
                                : 'general'
                            }
                            studentId={`std-row-${issue.row}`}
                          />
                        </td>
                        <td className="py-3 px-4 text-xs text-foreground max-w-md">
                          {issue.message}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t bg-muted/10 text-xs">
              <span className="text-muted-foreground">
                Showing{' '}
                <strong className="text-foreground">
                  {(currentPage - 1) * pageSize + 1}
                </strong>{' '}
                to{' '}
                <strong className="text-foreground">
                  {Math.min(currentPage * pageSize, totalItems)}
                </strong>{' '}
                of <strong className="text-foreground">{totalItems}</strong> entries
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="h-8 gap-1 text-xs"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  Previous
                </Button>
                <span className="font-medium px-2">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="h-8 gap-1 text-xs"
                >
                  Next
                  <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Fix & Resubmit Modal */}
      <FixResubmitModal
        isOpen={fixModalOpen}
        onClose={() => setFixModalOpen(false)}
        originalBatchId={currentReport.batch_id}
        originalReport={currentReport}
        onBatchUpdated={newReport => setCurrentReport(newReport)}
      />
    </div>
  );
};
