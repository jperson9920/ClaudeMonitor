import React from "react";
import { render } from "@testing-library/react";
import ProgressBar from "../ProgressBar";

describe("ProgressBar", () => {
  test("renders blue bar for normal value (50%)", () => {
    const { getByTestId } = render(<ProgressBar value={50} />);
    const fill = getByTestId("progress-fill");
    expect(fill).toBeInTheDocument();
    expect(fill.className).toContain("bg-blue-500");
    expect(fill).toHaveStyle({ width: "50%" });
  });

  test("renders warning color for value >= warning threshold", () => {
    const { getByTestId } = render(<ProgressBar value={85} thresholds={{ warning: 80, critical: 100 }} />);
    const fill = getByTestId("progress-fill");
    expect(fill.className).toContain("bg-yellow-400");
    expect(fill).toHaveStyle({ width: "85%" });
  });

  test("renders critical color for value >= critical threshold", () => {
    const { getByTestId } = render(<ProgressBar value={100} thresholds={{ warning: 80, critical: 100 }} />);
    const fill = getByTestId("progress-fill");
    expect(fill.className).toContain("bg-red-500");
    expect(fill).toHaveStyle({ width: "100%" });
  });
});