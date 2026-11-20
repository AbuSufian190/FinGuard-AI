import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskBadge } from "../src/components/ui/primitives";
import { StatCard } from "../src/components/ui/widgets";
import { ShieldAlert } from "lucide-react";

describe("UI components", () => {
  it("renders a risk badge", () => {
    render(<RiskBadge level="HIGH" />);
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("renders a stat card with label and value", () => {
    render(<StatCard label="Fraud" value="42" icon={ShieldAlert} tone="danger" />);
    expect(screen.getByText("Fraud")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });
});
