use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::fs::{self, File};
use std::io::Write;
use dirs::config_dir;

/// Application configuration persisted to disk.
#[derive(Serialize, Deserialize, Clone)]
pub struct AppConfig {
    pub polling_interval_secs: u64,
    pub start_on_login: bool,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            polling_interval_secs: 300,
            start_on_login: false,
        }
    }
}

/// Compute platform-appropriate config path:
/// - Prefer Tauri app_config_dir() if available:
///    <app_config_dir>/ClaudeUsageMonitor/config.json
/// - Fallback to current working directory `config.json` (development)
pub fn config_path() -> PathBuf {
    if let Some(mut dir) = config_dir() {
        dir.push("ClaudeUsageMonitor");
        dir.push("config.json");
        dir
    } else {
        PathBuf::from("config.json")
    }
}

/// Load configuration from disk. Returns default config when the file is missing
/// or when parsing fails (best-effort resilience).
pub fn load_config() -> AppConfig {
    let path = config_path();
    if !path.exists() {
        return AppConfig::default();
    }
    match fs::read_to_string(&path) {
        Ok(s) => match serde_json::from_str::<AppConfig>(&s) {
            Ok(cfg) => cfg,
            Err(_) => AppConfig::default(),
        },
        Err(_) => AppConfig::default(),
    }
}

/// Save configuration atomically:
/// - Ensure parent directory exists
/// - Write to a temporary file then rename into place
/// - On Unix attempt to set owner-only permissions on the temp file (0o600)
pub fn save_config(cfg: &AppConfig) -> Result<(), String> {
    let path = config_path();
    if let Some(parent) = path.parent() {
        if let Err(e) = fs::create_dir_all(parent) {
            return Err(format!("failed to create config dir: {}", e));
        }
    }

    let tmp_path = path.with_extension("tmp");
    let data = match serde_json::to_vec_pretty(cfg) {
        Ok(d) => d,
        Err(e) => return Err(format!("failed to serialize config: {}", e)),
    };

    match File::create(&tmp_path) {
        Ok(mut f) => {
            if let Err(e) = f.write_all(&data) {
                let _ = fs::remove_file(&tmp_path);
                return Err(format!("failed to write temp config: {}", e));
            }
        }
        Err(e) => return Err(format!("failed to create temp config file: {}", e)),
    }

    // Attempt to set owner-only permissions on Unix
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        if let Ok(mut perms) = fs::metadata(&tmp_path).map(|m| m.permissions()) {
            perms.set_mode(0o600);
            let _ = fs::set_permissions(&tmp_path, perms);
        }
    }

    if let Err(e) = fs::rename(&tmp_path, &path) {
        let _ = fs::remove_file(&tmp_path);
        return Err(format!("failed to rename config file into place: {}", e));
    }

    Ok(())
}