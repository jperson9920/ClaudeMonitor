use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::sync::Mutex;
use tauri::{AppHandle, Notification};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationSettings {
    pub enabled: bool,
    pub thresholds: Vec<u32>,
    pub sound_enabled: bool,
}

impl Default for NotificationSettings {
    fn default() -> Self {
        Self {
            enabled: true,
            thresholds: vec![80, 90, 100],
            sound_enabled: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationRecord {
    pub timestamp: String,
    pub title: String,
    pub message: String,
    pub level: String,
}

/// Track which thresholds have already triggered notifications
pub struct NotificationState {
    notified_thresholds: Mutex<HashSet<u32>>,
}

impl NotificationState {
    pub fn new() -> Self {
        Self {
            notified_thresholds: Mutex::new(HashSet::new()),
        }
    }

    pub fn has_notified(&self, threshold: u32) -> bool {
        self.notified_thresholds
            .lock()
            .unwrap()
            .contains(&threshold)
    }

    pub fn mark_notified(&self, threshold: u32) {
        self.notified_thresholds.lock().unwrap().insert(threshold);
    }

    pub fn reset(&self) {
        self.notified_thresholds.lock().unwrap().clear();
    }
}

/// Send a desktop notification
pub fn send_notification(
    app: &AppHandle,
    title: &str,
    body: &str,
) -> Result<(), String> {
    Notification::new(&app.config().tauri.bundle.identifier)
        .title(title)
        .body(body)
        .show()
        .map_err(|e| format!("Failed to send notification: {}", e))?;

    eprintln!("Notification sent: {} - {}", title, body);
    Ok(())
}

/// Check usage and send threshold notifications if needed
pub fn check_and_notify(
    app: &AppHandle,
    usage_percent: f64,
    settings: &NotificationSettings,
    state: &NotificationState,
) -> Result<(), String> {
    // Skip if notifications disabled
    if !settings.enabled {
        return Ok(());
    }

    // Check each threshold
    for threshold in &settings.thresholds {
        let threshold_f64 = *threshold as f64;

        // If usage has crossed this threshold and we haven't notified yet
        if usage_percent >= threshold_f64 && !state.has_notified(*threshold) {
            let title = match *threshold {
                100 => "🚫 Usage Limit Reached",
                90.. => "⚠️ High Usage Warning",
                _ => "📊 Usage Alert",
            };

            let body = format!(
                "You've used {}% of your Claude usage cap.",
                threshold
            );

            send_notification(app, title, &body)?;
            state.mark_notified(*threshold);
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_notification_state() {
        let state = NotificationState::new();

        assert!(!state.has_notified(80));

        state.mark_notified(80);
        assert!(state.has_notified(80));

        state.reset();
        assert!(!state.has_notified(80));
    }

    #[test]
    fn test_notification_settings_default() {
        let settings = NotificationSettings::default();
        assert_eq!(settings.enabled, true);
        assert_eq!(settings.thresholds, vec![80, 90, 100]);
        assert_eq!(settings.sound_enabled, true);
    }
}
