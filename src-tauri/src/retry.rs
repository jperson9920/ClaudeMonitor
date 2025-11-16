use serde::{Deserialize, Serialize};
use std::time::Duration;
use tokio::time::sleep;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetryPolicy {
    pub initial_delay_ms: u64,
    pub multiplier: f64,
    pub max_attempts: u32,
    pub max_delay_ms: u64,
}

impl Default for RetryPolicy {
    fn default() -> Self {
        Self {
            initial_delay_ms: 1000,
            multiplier: 2.0,
            max_attempts: 4,
            max_delay_ms: 60000,
        }
    }
}

/// Retry an async operation with exponential backoff according to `policy`.
/// The operation returns Result<T, E>. If all attempts fail the last Err(E) is returned.
/// E must implement Display to make log messages readable.
pub async fn retry_async<F, Fut, T, E>(
    policy: &RetryPolicy,
    mut operation: F,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = Result<T, E>>,
    E: std::fmt::Display,
{
    let mut attempt: u32 = 0;
    let mut delay_ms = policy.initial_delay_ms;

    loop {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) => {
                attempt += 1;
                if attempt >= policy.max_attempts {
                    // return last error
                    return Err(e);
                }

                log::warn!(
                    "Retry {}/{} after {}ms: {}",
                    attempt,
                    policy.max_attempts,
                    delay_ms,
                    e
                );

                sleep(Duration::from_millis(delay_ms)).await;
                // compute next delay with multiplier and cap
                let next = (delay_ms as f64 * policy.multiplier) as u64;
                delay_ms = std::cmp::min(next, policy.max_delay_ms);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Arc, Mutex};
    use tokio::time::Instant;

    #[tokio::test]
    async fn test_retry_async_succeeds_after_retries() {
        let policy = RetryPolicy {
            initial_delay_ms: 10,
            multiplier: 2.0,
            max_attempts: 4,
            max_delay_ms: 1000,
        };

        // Simulate an operation that fails twice then succeeds.
        let state = Arc::new(Mutex::new(0));
        let s2 = state.clone();
        let op = move || {
            let s = s2.clone();
            async move {
                let mut guard = s.lock().unwrap();
                *guard += 1;
                let attempt = *guard;
                if attempt < 3 {
                    Err(format!("transient failure #{attempt}"))
                } else {
                    Ok("success")
                }
            }
        };

        let res = retry_async(&policy, op).await;
        assert!(res.is_ok());
        assert_eq!(res.unwrap(), "success");
        let final_attempts = *state.lock().unwrap();
        assert!(final_attempts >= 3);
    }

    #[tokio::test]
    async fn test_retry_async_gives_up() {
        let policy = RetryPolicy {
            initial_delay_ms: 5,
            multiplier: 2.0,
            max_attempts: 3,
            max_delay_ms: 100,
        };

        // Always fail
        let op = || async { Err("always fail".to_string()) };

        let start = Instant::now();
        let res = retry_async(&policy, op).await;
        assert!(res.is_err());
        // Ensure some time has passed (>= sum of delays roughly)
        assert!(start.elapsed().as_millis() >= 5);
    }
}