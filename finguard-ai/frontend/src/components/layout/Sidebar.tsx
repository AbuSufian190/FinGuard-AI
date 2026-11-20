import { cn } from "@/lib/utils";
import {
  BarChart3,
  FileSearch,
  Gauge,
  History,
  Info,
  LayoutDashboard,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/analyze", label: "Transaction Analysis", icon: FileSearch },
  { to: "/batch", label: "Batch Detection", icon: UploadCloud },
  { to: "/performance", label: "Model Performance", icon: BarChart3 },
  { to: "/history", label: "Prediction History", icon: History },
  { to: "/model", label: "Model Information", icon: Gauge },
  { to: "/about", label: "Settings / About", icon: Info },
];

export function Sidebar({ open }: { open: boolean }) {
  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-30 w-64 transform border-r border-border bg-card transition-transform lg:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full"
      )}
    >
      <div className="flex h-16 items-center gap-2 border-b border-border px-5">
        <ShieldCheck className="h-6 w-6 text-primary" />
        <span className="text-lg font-bold tracking-tight">FinGuard AI</span>
      </div>
      <nav className="space-y-1 p-3">
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="absolute bottom-0 w-full border-t border-border p-4 text-xs text-muted-foreground">
        ML-powered fraud detection
      </div>
    </aside>
  );
}
