use std::sync::Arc;
use std::time::Instant;
use tokio::sync::Mutex;

use crate::scraper::{ScraperInterface, UsageData};

/// Polling state to track whether automatic polling is active
#[derive(Debug)]
pub struct PollingState {
    enabled: bool,
}

impl PollingState {
    pub fn new() -> Self {
        Self { enabled: false }
    }

    pub fn is_enabled(&self) -> bool {
        self.enabled
    }

    pub fn start(&mut self) {
        self.enabled = true;
    }

    pub fn stop(&mut self) {
        self.enabled = false;
    }
}

/// Application state shared across the Tauri application
pub struct AppState {
    /// Scraper interface for spawning Python subprocess
    pub scraper: Arc<Mutex<ScraperInterface>>,

    /// Polling state to control automatic polling
    pub polling: Arc<Mutex<PollingState>>,

    /// Last successful poll time
    pub last_poll: Arc<Mutex<Option<Instant>>>,

    /// Last retrieved usage data
    pub last_data: Arc<Mutex<Option<UsageData>>>,
}

impl AppState {
    /// Create new application state
    pub fn new(scraper_dir: &str) -> Self {
        let scraper = ScraperInterface::new(scraper_dir);

        Self {
            scraper: Arc::new(Mutex::new(scraper)),
            polling: Arc::new(Mutex::new(PollingState::new())),
            last_poll: Arc::new(Mutex::new(None)),
            last_data: Arc::new(Mutex::new(None)),
        }
    }

    /// Get a clone of the scraper Arc for use in background tasks
    pub fn scraper_clone(&self) -> Arc<Mutex<ScraperInterface>> {
        Arc::clone(&self.scraper)
    }

    /// Get a clone of the polling state Arc for use in background tasks
    pub fn polling_clone(&self) -> Arc<Mutex<PollingState>> {
        Arc::clone(&self.polling)
    }

    /// Get a clone of the last poll Arc for use in background tasks
    pub fn last_poll_clone(&self) -> Arc<Mutex<Option<Instant>>> {
        Arc::clone(&self.last_poll)
    }

    /// Get a clone of the last data Arc for use in background tasks
    pub fn last_data_clone(&self) -> Arc<Mutex<Option<UsageData>>> {
        Arc::clone(&self.last_data)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_polling_state() {
        let mut state = PollingState::new();
        assert!(!state.is_enabled());

        state.start();
        assert!(state.is_enabled());

        state.stop();
        assert!(!state.is_enabled());
    }

    #[test]
    fn test_app_state_creation() {
        let state = AppState::new("./scraper");
        // Just verify it doesn't panic
        assert!(true);
    }
}
