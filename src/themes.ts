export interface ThemeColors {
  primary_start: string;
  primary_end: string;
  accent: string;
  warning: string;
  critical: string;
}

export interface Theme {
  name: string;
  colors: ThemeColors;
}

export const PRESET_THEMES: Theme[] = [
  {
    name: "default",
    colors: {
      primary_start: "#667eea",
      primary_end: "#764ba2",
      accent: "#22c55e",
      warning: "#f97316",
      critical: "#ef4444",
    },
  },
  {
    name: "ocean",
    colors: {
      primary_start: "#0891b2",
      primary_end: "#0e7490",
      accent: "#06b6d4",
      warning: "#f59e0b",
      critical: "#ef4444",
    },
  },
  {
    name: "forest",
    colors: {
      primary_start: "#059669",
      primary_end: "#047857",
      accent: "#10b981",
      warning: "#f59e0b",
      critical: "#ef4444",
    },
  },
  {
    name: "sunset",
    colors: {
      primary_start: "#f97316",
      primary_end: "#ec4899",
      accent: "#fb923c",
      warning: "#eab308",
      critical: "#dc2626",
    },
  },
  {
    name: "midnight",
    colors: {
      primary_start: "#1e3a8a",
      primary_end: "#581c87",
      accent: "#3b82f6",
      warning: "#f59e0b",
      critical: "#ef4444",
    },
  },
  {
    name: "monochrome",
    colors: {
      primary_start: "#374151",
      primary_end: "#1f2937",
      accent: "#9ca3af",
      warning: "#d1d5db",
      critical: "#6b7280",
    },
  },
];

export const applyTheme = (colors: ThemeColors) => {
  const root = document.documentElement;
  root.style.setProperty("--primary-start", colors.primary_start);
  root.style.setProperty("--primary-end", colors.primary_end);
  root.style.setProperty("--accent", colors.accent);
  root.style.setProperty("--warning", colors.warning);
  root.style.setProperty("--critical", colors.critical);
};

export const getThemeByName = (name: string): Theme | undefined => {
  return PRESET_THEMES.find((theme) => theme.name === name);
};
