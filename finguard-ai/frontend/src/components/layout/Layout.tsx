import { getHealth } from "@/api/client";
import { useFetch } from "@/hooks/useFetch";
import { Menu, Moon, Sun } from "lucide-react";
import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Button } from "../ui/primitives";
import { Sidebar } from "./Sidebar";
import { useTheme } from "./ThemeProvider";

export function Layout() {
  const [open, setOpen] = useState(false);
  const { theme, toggle } = useTheme();
  const { data: health } = useFetch(getHealth, []);

  return (
    <div className="min-h-screen">
      <Sidebar open={open} />
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-border bg-background/80 px-4 backdrop-blur lg:px-8">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              className="px-2 lg:hidden"
              onClick={() => setOpen((o) => !o)}
              aria-label="Toggle navigation"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span
                className={
                  "inline-block h-2 w-2 rounded-full " +
                  (health?.model_loaded ? "bg-success" : "bg-warning")
                }
              />
              {health
                ? health.model_loaded
                  ? "Model online"
                  : "Model not loaded"
                : "Connecting…"}
            </div>
          </div>
          <Button
            variant="outline"
            className="px-2"
            onClick={toggle}
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>
        </header>
        <main className="mx-auto max-w-7xl p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
