import React from "react";
import { render } from "@testing-library/react";
import UsageDisplay from "../UsageDisplay";
import type { UsagePayload } from "../../types/usage";

const samplePayload: UsagePayload = {
  status: "ok",
  found_components: 3,
  components: [
    {
      id: "current_session",
      name: "Current session",
      usage_percent: 3,
      tokens_used: null,
      tokens_limit: null,
      reset_time: new Date(Date.now() + 3600_000).toISOString(),
      raw_reset_text: "Resets in 1 hr",
      last_updated: new Date().toISOString(),
      status: "ok",
    },
    {
      id: "weekly_all_models",
      name: "All models",
      usage_percent: 45,
      tokens_used: 450,
      tokens_limit: 1000,
      reset_time: null,
      raw_reset_text: "",
      last_updated: new Date().toISOString(),
      status: "ok",
    },
    {
      id: "weekly_opus",
      name: "Opus only",
      usage_percent: 92,
      tokens_used: 920,
      tokens_limit: 1000,
      reset_time: null,
      raw_reset_text: "",
      last_updated: new Date().toISOString(),
      status: "ok",
    },
  ],
};

describe("UsageDisplay", () => {
  test("renders three component rows with percentages and reset text", () => {
    const { getByText } = render(
      <UsageDisplay payload={samplePayload} loading={false} error={null} onRefresh={() => {}} onLogin={() => {}} />
    );

    expect(getByText("Current session")).toBeInTheDocument();
    expect(getByText("All models")).toBeInTheDocument();
    expect(getByText("Opus only")).toBeInTheDocument();

    // percentages
    expect(getByText("3%")).toBeInTheDocument();
    expect(getByText("45%")).toBeInTheDocument();
    expect(getByText("92%")).toBeInTheDocument();

    // reset raw text present for first row
    expect(getByText((c) => c.includes("Resets") || c.includes("Reset"))).toBeTruthy();
  });

  test("shows loading state when loading is true", () => {
    const { getByText } = render(
      <UsageDisplay payload={null} loading={true} error={null} onRefresh={() => {}} onLogin={() => {}} />
    );
    expect(getByText("Loading usage…")).toBeInTheDocument();
  });

  test("shows error alert when error provided", () => {
    const err = new Error("Test failure");
    const { getByRole } = render(
      <UsageDisplay payload={null} loading={false} error={err} onRefresh={() => {}} onLogin={() => {}} />
    );
    expect(getByRole("alert")).toBeInTheDocument();
  });
});