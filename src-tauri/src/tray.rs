use tauri::AppHandle;
use serde_json::json;

/// Minimal system tray stubs to maintain compatibility when the tauri
/// system-tray API is not available or built without the feature flags.
///
/// - create_system_tray returns None; lib.rs does not rely on the returned
///   value when building without system-tray support.
/// - handle_tray_event is a no-op that accepts an AppHandle and a string
///   event placeholder to avoid referencing tauri-specific event enums.
pub fn create_system_tray() -> Option<()> {
    // System tray not available in this build configuration.
    None
}

/// No-op handler used when system tray events are not available in the tauri crate.
/// Accepts the AppHandle to allow callers to pass through their handle without
/// causing compilation errors when the concrete SystemTrayEvent type is absent.
pub fn handle_tray_event(_app: &AppHandle, _event: &str) {
    // Intentionally noop.
    let _ = json!({"status":"noop"});
}