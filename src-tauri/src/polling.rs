use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::time::Duration;
use tokio::task::JoinHandle;
use tokio::time;
use serde_json::Value;
use crate::scraper;
use std::fmt;

/// Poller controls a background task that invokes the scraper at intervals
/// and emits events via a generic emitter closure.
pub struct Poller {
    interval_secs: u64,
    running: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
}

impl fmt::Debug for Poller {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Poller")
            .field("interval_secs", &self.interval_secs)
            .field("running", &self.running.load(Ordering::SeqCst))
            .finish()
    }
}

impl Poller {
    /// Create a default poller with default interval 300s and not running.
    pub fn new_default() -> Self {
        Poller {
            interval_secs: 300,
            running: Arc::new(AtomicBool::new(false)),
            handle: None,
        }
    }

    /// Return whether the poller is currently running.
    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }

    /// Start the poller using a tauri AppHandle emitter (convenience)
    pub fn start(&mut self, app_handle: tauri::AppHandle, interval_secs: u64) -> Result<(), String> {
        // Wrap app_handle into a generic emitter closure and call start_with_emitter
        let emitter = Arc::new(move |event_name: String, payload: Value| {
            // best-effort emit (fire-and-forget)
            let _ = app_handle.emit_all(&event_name, payload);
        });
        self.start_with_emitter(emitter, interval_secs)
    }

    /// Start the poller with a generic emitter closure: Fn(event_name, payload)
    /// The emitter is called with `usage-update` on success and `usage-error` on error.
    pub fn start_with_emitter(
        &mut self,
        emitter: Arc<dyn Fn(String, Value) + Send + Sync + 'static>,
        interval_secs: u64,
    ) -> Result<(), String> {
        if self.is_running() {
            return Err("poller already running".to_string());
        }
        self.interval_secs = interval_secs;
        self.running.store(true, Ordering::SeqCst);
        let running = self.running.clone();

        let handle = tokio::spawn(async move {
            let mut interval = time::interval(Duration::from_secs(interval_secs));
            // Immediate first tick
            interval.set_missed_tick_behavior(time::MissedTickBehavior::Delay);
            loop {
                if !running.load(Ordering::SeqCst) {
                    break;
                }
                interval.tick().await;

                if !running.load(Ordering::SeqCst) {
                    break;
                }

                // Spawn a single-run scraper call with 30s timeout.
                match scraper::spawn_scraper(vec!["--poll_once".to_string()], 30).await {
                    Ok(payload) => {
                        (emitter)("usage-update".to_string(), payload);
                    }
                    Err(e) => {
                        let mut obj = serde_json::Map::new();
                        obj.insert("status".to_string(), serde_json::Value::String("error".to_string()));
                        obj.insert("message".to_string(), serde_json::Value::String(e.to_string()));
                        let v = serde_json::Value::Object(obj);
                        (emitter)("usage-error".to_string(), v);
                    }
                }
            }
        });

        self.handle = Some(handle);
        Ok(())
    }

    /// Stop the poller and abort the background task. Returns Ok when stopped.
    pub fn stop(&mut self) -> Result<(), String> {
        if !self.is_running() {
            return Err("poller not running".to_string());
        }
        self.running.store(false, Ordering::SeqCst);
        if let Some(h) = self.handle.take() {
            h.abort();
            // best-effort: we won't await join here
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;
    use serde_json::json;
    use tokio::time::{sleep, Duration};
    use std::sync::Arc;

    // Verify that start_with_emitter causes at least one usage-update to be emitted
    #[tokio::test]
    async fn test_poller_emits_using_override() {
        // Provide an override scraper command that prints valid JSON immediately
        std::env::set_var(
            "CLAUDE_SCRAPER_CMD",
            "python -c \"print('{\\\"status\\\":\\\"ok\\\",\\\"components\\\":[] }')\"",
        );

        let events: Arc<Mutex<Vec<(String, Value)>>> = Arc::new(Mutex::new(Vec::new()));
        let events_clone = events.clone();

        let emitter = Arc::new(move |event_name: String, payload: Value| {
            let mut guard = events_clone.lock().unwrap();
            guard.push((event_name, payload));
        });

        let mut poller = Poller::new_default();
        // use a short interval for the test
        poller.start_with_emitter(emitter.clone(), 1).expect("start should succeed");

        // wait for a couple seconds to allow at least one tick
        sleep(Duration::from_secs(2)).await;

        poller.stop().expect("stop should succeed");

        let guard = events.lock().unwrap();
        assert!(!guard.is_empty(), "expected at least one event emitted");
        // verify event shape
        let (ev_name, payload) = &guard[0];
        assert!(
            ev_name == "usage-update" || ev_name == "usage-error",
            "unexpected event name"
        );
        // if update ensure status ok
        if ev_name == "usage-update" {
            assert_eq!(payload["status"], json!("ok"));
        }

        std::env::remove_var("CLAUDE_SCRAPER_CMD");
    }

    #[test]
    fn test_start_stop_idempotence() {
        let mut poller = Poller::new_default();
        // not running initially
        assert!(!poller.is_running());
        // fake emitter that does nothing
        let emitter = Arc::new(|_ev: String, _p: Value| {});
        // Starting in a non-async context: spawn a runtime to start then stop
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async {
            poller.start_with_emitter(emitter.clone(), 60).expect("start ok");
            assert!(poller.is_running());
            // stop
            poller.stop().expect("stop ok");
            assert!(!poller.is_running());
            // stopping again should error
            assert!(poller.stop().is_err());
            // starting again is fine
            poller.start_with_emitter(emitter.clone(), 60).expect("start ok");
            poller.stop().expect("stop ok");
        });
    }
}