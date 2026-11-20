import { getModelPerformance } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Spinner } from "@/components/ui/primitives";
import { CHART_COLORS, InfoBanner, PageHeader } from "@/components/ui/widgets";
import { useFetch } from "@/hooks/useFetch";
import { cn, formatPercent } from "@/lib/utils";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const METRIC_KEYS = ["pr_auc", "roc_auc", "f1", "precision", "recall"] as const;

export default function ModelPerformance() {
  const { data, loading, error } = useFetch(getModelPerformance, []);

  if (loading) return <Spinner label="Loading evaluation…" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState message="No evaluation report." />;

  const modelNames = Object.keys(data.models);
  const selected = data.selected_model;
  const cm = data.models[selected].test.confusion_matrix;

  const roc = data.test_roc_curve.fpr.map((fpr, i) => ({
    fpr,
    tpr: data.test_roc_curve.tpr[i],
  }));
  const pr = data.test_pr_curve.recall.map((recall, i) => ({
    recall,
    precision: data.test_pr_curve.precision[i],
  }));

  return (
    <div>
      <PageHeader
        title="Model Performance"
        subtitle={`Best model: ${selected} · selected by ${data.selection_metric.toUpperCase()}`}
      />

      {data.synthetic && (
        <InfoBanner>
          ⚠️ These metrics were computed on <strong>synthetic development data</strong>,
          not the real PaySim dataset. Train on real PaySim for benchmark numbers.
        </InfoBanner>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Model Comparison (test split)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="pb-2 pr-4">Model</th>
                  {METRIC_KEYS.map((m) => (
                    <th key={m} className="pb-2 pr-4 uppercase">
                      {m.replace("_", "-")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {modelNames.map((name) => (
                  <tr
                    key={name}
                    className={cn(
                      "border-b border-border/60",
                      name === selected && "bg-primary/5 font-medium"
                    )}
                  >
                    <td className="py-2 pr-4">
                      {name}
                      {name === selected && (
                        <span className="ml-2 rounded bg-primary/15 px-1.5 py-0.5 text-xs text-primary">
                          selected
                        </span>
                      )}
                    </td>
                    {METRIC_KEYS.map((m) => (
                      <td key={m} className="py-2 pr-4">
                        {formatPercent(data.models[name].test[m], 1)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>ROC Curve (selected)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={roc}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis
                  dataKey="fpr"
                  type="number"
                  domain={[0, 1]}
                  fontSize={11}
                  tickFormatter={(v) => v.toFixed(1)}
                />
                <YAxis domain={[0, 1]} fontSize={11} tickFormatter={(v) => v.toFixed(1)} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="tpr"
                  stroke={CHART_COLORS.primary}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-center text-xs text-muted-foreground">
              ROC-AUC: {formatPercent(data.models[selected].test.roc_auc, 2)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Precision–Recall (selected)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={pr}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis
                  dataKey="recall"
                  type="number"
                  domain={[0, 1]}
                  fontSize={11}
                  tickFormatter={(v) => v.toFixed(1)}
                />
                <YAxis domain={[0, 1]} fontSize={11} tickFormatter={(v) => v.toFixed(1)} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="precision"
                  stroke={CHART_COLORS.success}
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-center text-xs text-muted-foreground">
              PR-AUC: {formatPercent(data.models[selected].test.pr_auc, 2)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Confusion Matrix (selected)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2 text-center">
              <Cell label="True Negative" value={cm.tn} tone="success" />
              <Cell label="False Positive" value={cm.fp} tone="warning" />
              <Cell label="False Negative" value={cm.fn} tone="danger" />
              <Cell label="True Positive" value={cm.tp} tone="success" />
            </div>
            <p className="mt-3 text-center text-xs text-muted-foreground">
              At decision threshold {formatPercent(data.decision_threshold, 1)}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Cell({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "warning" | "danger";
}) {
  const tones = {
    success: "bg-success/10 text-success",
    warning: "bg-warning/10 text-warning",
    danger: "bg-danger/10 text-danger",
  };
  return (
    <div className={cn("rounded-lg p-4", tones[tone])}>
      <p className="text-2xl font-bold">{value.toLocaleString()}</p>
      <p className="text-xs">{label}</p>
    </div>
  );
}
