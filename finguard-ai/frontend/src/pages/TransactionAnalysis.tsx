import { predict } from "@/api/client";
import type { PredictionResponse, TransactionInput, TransactionType } from "@/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Button,
  ErrorState,
  Field,
  Input,
  RiskBadge,
  Select,
  Spinner,
} from "@/components/ui/primitives";
import { PageHeader } from "@/components/ui/widgets";
import { formatPercent } from "@/lib/utils";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { useState } from "react";

const TYPES: TransactionType[] = [
  "PAYMENT",
  "TRANSFER",
  "CASH_OUT",
  "CASH_IN",
  "DEBIT",
];

const DEFAULTS: TransactionInput = {
  step: 100,
  type: "TRANSFER",
  amount: 181000,
  oldbalanceOrg: 181000,
  newbalanceOrig: 0,
  oldbalanceDest: 0,
  newbalanceDest: 0,
};

const NUMERIC_FIELDS: { key: keyof TransactionInput; label: string }[] = [
  { key: "amount", label: "Amount" },
  { key: "oldbalanceOrg", label: "Sender balance (before)" },
  { key: "newbalanceOrig", label: "Sender balance (after)" },
  { key: "oldbalanceDest", label: "Recipient balance (before)" },
  { key: "newbalanceDest", label: "Recipient balance (after)" },
  { key: "step", label: "Step (hour)" },
];

export default function TransactionAnalysis() {
  const [form, setForm] = useState<TransactionInput>(DEFAULTS);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof TransactionInput>(key: K, value: string) {
    setForm((f) => ({
      ...f,
      [key]: key === "type" ? (value as TransactionType) : Number(value),
    }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await predict(form));
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Prediction failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Transaction Analysis"
        subtitle="Score a single transaction and see why it was flagged"
      />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Transaction Details</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              <Field label="Transaction type">
                <Select
                  value={form.type}
                  onChange={(e) => update("type", e.target.value)}
                >
                  {TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </Field>
              <div className="grid grid-cols-2 gap-3">
                {NUMERIC_FIELDS.map(({ key, label }) => (
                  <Field key={key} label={label}>
                    <Input
                      type="number"
                      min={0}
                      step="any"
                      value={form[key] as number}
                      onChange={(e) => update(key, e.target.value)}
                      required
                    />
                  </Field>
                ))}
              </div>
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? "Analyzing…" : "Analyze Transaction"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Prediction Result</CardTitle>
          </CardHeader>
          <CardContent>
            {loading && <Spinner label="Scoring…" />}
            {error && <ErrorState message={error} />}
            {!loading && !error && !result && (
              <p className="py-10 text-center text-sm text-muted-foreground">
                Submit a transaction to see the fraud assessment.
              </p>
            )}
            {result && (
              <div className="space-y-5">
                <div className="flex items-center gap-3">
                  {result.is_fraud ? (
                    <AlertCircle className="h-8 w-8 text-danger" />
                  ) : (
                    <CheckCircle2 className="h-8 w-8 text-success" />
                  )}
                  <div>
                    <p className="text-lg font-bold">
                      {result.is_fraud
                        ? "Flagged as Fraudulent"
                        : "Likely Legitimate"}
                    </p>
                    <RiskBadge level={result.risk_level} />
                  </div>
                </div>

                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="text-muted-foreground">Fraud probability</span>
                    <span className="font-semibold">
                      {formatPercent(result.fraud_probability, 2)}
                    </span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className={
                        "h-full rounded-full " +
                        (result.is_fraud ? "bg-danger" : "bg-success")
                      }
                      style={{
                        width: `${Math.min(result.fraud_probability * 100, 100)}%`,
                      }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Decision threshold: {formatPercent(result.threshold, 1)} ·{" "}
                    {result.model_name} {result.model_version}
                  </p>
                </div>

                {result.explanation && (
                  <div>
                    <p className="mb-2 text-sm font-semibold">
                      Why? Top contributing factors
                      <span className="ml-1 text-xs font-normal text-muted-foreground">
                        ({result.explanation.method})
                      </span>
                    </p>
                    <ul className="space-y-1.5">
                      {result.explanation.top_features.slice(0, 6).map((f) => (
                        <li
                          key={f.feature}
                          className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-1.5 text-sm"
                        >
                          <span className="font-mono text-xs">{f.feature}</span>
                          <span
                            className={
                              f.direction === "increases_risk"
                                ? "text-danger"
                                : "text-success"
                            }
                          >
                            {f.direction === "increases_risk" ? "↑ risk" : "↓ risk"}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
