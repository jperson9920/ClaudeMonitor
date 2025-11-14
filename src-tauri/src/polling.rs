use std::sync::Arc;
use std::time::{Duration, Instant};
use tauri::{AppHandle, Manager};
use tokio::sync::Mutex;
use tokio::time;

use crate::scraper::{ScraperInterface, UsageData};
use crate::state::PollingState;

/// Default polling interval (5 minutes in seconds)
const DEFAULT_POLL_INTERVAL_SECS: u64 = 300;

/// Start the automatic polling loop
///
/// This spawns a background task that polls the scraper every 5 minutes
/// and emits events to the frontend with the results.
pub fn start_polling_task(
    app: AppHandle,
    scraper: Arc<Mutex<ScraperInterface>>,
    polling_state: Arc<Mutex<PollingState>>,
    last_poll: Arc<Mutex<Option<Instant>>>,
    last_data: Arc<Mutex<Option<UsageData>>>,
) {
    tauri::async_runtime::spawn(async move {
        let mut interval = time::interval(Duration::from_secs(DEFAULT_POLL_INTERVAL_SECS));

        loop {
            interval.tick().await;

            // Check if polling is enabled
            let enabled = {
                let state = polling_state.lock().await;
                state.is_enabled()
            };

            if !enabled {
                continue;
            }

            // Perform poll
            eprintln!("Automatic poll triggered");

            let result = {
                let scraper_guard = scraper.lock().await;
                scraper_guard.poll_usage().await
            };

            match result {
                Ok(data) => {
                    eprintln!("Poll successful: {}%", data.usage_percent);

                    // Update last poll time and data
                    {
                        let mut last_poll_guard = last_poll.lock().await;
                        *last_poll_guard = Some(Instant::now());
                    }
                    {
                        let mut last_data_guard = last_data.lock().await;
                        *last_data_guard = Some(data.clone());
                    }

                    // Emit to frontend
                    if let Err(e) = app.emit_all("usage-update", &data) {
                        eprintln!("Failed to emit usage-update event: {}", e);
                    }
                }
                Err(e) => {
                    eprintln!("Poll failed: {}", e);

                    // Emit error to frontend
                    if let Err(emit_err) = app.emit_all("usage-error", e.clone()) {
                        eprintln!("Failed to emit usage-error event: {}", emit_err);
                    }
                }
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_poll_interval_constant() {
        assert_eq!(DEFAULT_POLL_INTERVAL_SECS, 300); // 5 minutes
    }
}
