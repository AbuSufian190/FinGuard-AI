import { batchPredict } from "@/api/client";
import type { BatchPredictionResponse } from "@/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, ErrorState, RiskBadge, Spinner } from "@/components/ui/primitives";
import { InfoBanner, PageHeader, StatCard } from "@/components/ui/widgets";
import { formatPercent } from "@/lib/utils";
import { Download, FileCheck2, ShieldAlert, Table, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

const REQUIRED = [
  "step",
  "type",
  "amount",
  "oldbalanceOrg",
  "newbalanceOrig",
  "oldbalanceDest",
  "newbalanceDest",
];

export default function BatchDetection() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<BatchPredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function onUpload() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await batchPredict(file));
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  function downloadResults() {
    if (!result?.result_csv_base64) return;
    const blob = new Blob([atob(result.result_csv_base64)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "finguard_results.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <PageHeader
        title="Batch Fraud Detection"
        subtitle="Upload a CSV of transactions and score them all at once"
      />

      <InfoBanner>
        CSV must include columns: <code>{REQUIRED.join(", ")}</code>. Max 10 MB.
      </InfoBanner>

      <Card>
        <CardContent className="pt-6">
          <div
            className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed border-border p-10 text-center"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files?.[0];
              if (f) setFile(f);
            }}
          >
            <UploadCloud className="h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              {file ? (
                <span className="font-medium text-foreground">{file.name}</span>
              ) : (
                "Drag & drop a CSV here, or"
              )}
            </p>
            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => inputRef.current?.click()}>
                Choose file
              </Button>
              <Button onClick={onUpload} disabled={!file || loading}>
                {loading ? "Scoring…" : "Run Detection"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading && <Spinner label="Scoring transactions…" />}
      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard
              label="Rows Scored"
              value={result.summary.total_rows.toLocaleString()}
              icon={Table}
            />
            <StatCard
              label="Flagged Fraud"
              value={result.summary.flagged_fraud.toLocaleString()}
              icon={ShieldAlert}
              tone="danger"
            />
            <StatCard
              label="Fraud Rate"
              value={formatPercent(result.summary.fraud_rate, 2)}
              icon={FileCheck2}
              tone="warning"
            />
            <StatCard
              label="High Risk"
              value={result.summary.high_risk.toLocaleString()}
              icon={ShieldAlert}
              tone="danger"
            />
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Results (first 100 rows)</CardTitle>
                <Button variant="outline" onClick={downloadResults}>
                  <Download className="h-4 w-4" /> Download CSV
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="max-h-[420px] overflow-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-card">
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="pb-2 pr-4">Row</th>
                      <th className="pb-2 pr-4">Probability</th>
                      <th className="pb-2 pr-4">Flagged</th>
                      <th className="pb-2">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.results.slice(0, 100).map((r) => (
                      <tr key={r.row} className="border-b border-border/60">
                        <td className="py-2 pr-4 font-mono text-xs">{r.row}</td>
                        <td className="py-2 pr-4">
                          {formatPercent(r.fraud_probability, 1)}
                        </td>
                        <td className="py-2 pr-4">{r.is_fraud ? "Yes" : "No"}</td>
                        <td className="py-2">
                          <RiskBadge level={r.risk_level} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
