import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { listen } from "@tauri-apps/api/event";
import "./App.css";

interface UsageData {
  status: string;
  usage_percent: number;
  tokens_used: number;
  tokens_limit: number;
  tokens_remaining: number;
  reset_time: string | null;
  last_updated: string;
}

function App() {
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [needsLogin, setNeedsLogin] = useState(false);
  const [loggingIn, setLoggingIn] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Check session and load data on mount
  useEffect(() => {
    checkSessionAndLoad();
  }, []);

  // Listen for automatic updates and force refresh
  useEffect(() => {
    const setupListeners = async () => {
      const unlistenUpdate = await listen<UsageData>("usage-update", (event) => {
        console.log("Received usage update:", event.payload);
        setUsageData(event.payload);
        setError(null);
      });

      const unlistenError = await listen<string>("usage-error", (event) => {
        console.error("Received usage error:", event.payload);
        setError(event.payload);
      });

      const unlistenRefresh = await listen("force-refresh", () => {
        console.log("Force refresh triggered");
        refreshUsage();
      });

      return () => {
        unlistenUpdate();
        unlistenError();
        unlistenRefresh();
      };
    };

    setupListeners();
  }, []);

  const checkSessionAndLoad = async () => {
    try {
      setLoading(true);
      setError(null);

      const hasSession = await invoke<boolean>("check_session");
      console.log("Has session:", hasSession);

      if (hasSession) {
        setNeedsLogin(false);
        await loadUsageData();
        await startPolling();
      } else {
        setNeedsLogin(true);
        setLoading(false);
      }
    } catch (err) {
      console.error("Session check failed:", err);
      setError(String(err));
      setLoading(false);
    }
  };

  const loadUsageData = async () => {
    try {
      setError(null);
      const data = await invoke<UsageData>("poll_usage");
      console.log("Usage data loaded:", data);
      setUsageData(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load usage data:", err);
      const errorMsg = String(err);

      // Handle session expired specifically
      if (errorMsg.includes("session_expired") || errorMsg.includes("session_required")) {
        setNeedsLogin(true);
      } else {
        setError(errorMsg);
      }
      setLoading(false);
    }
  };

  const handleManualLogin = async () => {
    try {
      setLoggingIn(true);
      setError(null);

      console.log("Starting manual login...");
      await invoke<string>("manual_login");

      console.log("Login successful, loading data...");
      setNeedsLogin(false);
      await loadUsageData();
      await startPolling();
    } catch (err) {
      console.error("Login failed:", err);
      setError(String(err));
    } finally {
      setLoggingIn(false);
    }
  };

  const refreshUsage = async () => {
    try {
      setRefreshing(true);
      setError(null);
      await loadUsageData();
    } catch (err) {
      setError(String(err));
    } finally {
      setRefreshing(false);
    }
  };

  const startPolling = async () => {
    try {
      await invoke("start_polling");
      console.log("Automatic polling started");
    } catch (err) {
      console.error("Failed to start polling:", err);
    }
  };

  const getTimeUntilReset = () => {
    if (!usageData?.reset_time) return null;

    const resetTime = new Date(usageData.reset_time);
    const now = new Date();
    const diff = resetTime.getTime() - now.getTime();

    if (diff <= 0) return "Reset overdue";

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    return `${hours}h ${minutes}m`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const getErrorMessage = (error: string) => {
    if (error.includes("session_required") || error.includes("No saved session")) {
      return "Please log in to Claude.ai to start monitoring usage.";
    }
    if (error.includes("session_expired")) {
      return "Your session has expired. Please log in again.";
    }
    if (error.includes("navigation_failed")) {
      return "Couldn't reach Claude.ai. Please check your internet connection.";
    }
    if (error.includes("extraction_failed")) {
      return "Couldn't read usage data. The page structure may have changed. Try refreshing.";
    }
    if (error.includes("Python")) {
      return "Python is not installed or not found. Please install Python 3.9+ and try again.";
    }
    return error;
  };

  // Login Screen
  if (needsLogin) {
    return (
      <div className="app login-screen">
        <header>
          <h1>Claude Usage Monitor</h1>
          <p className="subtitle">First-Time Setup</p>
        </header>

        <div className="content">
          <div className="login-box">
            <h2>🔐 Login Required</h2>
            <p className="instructions">
              To monitor your Claude.ai usage, you need to log in once.
              A browser window will open where you can log in to Claude.ai.
            </p>
            <p className="instructions">
              Your login session will be saved securely, so you won't need
              to log in again unless your session expires (typically after 7 days).
            </p>

            <button
              onClick={handleManualLogin}
              disabled={loggingIn}
              className="login-btn"
            >
              {loggingIn ? "⏳ Waiting for Login..." : "🚀 Start Login Process"}
            </button>

            {loggingIn && (
              <p className="login-hint">
                Complete the login in the browser window, then press Enter in the terminal.
              </p>
            )}

            {error && (
              <div className="error-box">
                <strong>❌ Error:</strong>
                <p>{getErrorMessage(error)}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Loading Screen
  if (loading && !usageData) {
    return (
      <div className="app loading-screen">
        <div className="spinner"></div>
        <p>Loading usage data...</p>
      </div>
    );
  }

  // Error Screen (only if no data and error)
  if (error && !usageData) {
    return (
      <div className="app error-screen">
        <header>
          <h1>Claude Usage Monitor</h1>
        </header>
        <div className="content">
          <div className="error-box">
            <h2>❌ Error</h2>
            <p>{getErrorMessage(error)}</p>
            <button onClick={refreshUsage} className="retry-btn">
              🔄 Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!usageData) {
    return (
      <div className="app">
        <p>No usage data available</p>
      </div>
    );
  }

  const isNearLimit = usageData.usage_percent >= 80;
  const isAtLimit = usageData.usage_percent >= 100;
  const timeUntilReset = getTimeUntilReset();

  // Main Dashboard
  return (
    <div className="app">
      <header>
        <h1>Claude Usage Monitor</h1>
        <p className="subtitle">Claude Max Plan</p>
      </header>

      <div className="content">
        <div className="usage-card">
          {/* Usage Percentage */}
          <div className="usage-percent">
            <span className="percent-value">{usageData.usage_percent.toFixed(1)}%</span>
            <span className="percent-label">of limit used</span>
          </div>

          {/* Progress Bar */}
          <div className="progress-container">
            <div className="progress-bar">
              <div
                className={`progress-fill ${isAtLimit ? 'critical' : isNearLimit ? 'warning' : 'normal'}`}
                style={{ width: `${Math.min(usageData.usage_percent, 100)}%` }}
              />
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="metrics-grid">
            <div className="metric">
              <label>Used</label>
              <span className="value">{formatNumber(usageData.tokens_used)}</span>
            </div>
            <div className="metric">
              <label>Limit</label>
              <span className="value">{formatNumber(usageData.tokens_limit)}</span>
            </div>
            <div className="metric">
              <label>Remaining</label>
              <span className="value">{formatNumber(usageData.tokens_remaining)}</span>
            </div>
          </div>

          {/* Reset Timer */}
          {timeUntilReset && (
            <div className="reset-timer">
              <label>⏱ Resets in:</label>
              <span className="time">{timeUntilReset}</span>
            </div>
          )}

          {/* Alerts */}
          {isAtLimit && (
            <div className="alert critical">
              <strong>🚫 Usage limit reached!</strong>
              <p>Your cap will reset {timeUntilReset ? `in ${timeUntilReset}` : 'soon'}.</p>
            </div>
          )}

          {isNearLimit && !isAtLimit && (
            <div className="alert warning">
              <strong>⚠️ Approaching limit!</strong>
              <p>You've used {usageData.usage_percent.toFixed(0)}% of your cap.</p>
            </div>
          )}

          {/* Error Display (if error but we have cached data) */}
          {error && (
            <div className="alert error-alert">
              <strong>⚠️ Update Error:</strong>
              <p>{getErrorMessage(error)}</p>
            </div>
          )}

          {/* Last Updated */}
          <div className="last-updated">
            Last updated: {new Date(usageData.last_updated).toLocaleTimeString()}
          </div>
        </div>
      </div>

      <footer>
        <button
          onClick={refreshUsage}
          className="refresh-btn"
          disabled={refreshing}
        >
          {refreshing ? "⏳ Refreshing..." : "🔄 Refresh Now"}
        </button>
      </footer>
    </div>
  );
}

export default App;
