import { useEffect, useRef, useState } from "react";
import type { UsagePayload } from "../types/usage";

declare global {
  interface Window {
    __TAURI__?: any;
  }
}

/**
 * useUsage - connects to Tauri backend via window.__TAURI__.invoke and window.__TAURI__.event
 *
 * Returns:
 *  - payload: UsagePayload | null
 *  - loading: boolean
 *  - error: Error | null
 *  - refresh(): Promise<void>
 *  - login(): Promise<void>
 *  - startPolling(intervalSecs?: number): Promise<void>
 *  - stopPolling(): Promise<void>
 */
export default function useUsage() {
  const [payload, setPayload] = useState<UsagePayload | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  // keep refs to unlisten fns to cleanup on unmount
  const unlistenRefs = useRef<Array<() => void>>([]);

  useEffect(() => {
    // Subscribe to Tauri events if available
    const tauri = window.__TAURI;
    if (tauri && tauri.event && typeof tauri.event.listen === "function") {
      // usage-update
      const p1 = tauri.event.listen("usage-update", (evt: any) => {
        try {
          const data = evt?.payload as UsagePayload;
          setPayload(data);
          setError(null);
        } catch (e: any) {
          setError(e instanceof Error ? e : new Error(String(e)));
        } finally {
          setLoading(false);
        }
      });
      // usage-error
      const p2 = tauri.event.listen("usage-error", (evt: any) => {
        const payloadErr = evt?.payload;
        const message = payloadErr?.message ?? "Unknown usage error";
        const err = new Error(message);
        // attach diagnostics for UI exploration
        (err as any).diagnostics = payloadErr?.diagnostics ?? payloadErr;
        setError(err);
        setLoading(false);
      });

      // p1 and p2 may be promises that resolve to unlisten functions
      Promise.all([p1, p2])
        .then((unlistenFns: any[]) => {
          // store cleanup fns
          unlistenRefs.current.push(
            ...(unlistenFns.map((u) => (typeof u === "function" ? u : () => {})) as Array<() => void>)
          );
        })
        .catch(() => {
          // ignore listen errors; fallback to manual polling
        });
    }

    // On mount, do an initial check to get current state (non-blocking)
    (async () => {
      try {
        setLoading(true);
        if (tauri && typeof tauri.invoke === "function") {
          const res = await tauri.invoke("poll_usage_once");
          setPayload(res as UsagePayload);
        }
      } catch (e: any) {
        setError(e instanceof Error ? e : new Error(String(e)));
      } finally {
        setLoading(false);
      }
    })();

    return () => {
      // cleanup listeners
      unlistenRefs.current.forEach((u) => {
        try {
          u();
        } catch {
          // ignore
        }
      });
      unlistenRefs.current = [];
    };
  }, []);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      if (window.__TAURI && typeof window.__TAURI.invoke === "function") {
        const res = await window.__TAURI.invoke("poll_usage_once");
        setPayload(res as UsagePayload);
      } else {
        throw new Error("Tauri API not available");
      }
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  }

  async function login() {
    setLoading(true);
    setError(null);
    try {
      if (window.__TAURI && typeof window.__TAURI.invoke === "function") {
        await window.__TAURI.invoke("manual_login");
      } else {
        throw new Error("Tauri API not available");
      }
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error(String(e)));
    } finally {
      setLoading(false);
    }
  }

  async function startPolling(intervalSecs: number = 300) {
    try {
      if (window.__TAURI && typeof window.__TAURI.invoke === "function") {
        await window.__TAURI.invoke("start_polling", { interval_secs: intervalSecs });
      } else {
        throw new Error("Tauri API not available");
      }
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async function stopPolling() {
    try {
      if (window.__TAURI && typeof window.__TAURI.invoke === "function") {
        await window.__TAURI.invoke("stop_polling");
      } else {
        throw new Error("Tauri API not available");
      }
    } catch (e: any) {
      setError(e instanceof Error ? e : new Error(String(e)));
    }
  }

  return {
    payload,
    loading,
    error,
    refresh,
    login,
    startPolling,
    stopPolling,
  };
}