import React from "react";
import { render } from "@testing-library/react";
import ResetTimer from "../ResetTimer";

describe("ResetTimer", () => {
  test("falls back to rawResetText when ISO is invalid", () => {
    const { getByText } = render(
      <ResetTimer resetTimeISO={"not-a-date"} rawResetText={"Resets in 4 hr 16 min"} />
    );
    expect(getByText("Resets in 4 hr 16 min")).toBeInTheDocument();
  });

  test("shows relative label when valid ISO is provided", () => {
    // 90 seconds from now
    const iso = new Date(Date.now() + 90_000).toISOString();
    const { getByText } = render(<ResetTimer resetTimeISO={iso} />);
    // Expect text that starts with "Resets" (format uses Intl.RelativeTimeFormat)
    expect(getByText((content) => content.startsWith("Resets"))).toBeInTheDocument();
  });
});