import React, { useEffect, useState } from "react";

export interface ResetTimerProps {
  resetTimeISO?: string | null;
  rawResetText?: string | null;
}

/**
 * ResetTimer
 * - If resetTimeISO is parseable as a Date, shows a relative countdown (e.g. "Resets in 4h")
 *   and updates every 30s.
 * - Otherwise falls back to rawResetText or a default message.
 */
export default function ResetTimer({ resetTimeISO, rawResetText }: ResetTimerProps) {
  const [label, setLabel] = useState<string>(() => formatLabel(resetTimeISO, rawResetText));

  useEffect(() => {
    setLabel(formatLabel(resetTimeISO, rawResetText));
    if (!resetTimeISO) {
      return;
    }
    let target = Date.parse(resetTimeISO);
    if (Number.isNaN(target)) {
      return;
    }

    const update = () => setLabel(formatLabel(resetTimeISO, rawResetText));
    const id = window.setInterval(update, 30_000); // update every 30s
    // also update shortly after mount to avoid stale tick
    const to = window.setTimeout(update, 500);
    return () => {
      clearInterval(id);
      clearTimeout(to);
    };
  }, [resetTimeISO, rawResetText]);

  return <span className="text-sm text-gray-600 dark:text-gray-300" aria-live="polite">{label}</span>;
}

function formatLabel(resetTimeISO?: string | null, rawResetText?: string | null): string {
  if (resetTimeISO) {
    const ts = Date.parse(resetTimeISO);
    if (!Number.isNaN(ts)) {
      const diffMs = ts - Date.now();
      // If already passed or within 1s, show 'Resets soon' or exact units
      if (diffMs <= 1000) return "Resets soon";
      const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
      const seconds = Math.round(diffMs / 1000);
      const minutes = Math.round(seconds / 60);
      const hours = Math.round(minutes / 60);
      const days = Math.round(hours / 24);

      // Choose best unit
      if (Math.abs(days) >= 1) return `Resets ${rtf.format(days, "day")}`;
      if (Math.abs(hours) >= 1) return `Resets ${rtf.format(hours, "hour")}`;
      if (Math.abs(minutes) >= 1) return `Resets ${rtf.format(minutes, "minute")}`;
      return `Resets ${rtf.format(seconds, "second")}`;
    }
  }

  if (rawResetText) return rawResetText;
  return "Reset time unknown";
}