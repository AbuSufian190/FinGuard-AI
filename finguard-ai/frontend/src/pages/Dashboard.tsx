import { getDashboard } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  EmptyState,
  ErrorState,
  RiskBadge,
  Spinner,
} from "@/components/ui/primitives";
import { CHART_COLORS, PageHeader, StatCard } from "@/components/ui/widgets";
import { useFetch } from "@/hooks/useFetch";
import { formatCurrency, formatDate, formatNumber, formatPercent } from "@/lib/utils";
import { AlertTriangle, Banknote, ShieldAlert, TrendingUp } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const RISK_COLOR: Record<string, string> = {
  LOW: CHART_COLORS.success,
  MEDIUM: CHART_COLORS.warning,
  HIGH: CHART_COLORS.danger,
};

export default function Dashboard() {
  const { data, loading, error } = useFetch(getDashboard, []);

  if (loading) return <Spinner label="Loading analytics…" />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState message="No data yet." />;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Overview of analyzed transactions and detected fraud"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Transactions Analyzed"
          value={formatNumber(data.total_transactions)}
          icon={TrendingUp}
        />
        <StatCard
          label="Fraud Detected"
          value={formatNumber(data.fraudulent_detected)}
          icon={ShieldAlert}
          tone="danger"
        />
        <StatCard
          label="Fraud Detection Rate"
          value={formatPercent(data.fraud_detection_rate, 2)}
          icon={AlertTriangle}
          tone="warning"
        />
        <StatCard
          label="Avg Transaction"
          value={formatCurrency(data.average_amount)}
          icon={Banknote}
          tone="success"
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Transaction Trend (14 days)</CardTitle>
          </CardHeader>
          <CardContent>
            {data.trend.length === 0 ? (
              <EmptyState message="No recent transactions." />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={data.trend}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis dataKey="date" fontSize={11} tickMargin={8} />
                  <YAxis fontSize={11} allowDecimals={false} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="total"
                    name="Total"
                    stroke={CHART_COLORS.primary}
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="fraud"
                    name="Fraud"
                    stroke={CHART_COLORS.danger}
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {data.fraud_distribution.length === 0 ? (
              <EmptyState message="No predictions yet." />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={data.fraud_distribution}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis dataKey="risk_level" fontSize={11} />
                  <YAxis fontSize={11} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" name="Count" radius={[4, 4, 0, 0]}>
                    {data.fraud_distribution.map((d) => (
                      <Cell
                        key={d.risk_level}
                        fill={RISK_COLOR[d.risk_level] || CHART_COLORS.muted}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Recent Suspicious Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          {data.recent_suspicious.length === 0 ? (
            <EmptyState message="No suspicious transactions detected yet." />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-muted-foreground">
                    <th className="pb-2 pr-4">ID</th>
                    <th className="pb-2 pr-4">Time</th>
                    <th className="pb-2 pr-4">Type</th>
                    <th className="pb-2 pr-4">Amount</th>
                    <th className="pb-2 pr-4">Probability</th>
                    <th className="pb-2">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_suspicious.map((t) => (
                    <tr key={t.id} className="border-b border-border/60">
                      <td className="py-2 pr-4 font-mono text-xs">#{t.id}</td>
                      <td className="py-2 pr-4">{formatDate(t.created_at)}</td>
                      <td className="py-2 pr-4">{t.type}</td>
                      <td className="py-2 pr-4">{formatCurrency(t.amount)}</td>
                      <td className="py-2 pr-4">
                        {formatPercent(t.fraud_probability, 1)}
                      </td>
                      <td className="py-2">
                        <RiskBadge level={t.risk_level} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
