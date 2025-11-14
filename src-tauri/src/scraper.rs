use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::{Command, Stdio};

/// Usage data response from Python scraper
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageData {
    pub status: String,
    pub usage_percent: f64,
    pub tokens_used: i64,
    pub tokens_limit: i64,
    pub tokens_remaining: i64,
    pub reset_time: Option<String>,
    pub last_updated: String,
}

/// Error response from Python scraper
#[derive(Debug, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub status: String,
    pub error: String,
    pub message: String,
}

/// Generic response that can be either success or error
#[derive(Debug, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ScraperResponse {
    Success(UsageData),
    Error(ErrorResponse),
}

/// Interface for spawning and managing Python scraper subprocess
pub struct ScraperInterface {
    scraper_path: PathBuf,
    python_cmd: String,
}

impl ScraperInterface {
    /// Create a new scraper interface
    ///
    /// # Arguments
    /// * `scraper_dir` - Path to directory containing claude_scraper.py
    pub fn new(scraper_dir: &str) -> Self {
        let scraper_path = PathBuf::from(scraper_dir);

        // Detect Python command (python3 on Unix, python on Windows)
        let python_cmd = if cfg!(windows) {
            "python".to_string()
        } else {
            "python3".to_string()
        };

        Self {
            scraper_path,
            python_cmd,
        }
    }

    /// Check if a valid session file exists
    pub fn has_valid_session(&self) -> Result<bool, String> {
        let session_file = self.scraper_path.join("chrome-profile/session.json");
        Ok(session_file.exists())
    }

    /// Perform manual login (spawns browser for user interaction)
    pub async fn manual_login(&self) -> Result<String, String> {
        let script_path = self.scraper_path.join("claude_scraper.py");

        if !script_path.exists() {
            return Err(format!(
                "Scraper script not found at: {}",
                script_path.display()
            ));
        }

        let output = Command::new(&self.python_cmd)
            .arg(&script_path)
            .arg("--login")
            .current_dir(&self.scraper_path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .map_err(|e| format!("Failed to spawn Python process: {}", e))?;

        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let data: serde_json::Value = serde_json::from_str(&stdout)
                .map_err(|e| format!("Failed to parse JSON: {}\nOutput: {}", e, stdout))?;

            if data["status"] == "success" {
                Ok("Login successful".to_string())
            } else {
                Err(format!(
                    "Login failed: {}",
                    data["message"].as_str().unwrap_or("Unknown error")
                ))
            }
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            Err(format!("Python script failed:\n{}", stderr))
        }
    }

    /// Poll usage data from Claude.ai
    pub async fn poll_usage(&self) -> Result<UsageData, String> {
        let script_path = self.scraper_path.join("claude_scraper.py");

        if !script_path.exists() {
            return Err(format!(
                "Scraper script not found at: {}",
                script_path.display()
            ));
        }

        let output = Command::new(&self.python_cmd)
            .arg(&script_path)
            .current_dir(&self.scraper_path)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .map_err(|e| format!("Failed to spawn Python process: {}", e))?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        // Log stderr for debugging (contains scraper logs)
        if !stderr.is_empty() {
            eprintln!("Scraper logs:\n{}", stderr);
        }

        if output.status.success() {
            // Parse JSON response
            let response: ScraperResponse = serde_json::from_str(&stdout).map_err(|e| {
                format!(
                    "Failed to parse JSON: {}\nOutput: {}\nStderr: {}",
                    e, stdout, stderr
                )
            })?;

            match response {
                ScraperResponse::Success(data) => Ok(data),
                ScraperResponse::Error(err) => Err(format!("{}: {}", err.error, err.message)),
            }
        } else {
            Err(format!(
                "Python script failed with exit code: {}\nStderr: {}",
                output.status, stderr
            ))
        }
    }

    /// Get the path to the scraper directory
    pub fn scraper_path(&self) -> &PathBuf {
        &self.scraper_path
    }

    /// Get the Python command being used
    pub fn python_cmd(&self) -> &str {
        &self.python_cmd
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scraper_interface_creation() {
        let scraper = ScraperInterface::new("./scraper");
        assert_eq!(scraper.scraper_path(), &PathBuf::from("./scraper"));
    }

    #[test]
    fn test_python_command_detection() {
        let scraper = ScraperInterface::new("./scraper");

        if cfg!(windows) {
            assert_eq!(scraper.python_cmd(), "python");
        } else {
            assert_eq!(scraper.python_cmd(), "python3");
        }
    }

    #[test]
    fn test_usage_data_deserialization() {
        let json = r#"{
            "status": "success",
            "usage_percent": 45.2,
            "tokens_used": 39856,
            "tokens_limit": 88000,
            "tokens_remaining": 48144,
            "reset_time": "2025-11-15T19:30:00Z",
            "last_updated": "2025-11-14T16:05:23Z"
        }"#;

        let data: UsageData = serde_json::from_str(json).unwrap();
        assert_eq!(data.status, "success");
        assert_eq!(data.usage_percent, 45.2);
        assert_eq!(data.tokens_used, 39856);
    }

    #[test]
    fn test_error_response_deserialization() {
        let json = r#"{
            "status": "error",
            "error": "session_required",
            "message": "No saved session found. Please run manual_login first."
        }"#;

        let response: ErrorResponse = serde_json::from_str(json).unwrap();
        assert_eq!(response.status, "error");
        assert_eq!(response.error, "session_required");
    }
}
