import { getModelInfo } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Spinner } from "@/components/ui/primitives";
import { InfoBanner, PageHeader } from "@/components/ui/widgets";
import { useFetch } from "@/hooks/useFetch";
import { formatPercent } from "@/lib/utils";

export default function ModelInformation() {
  const { data, loading, error } = useFetch(getModelInfo, []);
  if (loading) return <Spinner />;
  if (error) return <ErrorState message={error} />;
  if (!data) return <EmptyState message="No model info." />;

  const rows: [string, string][] = [
    ["Model", data.model_name],
    ["Version", data.model_version],
    ["Selection metric", data.selection_metric.toUpperCase()],
    ["Decision threshold", formatPercent(data.decision_threshold, 1)],
    ["Trained at", data.trained_at ? new Date(data.trained_at).toLocaleString() : "—"],
    ["Data source", data.data_source || "—"],
    ["Status", data.loaded ? "Loaded" : "Not loaded"],
  ];

  return (
    <div>
      <PageHeader
        title="Model Information"
        subtitle="Details of the currently active fraud-detection model"
      />
      {data.synthetic_data && (
        <InfoBanner>
          This model was trained on <strong>synthetic development data</strong>. Retrain
          on real PaySim for production-representative behaviour.
        </InfoBanner>
      )}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Active Model</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="divide-y divide-border">
              {rows.map(([k, v]) => (
                <div key={k} className="flex justify-between py-2.5 text-sm">
                  <dt className="text-muted-foreground">{k}</dt>
                  <dd className="font-medium">{v}</dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Features ({data.features.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {data.features.map((f) => (
                <span
                  key={f}
                  className="rounded-md bg-muted px-2.5 py-1 font-mono text-xs"
                >
                  {f}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
