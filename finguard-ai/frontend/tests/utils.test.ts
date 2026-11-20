import { describe, expect, it } from "vitest";
import { formatCurrency, formatPercent, riskColor } from "../src/lib/utils";

describe("formatting utils", () => {
  it("formats currency", () => {
    expect(formatCurrency(1000)).toContain("1,000");
  });
  it("formats percent", () => {
    expect(formatPercent(0.1234, 1)).toBe("12.3%");
  });
  it("maps risk to colour class", () => {
    expect(riskColor("HIGH")).toBe("text-danger");
    expect(riskColor("MEDIUM")).toBe("text-warning");
    expect(riskColor("LOW")).toBe("text-success");
  });
});
