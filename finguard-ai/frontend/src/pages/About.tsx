import { getHealth } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/primitives";
import { PageHeader } from "@/components/ui/widgets";
import { useTheme } from "@/components/layout/ThemeProvider";
import { useFetch } from "@/hooks/useFetch";
import { Moon, Sun } from "lucide-react";

export default function About() {
  const { data, loading } = useFetch(getHealth, []);
  const { theme, toggle } = useTheme();

  return (
    <div>
      <PageHeader title="Settings / About" subtitle="Preferences and system status" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
          </CardHeader>
          <CardContent>
            <button
              onClick={toggle}
              className="flex w-full items-center justify-between rounded-md border border-border px-4 py-3 text-sm hover:bg-muted"
            >
              <span>Theme</span>
              <span className="flex items-center gap-2 font-medium capitalize">
                {theme === "dark" ? (
                  <Moon className="h-4 w-4" />
                ) : (
                  <Sun className="h-4 w-4" />
                )}
                {theme}
              </span>
            </button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Spinner />
            ) : (
              <dl className="divide-y divide-border text-sm">
                <Row k="API status" v={data?.status ?? "unknown"} />
                <Row k="Model loaded" v={data?.model_loaded ? "Yes" : "No"} />
                <Row k="Database" v={data?.database ?? "unknown"} />
                <Row k="API version" v={data?.version ?? "—"} />
              </dl>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>About FinGuard AI</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>
              FinGuard AI is a machine-learning platform for detecting potentially
              fraudulent financial transactions. It trains Logistic Regression, Random
              Forest and XGBoost models on PaySim-style data, selects the best by
              PR-AUC, and serves real-time predictions with SHAP-based explanations.
            </p>
            <p>
              Built with React, TypeScript, FastAPI, scikit-learn, XGBoost and
              PostgreSQL. This is an educational portfolio project, not a production
              financial system.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between py-2.5">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="font-medium capitalize">{v}</dd>
    </div>
  );
}
