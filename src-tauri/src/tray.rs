use std::sync::{Arc, Mutex};
use tauri::{CustomMenuItem, SystemTray, SystemTrayMenu, SystemTrayEvent, SystemTrayMenuItem, Manager, AppHandle};
use serde_json::json;

/// Create the system tray with Show Dashboard, Refresh Now, and Quit menu items.
pub fn create_system_tray() -> SystemTray {
    let show = CustomMenuItem::new("show_dashboard".to_string(), "Show Dashboard");
    let refresh = CustomMenuItem::new("refresh_now".to_string(), "Refresh Now");
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");

    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_item(refresh)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);

    SystemTray::new().with_menu(tray_menu)
}

/// Handle tray events and dispatch actions to the app.
/// - show_dashboard: brings the main window to front
/// - refresh_now: triggers a single-run scraper invocation and emits a `usage-notification` event with the result
/// - quit: attempts to stop polling then exits the app
pub fn handle_tray_event(app: &AppHandle, event: SystemTrayEvent) {
    match event {
        SystemTrayEvent::MenuItemClick { id, .. } => {
            let id = id.as_str();
            match id {
                "show_dashboard" => {
                    if let Some(w) = app.get_window("main") {
                        let _ = w.show();
                        let _ = w.set_focus();
                    } else {
                        // emit a notification event so frontend can react if window not present
                        let _ = app.emit_all("usage-notification", json!({"level":"info","message":"Main window not available"}));
                    }
                }
                "refresh_now" => {
                    // Spawn an async task to call the scraper without blocking the tray event thread.
                    let app_handle = app.clone();
                    tauri::async_runtime::spawn(async move {
                        // Call the existing Rust bridge command path: directly invoke scraper spawn helper
                        let res = crate::scraper::spawn_scraper(vec!["--poll_once".to_string()], 30).await;
                        match res {
                            Ok(payload) => {
                                // Emit standard usage-update so UI and listeners receive it
                                let _ = app_handle.emit_all("usage-update", payload);
                                // Also emit a user-facing notification event
                                let _ = app_handle.emit_all("usage-notification", json!({"level":"info","message":"Refresh succeeded"}));
                            }
                            Err(e) => {
                                let mut obj = serde_json::Map::new();
                                obj.insert("status".to_string(), serde_json::Value::String("error".to_string()));
                                obj.insert("message".to_string(), serde_json::Value::String(e.to_string()));
                                let v = serde_json::Value::Object(obj);
                                let _ = app_handle.emit_all("usage-error", v.clone());
                                let _ = app_handle.emit_all("usage-notification", json!({"level":"error","message":format!("Refresh failed: {}", e)}));
                            }
                        }
                    });
                }
                "quit" => {
                    // Try to stop polling if managed
                    if let Some(state) = app.try_state::<Mutex<crate::polling::Poller>>() {
                        if let Ok(mut guard) = state.lock() {
                            let _ = guard.stop();
                        }
                    }
                    // Exit the app
                    app.exit(0);
                }
                _ => {}
            }
        }
        _ => {}
    }
}