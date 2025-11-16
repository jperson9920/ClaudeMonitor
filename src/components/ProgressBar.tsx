import React from "react";

export interface ProgressBarThresholds {
  warning: number;
  critical: number;
}

export interface ProgressBarProps {
  value: number; // 0-100
  size?: "sm" | "md" | "lg";
  thresholds?: ProgressBarThresholds;
  ariaLabel?: string;
}

const sizeHeight = {
  sm: "h-2",
  md: "h-3",
  lg: "h-4",
};

export default function ProgressBar({
  value,
  size = "md",
  thresholds = { warning: 80, critical: 100 },
  ariaLabel,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(value)));
  const isCritical = clamped >= thresholds.critical;
  const isWarning = !isCritical && clamped >= thresholds.warning;

  const barColor = isCritical
    ? "bg-red-500"
    : isWarning
    ? "bg-yellow-400"
    : "bg-blue-500";

  return (
    <div className="w-full" aria-hidden={false}>
      <label className="sr-only">{ariaLabel ?? `Usage: ${clamped}%`}</label>

      {/* Semantic progress element for accessibility */}
      <progress
        className="sr-only"
        value={clamped}
        max={100}
        aria-label={ariaLabel ?? "Usage progress"}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={clamped}
        role="progressbar"
      />

      {/* Visible styled bar */}
      <div
        className={`w-full rounded-md bg-gray-200 dark:bg-gray-700 overflow-hidden ${sizeHeight[size]}`}
        aria-hidden="true"
      >
        <div
          className={`${barColor} h-full transition-all duration-500`}
          style={{ width: `${clamped}%` }}
          data-testid="progress-fill"
        />
      </div>
    </div>
  );
}