import { getHistory, type HistoryParams } from "@/api/client";
import { Card, CardContent } from "@/components/ui/card";
import {
  Button,
  EmptyState,
  ErrorState,
  Input,
  RiskBadge,
  Select,
  Spinner,
} from "@/components/ui/primitives";
import { PageHeader } from "@/components/ui/widgets";
import { useFetch } from "@/hooks/useFetch";
import { formatCurrency, formatDate, formatPercent } from "@/lib/utils";
import { useState } from "react";

export default function History() {
  const [params, setParams] = useState<HistoryParams>({ page: 1, page_size: 20 });
  const [searchInput, setSearchInput] = useState("");
  const { data, loading, error } = useFetch(() => getHistory(params), [params]);

  function setFilter(patch: Partial<HistoryParams>) {
    setParams((p) => ({ ...p, ...patch, page: 1 }));
  }

  return (
    <div>
      <PageHeader
        title="Prediction History"
        subtitle="Search, filter and page through stored predictions"
      />

      <Card className="mb-4">
        <CardContent className="pt-5">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setFilter({ search: searchInput });
              }}
            >
              <Input
                placeholder="Search by ID or amount…"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </form>
            <Select
              value={params.risk_level || ""}
              onChange={(e) => setFilter({ risk_level: e.target.value || undefined })}
            >
              <option value="">All risk levels</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </Select>
            <Select
              value={params.type || ""}
              onChange={(e) => setFilter({ type: e.target.value || undefined })}
            >
              <option value="">All types</option>
              {["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
            <Select
              value={params.is_fraud === undefined ? "" : String(params.is_fraud)}
              onChange={(e) =>
                setFilter({
                  is_fraud: e.target.value === "" ? undefined : e.target.value === "true",
                })
              }
            >
              <option value="">All outcomes</option>
              <option value="true">Flagged fraud</option>
              <option value="false">Legitimate</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5">
          {loading && <Spinner />}
          {error && <ErrorState message={error} />}
          {data && data.items.length === 0 && (
            <EmptyState message="No predictions match your filters." />
          )}
          {data && data.items.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="pb-2 pr-4">ID</th>
                      <th className="pb-2 pr-4">Time</th>
                      <th className="pb-2 pr-4">Type</th>
                      <th className="pb-2 pr-4">Amount</th>
                      <th className="pb-2 pr-4">Probability</th>
                      <th className="pb-2 pr-4">Source</th>
                      <th className="pb-2">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((t) => (
                      <tr key={t.id} className="border-b border-border/60">
                        <td className="py-2 pr-4 font-mono text-xs">#{t.id}</td>
                        <td className="py-2 pr-4">{formatDate(t.created_at)}</td>
                        <td className="py-2 pr-4">{t.type}</td>
                        <td className="py-2 pr-4">{formatCurrency(t.amount)}</td>
                        <td className="py-2 pr-4">
                          {formatPercent(t.fraud_probability, 1)}
                        </td>
                        <td className="py-2 pr-4 text-xs text-muted-foreground">
                          {t.source}
                        </td>
                        <td className="py-2">
                          <RiskBadge level={t.risk_level} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  Page {data.page} of {data.pages} · {data.total} total
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    disabled={data.page <= 1}
                    onClick={() => setParams((p) => ({ ...p, page: (p.page || 1) - 1 }))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    disabled={data.page >= data.pages}
                    onClick={() => setParams((p) => ({ ...p, page: (p.page || 1) + 1 }))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
