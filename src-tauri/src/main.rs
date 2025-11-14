// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod polling;
mod scraper;
mod settings;
mod state;

use settings::Settings;
use state::AppState;
use tauri::{
    CustomMenuItem, Manager, State, SystemTray, SystemTrayEvent, SystemTrayMenu,
    SystemTrayMenuItem,
};

/// Check if a valid session exists
#[tauri::command]
async fn check_session(state: State<'_, AppState>) -> Result<bool, String> {
    let scraper = state.scraper.lock().await;
    scraper.has_valid_session()
}

/// Perform manual login (one-time setup)
#[tauri::command]
async fn manual_login(state: State<'_, AppState>) -> Result<String, String> {
    let scraper = state.scraper.lock().await;
    scraper.manual_login().await
}

/// Poll usage data from Claude.ai
#[tauri::command]
async fn poll_usage(
    state: State<'_, AppState>,
) -> Result<scraper::UsageData, String> {
    let scraper = state.scraper.lock().await;
    let data = scraper.poll_usage().await?;

    // Update last poll data
    {
        let mut last_data = state.last_data.lock().await;
        *last_data = Some(data.clone());
    }
    {
        let mut last_poll = state.last_poll.lock().await;
        *last_poll = Some(std::time::Instant::now());
    }

    Ok(data)
}

/// Start automatic polling (every 5 minutes)
#[tauri::command]
async fn start_polling(app: tauri::AppHandle, state: State<'_, AppState>) -> Result<(), String> {
    // Mark polling as started
    {
        let mut polling = state.polling.lock().await;
        polling.start();
    }

    // Start the polling task
    polling::start_polling_task(
        app,
        state.scraper_clone(),
        state.polling_clone(),
        state.last_poll_clone(),
        state.last_data_clone(),
    );

    Ok(())
}

/// Stop automatic polling
#[tauri::command]
async fn stop_polling(state: State<'_, AppState>) -> Result<(), String> {
    let mut polling = state.polling.lock().await;
    polling.stop();
    Ok(())
}

/// Get application version
#[tauri::command]
fn get_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

/// Set window always on top
#[tauri::command]
async fn set_always_on_top(window: tauri::Window, enabled: bool) -> Result<(), String> {
    window
        .set_always_on_top(enabled)
        .map_err(|e| format!("Failed to set always on top: {}", e))?;
    Ok(())
}

/// Load settings from disk
#[tauri::command]
fn load_settings(app: tauri::AppHandle) -> Result<Settings, String> {
    Settings::load(&app)
}

/// Save settings to disk
#[tauri::command]
fn save_settings(app: tauri::AppHandle, settings: Settings) -> Result<(), String> {
    settings.save(&app)
}

/// Save current window position and size
#[tauri::command]
async fn save_window_state(window: tauri::Window, app: tauri::AppHandle) -> Result<(), String> {
    // Get current window position and size
    let position = window
        .outer_position()
        .map_err(|e| format!("Failed to get window position: {}", e))?;
    let size = window
        .outer_size()
        .map_err(|e| format!("Failed to get window size: {}", e))?;

    // Load current settings
    let mut settings = Settings::load(&app)?;

    // Update window settings
    settings.window.x = Some(position.x);
    settings.window.y = Some(position.y);
    settings.window.width = size.width as f64;
    settings.window.height = size.height as f64;

    // Save updated settings
    settings.save(&app)?;

    Ok(())
}

/// Create the system tray with menu items
fn create_system_tray() -> SystemTray {
    let show = CustomMenuItem::new("show".to_string(), "Show Dashboard");
    let hide = CustomMenuItem::new("hide".to_string(), "Hide Window");
    let always_on_top = CustomMenuItem::new("always_on_top".to_string(), "Always on Top");
    let refresh = CustomMenuItem::new("refresh".to_string(), "Refresh Now");
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");

    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_item(hide)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(always_on_top)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(refresh)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);

    SystemTray::new().with_menu(tray_menu)
}

/// Handle system tray events
fn handle_system_tray_event(app: &tauri::AppHandle, event: SystemTrayEvent) {
    match event {
        SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
            "show" => {
                let window = app.get_window("main").unwrap();
                window.show().unwrap();
                window.set_focus().unwrap();
            }
            "hide" => {
                let window = app.get_window("main").unwrap();
                window.hide().unwrap();
            }
            "always_on_top" => {
                let window = app.get_window("main").unwrap();
                // Toggle always on top
                let is_always_on_top = window.is_always_on_top().unwrap_or(false);
                window.set_always_on_top(!is_always_on_top).unwrap();

                // Emit event to frontend to update UI state
                app.emit_all("always-on-top-changed", !is_always_on_top).unwrap();
            }
            "refresh" => {
                // Emit event to frontend to trigger refresh
                app.emit_all("force-refresh", ()).unwrap();
            }
            "quit" => {
                std::process::exit(0);
            }
            _ => {}
        },
        SystemTrayEvent::LeftClick { .. } => {
            // Show window on left click
            let window = app.get_window("main").unwrap();
            if window.is_visible().unwrap() {
                window.hide().unwrap();
            } else {
                window.show().unwrap();
                window.set_focus().unwrap();
            }
        }
        _ => {}
    }
}

fn main() {
    // Initialize application state
    let app_state = AppState::new("./scraper");

    tauri::Builder::default()
        .manage(app_state)
        .system_tray(create_system_tray())
        .on_system_tray_event(handle_system_tray_event)
        .invoke_handler(tauri::generate_handler![
            check_session,
            manual_login,
            poll_usage,
            start_polling,
            stop_polling,
            get_version,
            set_always_on_top,
            load_settings,
            save_settings,
            save_window_state
        ])
        .setup(|app| {
            // Restore window position and size from settings
            let window = app.get_window("main").unwrap();

            match Settings::load(&app.handle()) {
                Ok(settings) => {
                    // Restore size
                    let _ = window.set_size(tauri::LogicalSize {
                        width: settings.window.width,
                        height: settings.window.height,
                    });

                    // Restore position if saved
                    if let (Some(x), Some(y)) = (settings.window.x, settings.window.y) {
                        let _ = window.set_position(tauri::LogicalPosition { x, y });
                    } else {
                        // Center window if no position saved
                        let _ = window.center();
                    }

                    // Restore always on top setting
                    let _ = window.set_always_on_top(settings.window.always_on_top);
                }
                Err(e) => {
                    eprintln!("Failed to load settings on startup: {}", e);
                    // Use defaults - window will use tauri.conf.json settings
                    let _ = window.center();
                }
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
