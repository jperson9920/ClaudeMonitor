use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use tauri::AppHandle;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowSettings {
    pub width: f64,
    pub height: f64,
    pub x: Option<i32>,
    pub y: Option<i32>,
    pub always_on_top: bool,
}

impl Default for WindowSettings {
    fn default() -> Self {
        Self {
            width: 450.0,
            height: 650.0,
            x: None,
            y: None,
            always_on_top: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThemeColors {
    pub primary_start: String,
    pub primary_end: String,
    pub accent: String,
    pub warning: String,
    pub critical: String,
}

impl Default for ThemeColors {
    fn default() -> Self {
        Self {
            primary_start: "#667eea".to_string(),
            primary_end: "#764ba2".to_string(),
            accent: "#22c55e".to_string(),
            warning: "#f97316".to_string(),
            critical: "#ef4444".to_string(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ThemeSettings {
    pub preset: String,
    pub custom: ThemeColors,
}

impl Default for ThemeSettings {
    fn default() -> Self {
        Self {
            preset: "default".to_string(),
            custom: ThemeColors::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PollingSettings {
    pub interval: u64,
}

impl Default for PollingSettings {
    fn default() -> Self {
        Self {
            interval: 300, // 5 minutes
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub window: WindowSettings,
    pub theme: ThemeSettings,
    pub polling: PollingSettings,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            window: WindowSettings::default(),
            theme: ThemeSettings::default(),
            polling: PollingSettings::default(),
        }
    }
}

impl Settings {
    /// Get the settings file path
    fn get_settings_path(app: &AppHandle) -> Result<PathBuf, String> {
        let app_dir = app
            .path_resolver()
            .app_data_dir()
            .ok_or("Failed to get app data directory")?;

        // Create directory if it doesn't exist
        if !app_dir.exists() {
            fs::create_dir_all(&app_dir)
                .map_err(|e| format!("Failed to create app data directory: {}", e))?;
        }

        Ok(app_dir.join("settings.json"))
    }

    /// Load settings from disk
    pub fn load(app: &AppHandle) -> Result<Settings, String> {
        let settings_path = Self::get_settings_path(app)?;

        if !settings_path.exists() {
            eprintln!("Settings file not found, using defaults");
            return Ok(Settings::default());
        }

        let contents = fs::read_to_string(&settings_path)
            .map_err(|e| format!("Failed to read settings file: {}", e))?;

        let settings: Settings = serde_json::from_str(&contents)
            .map_err(|e| format!("Failed to parse settings: {}", e))?;

        Ok(settings)
    }

    /// Save settings to disk
    pub fn save(&self, app: &AppHandle) -> Result<(), String> {
        let settings_path = Self::get_settings_path(app)?;

        let contents = serde_json::to_string_pretty(self)
            .map_err(|e| format!("Failed to serialize settings: {}", e))?;

        fs::write(&settings_path, contents)
            .map_err(|e| format!("Failed to write settings file: {}", e))?;

        eprintln!("Settings saved to {:?}", settings_path);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_settings() {
        let settings = Settings::default();
        assert_eq!(settings.window.width, 450.0);
        assert_eq!(settings.window.height, 650.0);
        assert_eq!(settings.window.always_on_top, false);
        assert_eq!(settings.theme.preset, "default");
        assert_eq!(settings.polling.interval, 300);
    }

    #[test]
    fn test_settings_serialization() {
        let settings = Settings::default();
        let json = serde_json::to_string(&settings).unwrap();
        let deserialized: Settings = serde_json::from_str(&json).unwrap();

        assert_eq!(settings.window.width, deserialized.window.width);
        assert_eq!(settings.theme.preset, deserialized.theme.preset);
    }
}
