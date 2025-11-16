use serde_json::Value;
use std::fmt;
use std::process::Stdio;
use std::time::Duration;
use tokio::io::{AsyncReadExt, BufReader};
use tokio::process::Command;
use tokio::time::timeout;
use crate::resource::resolve_scraper_path;

/// Errors returned by the Scraper interface.
#[derive(Debug)]
pub enum ScraperError {
    Io(String),
    Timeout(String),
    JsonParse(String),
    Protocol(String),
    Execution(String),
}

impl fmt::Display for ScraperError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ScraperError::Io(s) => write!(f, "Io: {}", s),
            ScraperError::Timeout(s) => write!(f, "Timeout: {}", s),
            ScraperError::JsonParse(s) => write!(f, "JsonParse: {}", s),
            ScraperError::Protocol(s) => write!(f, "Protocol: {}", s),
            ScraperError::Execution(s) => write!(f, "Execution: {}", s),
        }
    }
}

impl From<std::io::Error> for ScraperError {
    fn from(e: std::io::Error) -> Self {
        ScraperError::Io(e.to_string())
    }
}

impl From<serde_json::Error> for ScraperError {
    fn from(e: serde_json::Error) -> Self {
        ScraperError::JsonParse(e.to_string())
    }
}

use serde::Deserialize;

/// Structured error messages emitted by the Python scraper to stderr.
#[derive(Debug, Deserialize)]
struct ScraperStderrError {
    error_code: String,
    message: String,
    details: Option<String>,
    timestamp: Option<String>,
    diagnostics: Option<serde_json::Value>,
}

/// Attempt to parse stderr content (JSON) and map to a ScraperError.
fn parse_stderr_error(stderr: &str) -> Option<ScraperError> {
    if stderr.trim().is_empty() {
        return None;
    }
    if let Ok(err) = serde_json::from_str::<ScraperStderrError>(stderr) {
        // Map well-known error codes to ScraperError variants.
        match err.error_code.as_str() {
            "session_required" => {
                Some(ScraperError::Execution(format!("session_required: {}", err.message)))
            }
            "session_expired" => {
                Some(ScraperError::Execution(format!("session_expired: {}", err.message)))
            }
            "navigation_failed" => Some(ScraperError::Timeout(format!("navigation failed: {}", err.message))),
            "manual_login_failed" => Some(ScraperError::Execution(format!("manual login failed: {}", err.message))),
            "timeout" => Some(ScraperError::Timeout(err.message)),
            "fatal" => Some(ScraperError::Execution(format!("fatal: {}", err.message))),
            _ => Some(ScraperError::Protocol(format!("scraper error: {}", err.message))),
        }
    } else {
        None
    }
}

/// Parse raw JSON produced by the scraper and validate basic schema
/// Expected top-level keys: "status" (string) and "components" (array)
pub fn parse_scraper_output(raw: &str) -> Result<Value, ScraperError> {
    let v: Value = serde_json::from_str(raw)?;
    // Basic schema validation
    if !v.get("status").map(|s| s.is_string()).unwrap_or(false) {
        return Err(ScraperError::Protocol(
            "missing or invalid 'status' field".to_string(),
        ));
    }
    if !v.get("components").map(|c| c.is_array()).unwrap_or(false) {
        return Err(ScraperError::Protocol(
            "missing or invalid 'components' array".to_string(),
        ));
    }
    Ok(v)
}

