import React from "react";
import useUsage from "./hooks/useUsage";
import UsageDisplay from "./components/UsageDisplay";
import "./styles.css";

/**
 * App - root React component that wires useUsage() to UsageDisplay
 */
export default function App() {
  const { payload, loading, error, refresh, login, startPolling, stopPolling } = useUsage();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <main className="container mx-auto p-4">
        <div className="max-w-4xl mx-auto">
          <header className="mb-6">
            <h1 className="text-2xl font-bold">Claude Monitor</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Dashboard showing usage metrics and reset timers.
            </p>
            <div className="mt-3 flex gap-2">
              <button
                className="px-3 py-1 rounded bg-green-500 hover:bg-green-600 text-white text-sm"
                onClick={() => startPolling(300)}
              >
                Start Polling
              </button>
              <button
                className="px-3 py-1 rounded bg-yellow-500 hover:bg-yellow-600 text-white text-sm"
                onClick={() => stopPolling()}
              >
                Stop Polling
              </button>
            </div>
          </header>

          <UsageDisplay
            payload={payload}
            loading={loading}
            error={error}
            onRefresh={() => {
              // fire-and-forget; UI handled by hook
              refresh().catch(() => {});
            }}
            onLogin={() => {
              login().catch(() => {});
            }}
          />
        </div>
      </main>
    </div>
  );
}