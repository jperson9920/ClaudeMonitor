import React from "react";
import type { UsagePayload } from "../types/usage";
import ProgressBar from "./ProgressBar";
import ResetTimer from "./ResetTimer";

export interface UsageDisplayProps {
  payload: UsagePayload | null;
  loading: boolean;
  error: Error | null;
  onRefresh: () => void;
  onLogin: () => void;
}

/**
 * UsageDisplay
 * - Renders up to three usage component rows from payload.components
 * - Shows loading, empty, and error states
 * - Exposes Refresh and Login handlers via props
 */
export default function UsageDisplay({
  payload,
  loading,
  error,
  onRefresh,
  onLogin,
}: UsageDisplayProps) {
  const components = payload?.components ?? [];
  const found = payload?.found_components ?? components.length;
  const rowsToShow = Math.min(3, found, components.length);

  return (
    <div className="max-w-3xl mx-auto p-4">
      <header className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Claude Usage</h2>
        <div className="flex gap-2 items-center">
          <button
            className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-sm"
            onClick={onRefresh}
            aria-label="Refresh usage"
            disabled={loading}
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
          <button
            className="px-3 py-1 rounded bg-blue-500 hover:bg-blue-600 text-white text-sm"
            onClick={onLogin}
            aria-label="Manual login"
          >
            Login
          </button>
        </div>
      </header>

      {error ? (
        <div
          role="alert"
          className="mb-4 p-3 border rounded bg-red-50 border-red-200 text-red-800"
        >
          <div className="flex justify-between items-start">
            <div>
              <strong>Error:</strong> {error.message}
            </div>
            <details className="text-xs text-gray-600">
              <summary className="cursor-pointer">Details</summary>
              <pre className="text-xs whitespace-pre-wrap mt-2">
                {(error as any).diagnostics ? JSON.stringify((error as any).diagnostics, null, 2) : ""}
              </pre>
            </details>
          </div>
        </div>
      ) : null}

      {!payload && !loading ? (
        <div className="text-center text-sm text-gray-600 py-8">No usage data available.</div>
      ) : null}

      <div className="space-y-4">
        {rowsToShow > 0
          ? components.slice(0, rowsToShow).map((c) => (
              <div
                key={c.id}
                className="p-3 bg-white dark:bg-gray-800 rounded shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {c.name}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        Last updated:{" "}
                        <time dateTime={c.last_updated}>
                          {new Date(c.last_updated).toLocaleString()}
                        </time>
                      </div>
                    </div>

                    <div className="text-right ml-4">
                      <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {Math.round(c.usage_percent)}%
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {c.tokens_used != null && c.tokens_limit != null
                          ? `${c.tokens_used}/${c.tokens_limit} tokens`
                          : null}
                      </div>
                    </div>
                  </div>

                  <div className="mt-2">
                    <ProgressBar
                      value={c.usage_percent}
                      ariaLabel={`${c.name} usage`}
                      thresholds={{ warning: 80, critical: 100 }}
                      size="md"
                    />
                  </div>
                </div>

                <div className="flex-shrink-0 w-full sm:w-auto text-right sm:text-left">
                  <div className="text-sm">
                    <ResetTimer resetTimeISO={c.reset_time ?? null} rawResetText={c.raw_reset_text ?? ""} />
                  </div>
                </div>
              </div>
            ))
          : loading ? (
            <div className="text-center py-8 text-sm text-gray-600">Loading usage…</div>
          ) : (
            <div className="text-center py-8 text-sm text-gray-600">No components found.</div>
          )}
      </div>
    </div>
  );
}