import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { GitCompare, CheckCircle2, XCircle, AlertTriangle, ArrowRight, ShieldAlert } from 'lucide-react';
import { DuplicateCluster } from '../../api/types';

export const DuplicatesView: React.FC = () => {
  const [resolvedClusters, setResolvedClusters] = useState<Record<string, string>>({});

  const { data: clusters } = useQuery<DuplicateCluster[]>({
    queryKey: ['duplicates'],
    queryFn: async () => {
      const res = await fetch('/v1/duplicates');
      return res.json();
    },
  });

  const handleResolve = async (clusterId: string, action: 'CONFIRM' | 'DISMISS') => {
    await fetch(`/v1/duplicates/${clusterId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        note: action === 'CONFIRM' ? 'Confirmed as cross-institution duplicate' : 'Dismissed as false positive',
      }),
    });
    setResolvedClusters(prev => ({ ...prev, [clusterId]: action }));
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Duplicate Enrolment Review Queue (Rule V009–V011)
          </h2>
          <p className="text-sm text-muted-foreground">
            Probabilistic Record Linkage (Fellegi-Sunter + Splink + Indic Soundex) matching candidate pairs
          </p>
        </div>
        <Badge variant="warning" className="text-xs">
          Human-in-the-Loop Review
        </Badge>
      </div>

      {/* Duplicate Cluster Cards */}
      <div className="space-y-6">
        {clusters?.map(cluster => {
          const isResolved = !!resolvedClusters[cluster.cluster_id];
          const resolution = resolvedClusters[cluster.cluster_id];

          return (
            <Card key={cluster.cluster_id} className="border-l-4 border-l-amber-500 overflow-hidden">
              <CardHeader className="bg-muted/20 pb-4">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-muted-foreground">
                      Cluster {cluster.cluster_id}
                    </span>
                    <Badge variant={cluster.scope === 'CROSS_INSTITUTION' ? 'destructive' : 'secondary'}>
                      {cluster.scope === 'CROSS_INSTITUTION' ? 'Cross-Institution Collision' : 'Intra-Batch Collision'}
                    </Badge>
                    <Badge variant="outline" className="font-mono text-xs font-bold">
                      Match Confidence: {(cluster.score * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  {isResolved && (
                    <Badge variant={resolution === 'CONFIRM' ? 'destructive' : 'success'}>
                      Status: {resolution}ED
                    </Badge>
                  )}
                </div>
                <CardDescription className="mt-1">
                  Triggered checks: {cluster.match_reasons?.join(' • ')}
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-4 space-y-4">
                {/* Side-by-Side Comparison Matrix */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Entity A */}
                  <div className="rounded-lg border p-4 bg-background space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase border-b pb-1">
                      <span>Record A (Primary Submitter)</span>
                      <span className="font-mono text-gov-navy dark:text-blue-400">
                        DTU (AICTE: 1-10293847)
                      </span>
                    </div>
                    <div className="text-xs space-y-1 font-mono">
                      <div><span className="text-muted-foreground">APAAR ID:</span> <strong>{cluster.apaar_ids[0]}</strong></div>
                      <div><span className="text-muted-foreground">Candidate:</span> <strong>Karthik S. Raman</strong></div>
                      <div><span className="text-muted-foreground">DOB:</span> 2005-04-12</div>
                      <div><span className="text-muted-foreground">Program:</span> CSE-UG-01 (Regular Seat)</div>
                    </div>
                  </div>

                  {/* Entity B */}
                  <div className="rounded-lg border p-4 bg-background space-y-2">
                    <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase border-b pb-1">
                      <span>Record B (Conflicting Entity)</span>
                      <span className="font-mono text-amber-600 dark:text-amber-400">
                        COEP Pune (AICTE: 1-92837465)
                      </span>
                    </div>
                    <div className="text-xs space-y-1 font-mono">
                      <div><span className="text-muted-foreground">APAAR ID:</span> <strong>{cluster.apaar_ids[0] || '7654****0987'}</strong></div>
                      <div><span className="text-muted-foreground">Candidate:</span> <strong>Karthik Subramanian Raman</strong></div>
                      <div><span className="text-muted-foreground">DOB:</span> 2005-04-12</div>
                      <div><span className="text-muted-foreground">Program:</span> ECE-UG-01 (Regular Seat)</div>
                    </div>
                  </div>
                </div>

                {/* Resolution Action Toolbar */}
                {!isResolved ? (
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t">
                    <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                      <ShieldAlert className="h-4 w-4 text-amber-500" />
                      <span>Action writes a tamper-evident entry to the AICTE audit chain</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResolve(cluster.cluster_id, 'DISMISS')}
                        className="text-xs"
                      >
                        <XCircle className="h-3.5 w-3.5 mr-1" />
                        Dismiss (Different Students)
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleResolve(cluster.cluster_id, 'CONFIRM')}
                        className="text-xs"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                        Confirm Dual-Enrolment (Block)
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-secondary/50 rounded text-xs text-muted-foreground">
                    Action recorded in audit log. Participating institutions notified via webhook.
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
