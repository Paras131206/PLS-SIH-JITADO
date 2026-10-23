import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Activity, AlertTriangle, CheckCircle, TrendingUp, ShieldAlert, ArrowUpRight } from 'lucide-react';
import { AnomalyItem } from '../../api/types';

export const AnomaliesView: React.FC = () => {
  const [acknowledged, setAcknowledged] = useState<Record<string, boolean>>({});

  const { data: anomalies } = useQuery<AnomalyItem[]>({
    queryKey: ['anomalies'],
    queryFn: async () => {
      const res = await fetch('/v1/anomalies');
      return res.json();
    },
  });

  const handleAcknowledge = async (id: string) => {
    await fetch(`/v1/anomalies/${id}/acknowledge`, { method: 'POST' });
    setAcknowledged(prev => ({ ...prev, [id]: true }));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Admissions Anomaly & Drift Engine (Rule V020)
          </h2>
          <p className="text-sm text-muted-foreground">
            Isolation Forest & Deequ-style stateful metric tracking over multi-year institutional history
          </p>
        </div>
        <Badge variant="destructive" className="gap-1 text-xs">
          <Activity className="h-3 w-3 animate-pulse" />
          Real-Time Drift Feed
        </Badge>
      </div>

      <div className="space-y-4">
        {anomalies?.map(anom => {
          const isAck = acknowledged[anom.id];

          return (
            <Card key={anom.id} className="border-l-4 border-l-destructive">
              <CardHeader className="pb-3">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-muted-foreground">
                      {anom.id}
                    </span>
                    <Badge variant="destructive" className="font-mono text-xs">
                      Z-Score: +{anom.z.toFixed(1)}σ
                    </Badge>
                    <Badge variant="outline" className="font-mono text-xs">
                      Metric: {anom.metric}
                    </Badge>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Detected: {new Date(anom.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <CardTitle className="text-base text-foreground mt-2">
                  {anom.institution_name} ({anom.institution_aicte_id})
                </CardTitle>
                <CardDescription className="text-foreground font-medium">
                  {anom.reason}
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-0 space-y-4">
                {/* Metric Delta Visuals */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3 bg-muted/30 rounded-lg text-xs font-mono">
                  <div>
                    <span className="text-muted-foreground block">Current Upload Value:</span>
                    <span className="text-lg font-bold text-destructive">
                      {(anom.value * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">3-Year Institutional Baseline:</span>
                    <span className="text-lg font-bold text-foreground">
                      {(anom.baseline * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block">Deviation Sigma:</span>
                    <span className="text-lg font-bold text-destructive">
                      +{anom.z}σ (&gt; 3.0 threshold)
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-between pt-2">
                  <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                    <ShieldAlert className="h-4 w-4 text-destructive" />
                    <span>Flagged by Scikit-Learn IsolationForest outlier model</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {isAck ? (
                      <Badge variant="success" className="gap-1 text-xs">
                        <CheckCircle className="h-3.5 w-3.5" />
                        Acknowledged
                      </Badge>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleAcknowledge(anom.id)}
                        className="text-xs"
                      >
                        Acknowledge & Mark Inspected
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
