import { useState, useEffect } from "react";
import { PRESET_THEMES, ThemeColors } from "../themes";
import "./Settings.css";

interface SettingsProps {
  isOpen: boolean;
  onClose: () => void;
  currentTheme: string;
  onThemeChange: (theme: string) => void;
  alwaysOnTop: boolean;
  onAlwaysOnTopChange: (enabled: boolean) => void;
  customColors: ThemeColors;
  onCustomColorsChange: (colors: ThemeColors) => void;
  pollingInterval: number;
  onPollingIntervalChange: (interval: number) => void;
}

export default function Settings({
  isOpen,
  onClose,
  currentTheme,
  onThemeChange,
  alwaysOnTop,
  onAlwaysOnTopChange,
  customColors,
  onCustomColorsChange,
  pollingInterval,
  onPollingIntervalChange,
}: SettingsProps) {
  const [tempColors, setTempColors] = useState<ThemeColors>(customColors);
  const [showColorPicker, setShowColorPicker] = useState(false);

  useEffect(() => {
    setTempColors(customColors);
  }, [customColors]);

  if (!isOpen) return null;

  const handleSaveColors = () => {
    onCustomColorsChange(tempColors);
    onThemeChange("custom");
    setShowColorPicker(false);
  };

  const handleColorChange = (key: keyof ThemeColors, value: string) => {
    setTempColors({ ...tempColors, [key]: value });
  };

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>⚙️ Settings</h2>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="settings-content">
          {/* Window Settings */}
          <div className="settings-section">
            <h3>Window</h3>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={alwaysOnTop}
                onChange={(e) => onAlwaysOnTopChange(e.target.checked)}
              />
              <span>Always on top</span>
            </label>
          </div>

          {/* Theme Settings */}
          <div className="settings-section">
            <h3>Theme</h3>
            <select
              value={currentTheme}
              onChange={(e) => onThemeChange(e.target.value)}
              className="settings-select"
            >
              {PRESET_THEMES.map((theme) => (
                <option key={theme.name} value={theme.name}>
                  {theme.name.charAt(0).toUpperCase() + theme.name.slice(1)}
                </option>
              ))}
              <option value="custom">Custom</option>
            </select>

            <button
              className="custom-colors-btn"
              onClick={() => setShowColorPicker(!showColorPicker)}
            >
              🎨 {showColorPicker ? "Hide" : "Customize"} Colors
            </button>

            {showColorPicker && (
              <div className="color-picker-section">
                <div className="color-input-group">
                  <label>Primary Start</label>
                  <div className="color-input-wrapper">
                    <input
                      type="color"
                      value={tempColors.primary_start}
                      onChange={(e) => handleColorChange("primary_start", e.target.value)}
                    />
                    <input
                      type="text"
                      value={tempColors.primary_start}
                      onChange={(e) => handleColorChange("primary_start", e.target.value)}
                      className="color-text-input"
                    />
                  </div>
                </div>

                <div className="color-input-group">
                  <label>Primary End</label>
                  <div className="color-input-wrapper">
                    <input
                      type="color"
                      value={tempColors.primary_end}
                      onChange={(e) => handleColorChange("primary_end", e.target.value)}
                    />
                    <input
                      type="text"
                      value={tempColors.primary_end}
                      onChange={(e) => handleColorChange("primary_end", e.target.value)}
                      className="color-text-input"
                    />
                  </div>
                </div>

                <div className="color-input-group">
                  <label>Accent</label>
                  <div className="color-input-wrapper">
                    <input
                      type="color"
                      value={tempColors.accent}
                      onChange={(e) => handleColorChange("accent", e.target.value)}
                    />
                    <input
                      type="text"
                      value={tempColors.accent}
                      onChange={(e) => handleColorChange("accent", e.target.value)}
                      className="color-text-input"
                    />
                  </div>
                </div>

                <div className="color-input-group">
                  <label>Warning</label>
                  <div className="color-input-wrapper">
                    <input
                      type="color"
                      value={tempColors.warning}
                      onChange={(e) => handleColorChange("warning", e.target.value)}
                    />
                    <input
                      type="text"
                      value={tempColors.warning}
                      onChange={(e) => handleColorChange("warning", e.target.value)}
                      className="color-text-input"
                    />
                  </div>
                </div>

                <div className="color-input-group">
                  <label>Critical</label>
                  <div className="color-input-wrapper">
                    <input
                      type="color"
                      value={tempColors.critical}
                      onChange={(e) => handleColorChange("critical", e.target.value)}
                    />
                    <input
                      type="text"
                      value={tempColors.critical}
                      onChange={(e) => handleColorChange("critical", e.target.value)}
                      className="color-text-input"
                    />
                  </div>
                </div>

                <button className="apply-colors-btn" onClick={handleSaveColors}>
                  Apply Custom Colors
                </button>
              </div>
            )}
          </div>

          {/* Export & Data */}
          <div className="settings-section">
            <h3>Export & Data</h3>
            <p style={{ fontSize: '13px', opacity: 0.8, marginBottom: '12px' }}>
              Export your usage history data
            </p>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                className="custom-colors-btn"
                onClick={async () => {
                  try {
                    const { invoke } = await import("@tauri-apps/api/tauri");
                    const csv = await invoke<string>("export_usage_csv", { hours: 24 * 30 });
                    const blob = new Blob([csv], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `claude-usage-${new Date().toISOString().split('T')[0]}.csv`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch (e) {
                    console.error("Export failed:", e);
                  }
                }}
              >
                📊 Export CSV (30 days)
              </button>
              <button
                className="custom-colors-btn"
                onClick={async () => {
                  try {
                    const { invoke } = await import("@tauri-apps/api/tauri");
                    const json = await invoke<string>("export_usage_json", { hours: 24 * 30 });
                    const blob = new Blob([json], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `claude-usage-${new Date().toISOString().split('T')[0]}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch (e) {
                    console.error("Export failed:", e);
                  }
                }}
              >
                📄 Export JSON (30 days)
              </button>
            </div>
          </div>

          {/* Polling Settings */}
          <div className="settings-section">
            <h3>Polling</h3>
            <div className="polling-setting">
              <label>Refresh interval (minutes)</label>
              <input
                type="number"
                min="1"
                max="60"
                value={pollingInterval / 60}
                onChange={(e) => onPollingIntervalChange(Number(e.target.value) * 60)}
                className="settings-input"
              />
            </div>
          </div>
        </div>

        <div className="settings-footer">
          <button className="settings-close-btn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
