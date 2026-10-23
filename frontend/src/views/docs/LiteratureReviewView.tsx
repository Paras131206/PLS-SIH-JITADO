import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { BookOpen, ExternalLink, ShieldCheck, Database, GitMerge, FileKey } from 'lucide-react';

export const LiteratureReviewView: React.FC = () => {
  const sources = [
    {
      id: 'S01',
      name: 'neuralsorcerer/student-performance (HF CC0)',
      focus: 'Demographics & distributions (26 cols, ~100M rows)',
      use: 'Value ranges, consistency rules, ~50k synthetic sample baseline',
      status: 'Verified via HF Viewer',
    },
    {
      id: 'S02',
      name: 'drsanjayagal/UniversityIntake-MLDataset (CC BY 4.0)',
      focus: 'Intake-side limits, MCAR/MAR gaps (28 cols)',
      use: 'Intake field modelling, missing-value stress fixtures, category mapping',
      status: 'Generator script validated',
    },
    {
      id: 'S03',
      name: 'drsanjayagal/SynEdu-HEDL (Zenodo 10.5281/zenodo.18884938)',
      focus: 'Multi-table referential integrity in higher ed (20k students)',
      use: 'Duplicate-enrolment baseline model (student_id, year, program)',
      status: 'Cite Zenodo copy (85 vs 60 cols note)',
    },
    {
      id: 'S04',
      name: 'Schelter et al., Deequ Data Quality (VLDB 2018)',
      focus: 'Automated large-scale constraint verification',
      use: 'Vectorised Pandera constraints (V001–V020), metric history, z-score',
      status: 'Deequ paradigm implemented',
    },
    {
      id: 'S05',
      name: 'Christen, Record Linkage Indexing Survey (IEEE TKDE 2012)',
      focus: 'Blocking & candidate-pair indexing algorithms',
      use: '12-digit APAAR exact blocking + phonetic candidate pruning',
      status: 'Abstract & taxonomy analyzed',
    },
    {
      id: 'S06',
      name: 'Vatsalan, Christen, Verykios, PPRL Taxonomy (2013)',
      focus: 'Privacy-Preserving Record Linkage across autonomous silos',
      use: 'Cryptographic Bloom-filter linkage across regional bodies roadmap',
      status: 'Taxonomy reviewed',
    },
    {
      id: 'S07',
      name: 'Berrios Moya et al., ZKP Academic Records (Sensors 2025)',
      focus: 'Decentralized identity & selective disclosure proofs',
      use: 'Selective disclosure motivation; contrast vs zero-gas SD-JWT',
      status: 'Abstract reviewed',
    },
    {
      id: 'S08',
      name: 'Rustemi et al., SLR on Blockchain Certificates (IEEE Access 2023)',
      focus: 'Systematic literature review of 34 verification systems',
      use: 'Gap justification: eliminate prohibitive gas fees & on-chain PII',
      status: 'Confirmed IEEE doc 10163764 match',
    },
    {
      id: 'S09',
      name: 'Springer Journal s10639-024-12493-6',
      focus: 'Credential distribution, issuance & auditability',
      use: 'Issuance pipelines, verifier trust, institutional auditability',
      status: 'Secondary sources reviewed',
    },
    {
      id: 'S10',
      name: 'MoE / AICTE Official APAAR Guidelines',
      focus: '12-digit lifelong student ID, DigiLocker/ABC linkage',
      use: 'Rule V002 format, Rule V018 consent ledger, mock registry adapter',
      status: 'apaar.education.gov.in referenced',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div className="border-b pb-4">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase text-gov-gold dark:text-amber-400">
          <BookOpen className="h-4 w-4" />
          <span>Research Foundation & Literature Review</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground mt-1">
          APAAR-SDMS Academic Grounding & Literature Review (§9)
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Theoretical taxonomy, empirical datasets, and algorithmic trade-offs establishing our system architecture.
        </p>
      </div>

      {/* Synthesis Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 border-l-4 border-l-gov-navy dark:border-l-blue-500">
          <div className="flex items-center gap-2 font-semibold text-sm">
            <Database className="h-4 w-4 text-primary" />
            <span>Deequ-Style Validation</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Replaces slow row-wise loops with vectorised Pandas/Pandera checks across 20 canonical rules (V001–V020).
          </p>
        </Card>

        <Card className="p-4 border-l-4 border-l-emerald-500">
          <div className="flex items-center gap-2 font-semibold text-sm">
            <GitMerge className="h-4 w-4 text-emerald-600" />
            <span>Fellegi-Sunter Dedup</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Exact APAAR blocking followed by Splink + Indic Soundex for cross-institution dual-enrolment detection.
          </p>
        </Card>

        <Card className="p-4 border-l-4 border-l-purple-500">
          <div className="flex items-center gap-2 font-semibold text-sm">
            <FileKey className="h-4 w-4 text-purple-600" />
            <span>Zero-Gas SD-JWT</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Selective disclosure without blockchain gas costs or slow block latency. Verification runs in &lt;50ms.
          </p>
        </Card>
      </div>

      {/* Table from agents.md §9 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Literature Sources & Project Mapping Table</CardTitle>
          <CardDescription>
            Direct derivation of algorithmic design from peer-reviewed literature and open datasets
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="uppercase bg-muted/60 text-muted-foreground border-b font-semibold">
                <tr>
                  <th className="py-3 px-4">#</th>
                  <th className="py-3 px-4">Source Reference</th>
                  <th className="py-3 px-4">Focus Area</th>
                  <th className="py-3 px-4">Use in APAAR-SDMS</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {sources.map(s => (
                  <tr key={s.id} className="hover:bg-muted/30">
                    <td className="py-3 px-4 font-mono font-bold text-muted-foreground">{s.id}</td>
                    <td className="py-3 px-4 font-semibold text-foreground max-w-[200px]">{s.name}</td>
                    <td className="py-3 px-4 text-muted-foreground">{s.focus}</td>
                    <td className="py-3 px-4 text-foreground font-medium">{s.use}</td>
                    <td className="py-3 px-4 text-xs font-mono text-muted-foreground">{s.status}</td>
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
