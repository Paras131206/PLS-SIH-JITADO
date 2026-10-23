import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
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
} from 'lucide-react';
import { Issue, RuleSeverity } from '../../api/types';
import { RULE_CATALOG } from '../../lib/ruleCatalog';
import { apiFetch } from '../../api/client';

export const IssuesView: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedRule, setSelectedRule] = useState<string>('ALL');
  const [selectedField, setSelectedField] = useState<string>('ALL');
  const [hoveredRule, setHoveredRule] = useState<string | null>(null);

  // Pagination / virtualised window state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading } = useQuery<{ total: number; items: Issue[] }>({
    queryKey: ['issues', selectedSeverity, selectedRule, selectedField, searchTerm],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedSeverity !== 'ALL') params.append('severity', selectedSeverity);
      if (selectedRule !== 'ALL') params.append('rule_id', selectedRule);
      if (searchTerm) params.append('search', searchTerm);

      const res = await apiFetch<{ total: number; items: Issue[] }>(
        `/batches/batch-2026-dtu-001/issues?${params.toString()}`
      );
      return res;
    },
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
          <p className="text-sm text-muted-foreground">
            Batch: <span className="font-mono font-medium">batch-2026-dtu-001</span> • Verified against contracts/rule_catalog.yaml
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            id="export-csv-btn"
            onClick={exportIssuesCsv}
            disabled={filteredIssues.length === 0}
            className="flex items-center gap-2 text-xs"
          >
            <Download className="h-4 w-4 text-primary" />
            Export Issues CSV ({filteredIssues.length})
          </Button>
        </div>
      </div>

      {/* Filter Toolbar (Rule ID, Severity, Field, Search by Masked APAAR) */}
      <Card className="p-4 shadow-sm">
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {/* Search by Masked APAAR */}
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                id="search-apaar-input"
                placeholder="Search masked APAAR (e.g. 1234****9012)..."
                value={searchTerm}
                onChange={e => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-9 pr-3 py-2 text-xs bg-background border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>

            {/* Severity Filter */}
            <div>
              <select
                id="severity-filter"
                aria-label="Filter by Severity"
                value={selectedSeverity}
                onChange={e => {
                  setSelectedSeverity(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full text-xs bg-background border rounded-md px-3 py-2 font-medium focus:outline-none"
              >
                <option value="ALL">All Severities (ERROR + WARN)</option>
                <option value="ERROR">ERROR Only (Blocking)</option>
                <option value="WARN">WARN Only (Non-blocking)</option>
              </select>
            </div>

            {/* Rule Filter */}
            <div>
              <select
                id="rule-filter"
                aria-label="Filter by Rule ID"
                value={selectedRule}
                onChange={e => {
                  setSelectedRule(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full text-xs bg-background border rounded-md px-3 py-2 font-medium focus:outline-none"
              >
                <option value="ALL">All Rule IDs (V001–V020)</option>
                {Object.keys(RULE_CATALOG).map(rid => (
                  <option key={rid} value={rid}>
                    {rid} — {RULE_CATALOG[rid].description.slice(0, 36)}...
                  </option>
                ))}
              </select>
            </div>

            {/* Field Filter */}
            <div>
              <select
                id="field-filter"
                aria-label="Filter by Field"
                value={selectedField}
                onChange={e => {
                  setSelectedField(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full text-xs bg-background border rounded-md px-3 py-2 font-medium focus:outline-none"
              >
                <option value="ALL">All Fields</option>
                {allFields.map(field => (
                  <option key={field} value={field}>
                    Field: {field}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Active Filter Chips / Reset */}
          {(searchTerm || selectedSeverity !== 'ALL' || selectedRule !== 'ALL' || selectedField !== 'ALL') && (
            <div className="flex items-center justify-between text-xs pt-1 border-t">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-muted-foreground font-medium">Active filters:</span>
                {selectedSeverity !== 'ALL' && (
                  <Badge variant="outline" className="text-[10px]">
                    Severity: {selectedSeverity}
                  </Badge>
                )}
                {selectedRule !== 'ALL' && (
                  <Badge variant="outline" className="text-[10px]">
                    Rule: {selectedRule}
                  </Badge>
                )}
                {selectedField !== 'ALL' && (
                  <Badge variant="outline" className="text-[10px]">
                    Field: {selectedField}
                  </Badge>
                )}
                {searchTerm && (
                  <Badge variant="outline" className="text-[10px]">
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
        </div>
      </Card>

      {/* Virtualised / High-Performance Issues Table */}
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
                  <th className="py-3 px-4 w-40">Masked Value</th>
                  <th className="py-3 px-4">Validation Message & Catalog Check</th>
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
                              className="font-mono font-bold text-xs bg-secondary hover:bg-secondary/80 px-2 py-0.5 rounded cursor-pointer inline-flex items-center gap-1 border border-border"
                              title={ruleDef?.description || issue.rule_id}
                              aria-label={`Rule details for ${issue.rule_id}`}
                            >
                              <span>{issue.rule_id}</span>
                              <HelpCircle className="h-3 w-3 text-muted-foreground" />
                            </button>

                            {/* Floating Rich Tooltip Box */}
                            {hoveredRule === issue.rule_id && ruleDef && (
                              <div className="absolute left-0 top-full mt-1 z-50 w-72 p-3 bg-popover text-popover-foreground border rounded-lg shadow-xl text-xs space-y-1.5 animate-in fade-in-50 zoom-in-95 pointer-events-none">
                                <div className="flex items-center justify-between font-bold border-b pb-1">
                                  <span className="text-primary font-mono">{ruleDef.id}</span>
                                  <Badge
                                    variant={ruleDef.severity === 'ERROR' ? 'destructive' : 'warning'}
                                    className="text-[10px]"
                                  >
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
                        <td className="py-3 px-4 font-mono text-xs text-muted-foreground">
                          {issue.value_masked}
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
                  {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, totalItems)}
                </strong>{' '}
                of <strong className="text-foreground">{totalItems}</strong> issues
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="h-8 w-8 p-0"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="px-2 font-mono font-medium">
                  {currentPage} / {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="h-8 w-8 p-0"
                  aria-label="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