/// Spawn the scraper subprocess and return parsed JSON output.
/// - args: arguments passed to the scraper (e.g., --login, --check-session, --poll_once)
/// - timeout_secs: timeout for the entire operation (read + process) in seconds
///
/// Behavior notes:
/// - By default this invokes: python -m src.scraper.claude_scraper <args...>
/// - If environment variable CLAUDE_SCRAPER_CMD is present and starts with `python -c `
///   the remainder will be passed to `python -c <code>` (used by tests to simulate output).
pub async fn spawn_scraper(args: Vec<String>, timeout_secs: u64) -> Result<Value, ScraperError> {
    // Build command based on optional override
    if let Ok(override_cmd) = std::env::var("CLAUDE_SCRAPER_CMD") {
        // Support a simple test override pattern: "python -c <code>"
        if override_cmd.starts_with("python -c ") {
            let code = &override_cmd["python -c ".len()..];
            let mut cmd = Command::new("python");
            cmd.arg("-c").arg(code);
            cmd.stdout(Stdio::piped());
            cmd.stderr(Stdio::piped());

            let mut child = cmd.spawn().map_err(|e| ScraperError::Execution(e.to_string()))?;
            let stdout = child
                .stdout
                .take()
                .ok_or_else(|| ScraperError::Io("failed to capture stdout".to_string()))?;
            let mut reader = BufReader::new(stdout);
            let mut buf = String::new();

            let dur = Duration::from_secs(timeout_secs);
            let read_future = async {
                reader.read_to_string(&mut buf).await?;
                Ok::<(), std::io::Error>(())
            };

            match timeout(dur, read_future).await {
                Ok(r) => {
                    r.map_err(|e| ScraperError::Io(e.to_string()))?;
                }
                Err(_) => {
                    // timeout, try to kill process
                    let _ = child.kill().await;
                    return Err(ScraperError::Timeout(format!(
                        "scraper did not produce output in {}s",
                        timeout_secs
                    )));
                }
            }

            // Wait for process to exit (don't block forever)
            let wait_future = async { child.wait().await };
            match timeout(Duration::from_secs(5), wait_future).await {
                Ok(_) => {}
                Err(_) => {
                    let _ = child.kill().await;
                }
            }

            return parse_scraper_output(&buf);
        }
        // If override set but not supported pattern, return execution error
        return Err(ScraperError::Execution(
            "unsupported CLAUDE_SCRAPER_CMD format".to_string(),
        ));
    }

    // Resolve scraper path (bundled exe or dev script)
    let scraper_path = resolve_scraper_path()
        .map_err(|e| ScraperError::Execution(format!("resource resolution failed: {}", e)))?;
 
    // Build command depending on file type
    let mut cmd = if scraper_path
        .extension()
        .and_then(|s| s.to_str())
        .map(|s| s.eq_ignore_ascii_case("py"))
        .unwrap_or(false)
    {
        // Python script: execute via system python
        let mut c = Command::new("python");
        c.arg(
            scraper_path
                .to_str()
                .ok_or_else(|| ScraperError::Execution("scraper path contains invalid UTF-8".to_string()))?,
        );
        c.args(args.iter().map(|s| s.as_str()));
        c
    } else {
        // Bundled executable: run directly
        let mut c = Command::new(
            scraper_path
                .to_str()
                .ok_or_else(|| ScraperError::Execution("scraper path contains invalid UTF-8".to_string()))?,
        );
        c.args(args.iter().map(|s| s.as_str()));
        c
    };
 
    // Set working directory to the scraper binary/script directory when available
    if let Some(parent) = scraper_path.parent() {
        if parent.exists() {
            cmd.current_dir(parent);
        }
    }
 
    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());
 
    let mut child = cmd.spawn().map_err(|e| ScraperError::Execution(format!("failed to spawn scraper process: {}", e)))?;

    // Capture both stdout and stderr so we can parse structured errors emitted on stderr.
    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| ScraperError::Io("failed to capture stdout".to_string()))?;
    let stderr = child
        .stderr
        .take()
        .ok_or_else(|| ScraperError::Io("failed to capture stderr".to_string()))?;

    let mut out_reader = BufReader::new(stdout);
    let mut err_reader = BufReader::new(stderr);
    let mut out_buf = String::new();
    let mut err_buf = String::new();

    let dur = Duration::from_secs(timeout_secs);
    let read_future = async {
        // Read both streams to completion (may return quickly)
        out_reader.read_to_string(&mut out_buf).await?;
        err_reader.read_to_string(&mut err_buf).await?;
        Ok::<(), std::io::Error>(())
    };

    match timeout(dur, read_future).await {
        Ok(r) => {
            r.map_err(|e| ScraperError::Io(e.to_string()))?;
        }
        Err(_) => {
            // timeout, try to kill process
            let _ = child.kill().await;
            return Err(ScraperError::Timeout(format!(
                "scraper did not produce output in {}s",
                timeout_secs
            )));
        }
    }

    // Best-effort wait for child termination (short)
    let wait_future = async { child.wait().await };
    match timeout(Duration::from_secs(5), wait_future).await {
        Ok(_) => {}
        Err(_) => {
            let _ = child.kill().await;
        }
    }

    // If stdout is empty but stderr contains structured JSON, try to map that to a ScraperError.
    if out_buf.trim().is_empty() && !err_buf.trim().is_empty() {
        if let Some(mapped) = parse_stderr_error(&err_buf) {
            return Err(mapped);
        } else {
            // If stderr is non-empty but not structured, return execution error with stderr content.
            return Err(ScraperError::Execution(format!("scraper stderr: {}", err_buf.trim())));
        }
    }

    // Otherwise attempt to parse stdout JSON as before.
    parse_scraper_output(&out_buf)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_valid_output() {
        let raw = r#"{
            "status": "ok",
            "components": [],
            "scraped_at": "2025-01-01T00:00:00Z"
        }"#;
        let v = parse_scraper_output(raw).expect("should parse");
        assert_eq!(v["status"], "ok");
        assert!(v["components"].is_array());
    }

    #[test]
    fn test_parse_invalid_json() {
        let raw = r#"not a json"#;
        let err = parse_scraper_output(raw).unwrap_err();
        match err {
            ScraperError::JsonParse(_) => {}
            other => panic!("unexpected error: {:?}", other),
        }
    }

    #[test]
    fn test_parse_missing_fields() {
        let raw = r#"{"status":"ok"}"#;
        let err = parse_scraper_output(raw).unwrap_err();
        match err {
            ScraperError::Protocol(s) => {
                assert!(s.contains("components"));
            }
            other => panic!("unexpected error: {:?}", other),
        }
    }

    // Async test to verify timeout path using override helper
    // This test spawns a python -c that sleeps longer than timeout
    #[tokio::test]
    async fn test_spawn_scraper_timeout_override() {
        std::env::set_var(
            "CLAUDE_SCRAPER_CMD",
            "python -c \"import time; time.sleep(3); print('{\\\"status\\\":\\\"ok\\\",\\\"components\\\":[] }')\"",
        );
        let res = spawn_scraper(vec![], 1).await;
        assert!(matches!(res, Err(ScraperError::Timeout(_))));
        std::env::remove_var("CLAUDE_SCRAPER_CMD");
    }

    // Async test to verify successful override run
    #[tokio::test]
    async fn test_spawn_scraper_override_success() {
        std::env::set_var(
            "CLAUDE_SCRAPER_CMD",
            "python -c \"print('{\\\"status\\\":\\\"ok\\\",\\\"components\\\":[] }')\"",
        );
        let res = spawn_scraper(vec![], 5).await.expect("should succeed");
        assert_eq!(res["status"], "ok");
        std::env::remove_var("CLAUDE_SCRAPER_CMD");
    }
}