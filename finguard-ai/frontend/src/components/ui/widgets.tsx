import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Card, CardContent } from "./card";

// Accessible, semantic chart palette (works in light + dark). Risk colours are
// never the only cue — labels accompany them everywhere.
export const CHART_COLORS = {
  primary: "hsl(221 83% 53%)",
  success: "hsl(142 71% 40%)",
  warning: "hsl(38 92% 50%)",
  danger: "hsl(0 72% 51%)",
  muted: "hsl(215 16% 60%)",
};

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && (
          <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>
      {actions}
    </div>
  );
}

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "primary",
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  tone?: "primary" | "danger" | "success" | "warning";
}) {
  const tones = {
    primary: "text-primary bg-primary/10",
    danger: "text-danger bg-danger/10",
    success: "text-success bg-success/10",
    warning: "text-warning bg-warning/10",
  };
  return (
    <Card>
      <CardContent className="flex items-center justify-between pt-5">
        <div>
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className="mt-1 text-2xl font-bold tracking-tight">{value}</p>
        </div>
        <div className={cn("rounded-lg p-2.5", tones[tone])}>
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}

export function InfoBanner({ children }: { children: ReactNode }) {
  return (
    <div className="mb-6 rounded-md border border-warning/30 bg-warning/10 p-3 text-sm text-foreground">
      {children}
    </div>
  );
}
