mod resource;
pub use resource::resolve_scraper_path;
mod scraper;
mod polling;
mod config;
mod tray;

use std::sync::Mutex;
use tauri::{Manager, Emitter};
use serde_json::Value;

/// 30s timeout for interactive login
#[tauri::command]
async fn manual_login() -> Result<Value, String> {
    scraper::spawn_scraper(vec!["--login".to_string()], 30)
        .await
        .map_err(|e| e.to_string())
}

/// Check session with 30s timeout
#[tauri::command]
async fn check_session() -> Result<Value, String> {
    scraper::spawn_scraper(vec!["--check-session".to_string()], 30)
        .await
        .map_err(|e| e.to_string())
}

/// Force a single poll. Uses the configured 30s timeout for scraper subprocess.
#[tauri::command]
async fn poll_usage_once() -> Result<Value, String> {
    scraper::spawn_scraper(vec!["--poll_once".to_string()], 30)
        .await
        .map_err(|e| e.to_string())
}

/// Start polling. If `interval_secs` is Some, persist it to disk; otherwise use persisted config default.
#[tauri::command]
fn start_polling(
    state: tauri::State<'_, Mutex<polling::Poller>>,
    app_handle: tauri::AppHandle,
    interval_secs: Option<u64>,
) -> Result<(), String> {
    let interval = if let Some(i) = interval_secs {
        // persist requested interval
        let mut cfg = config::load_config();
        cfg.polling_interval_secs = i;
        // best-effort persist; log errors via emitted event
        if let Err(e) = config::save_config(&cfg) {
            let mut obj = serde_json::Map::new();
            obj.insert("status".to_string(), serde_json::Value::String("error".to_string()));
            obj.insert("message".to_string(), serde_json::Value::String(format!("failed to save config: {}", e)));
            let _ = app_handle.emit("usage-error", serde_json::Value::Object(obj));
        }
        i
    } else {
        config::load_config().polling_interval_secs
    };

    let mut guard = state.lock().map_err(|e| format!("mutex lock failed: {}", e))?;
    guard.start(app_handle, interval)
}

/// Stop background polling
#[tauri::command]
fn stop_polling(state: tauri::State<'_, Mutex<polling::Poller>>) -> Result<(), String> {
    let mut guard = state.lock().map_err(|e| format!("mutex lock failed: {}", e))?;
    guard.stop()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let poller = polling::Poller::new_default();
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(Mutex::new(poller))
        .invoke_handler(tauri::generate_handler![
            manual_login,
            check_session,
            poll_usage_once,
            start_polling,
            stop_polling
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
