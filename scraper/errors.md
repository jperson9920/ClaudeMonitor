# Error Codes and Diagnostics Schema

**Story:** EPIC-08-STOR-02  
**Created:** 2025-11-16  
**Status:** Structured error reporting for Python scraper and Rust backend

## Error Codes

The scraper and backend use standardized error codes for consistent error handling across layers.

### Canonical Error Codes

- `session_required`: No valid session found, manual login required
- `session_expired`: Session exists but expired (>7 days old), re-login needed
- `navigation_failed`: Failed to navigate to usage page
- `extraction_failed`: Could not extract usage data from DOM
- `cloudflare_detected`: Cloudflare challenge detected and not automatically resolved
- `timeout`: Operation exceeded timeout (default 30s)
- `fatal`: Unrecoverable error (e.g., Python interpreter crash, invalid arguments)

## JSON Schema

All errors emitted to stderr follow this schema:

```json
{
  "error_code": "string (required, one of the codes above)",
  "message": "string (required, human-readable error description)",
  "details": "string (optional, additional context)",
  "timestamp": "string (required, ISO8601 UTC format)",
  "attempts": "number (optional, retry attempts made)",
  "diagnostics": {
    "url": "string (optional, URL where error occurred)",
    "status_code": "number (optional, HTTP status code if applicable)",
    "retries": "number (optional, number of retries attempted)"
  }
}
```

## Example Error Objects

### Session Required
```json
{
  "error_code": "session_required",
  "message": "No valid session found. Manual login required.",
  "timestamp": "2025-11-16T05:30:00Z",
  "diagnostics": {
    "session_file": "scraper/chrome-profile/session.json",
    "exists": false
  }
}
```

### Navigation Failed
```json
{
  "error_code": "navigation_failed",
  "message": "Failed to navigate to usage page after 3 attempts",
  "details": "Connection timeout",
  "timestamp": "2025-11-16T05:30:00Z",
  "attempts": 3,
  "diagnostics": {
    "url": "https://claude.ai/settings/usage",
    "retries": 3
  }
}
```

### Timeout
```json
{
  "error_code": "timeout",
  "message": "Operation exceeded 30s timeout",
  "timestamp": "2025-11-16T05:30:00Z",
  "diagnostics": {
    "timeout_ms": 30000,
    "elapsed_ms": 31500
  }
}
```

## Rust Error Mapping

The Rust backend (`src-tauri/src/scraper.rs`) parses stderr JSON and maps to `ScraperError` enum:

- `session_required` → `ScraperError::SessionRequired`
- `session_expired` → `ScraperError::SessionExpired`
- `timeout` → `ScraperError::Timeout(message)`
- `navigation_failed` → `ScraperError::NavigationFailed(message)`
- `extraction_failed` → `ScraperError::ExtractionFailed(message)`
- `cloudflare_detected` → `ScraperError::CloudflareDetected`
- `fatal` → `ScraperError::Fatal(message)`
- Unknown codes → `ScraperError::Protocol(message)`

## Security Considerations

**CRITICAL:** Diagnostics must NOT contain sensitive data:
- ❌ Cookies, session tokens, authentication headers
- ❌ Full HTML content with user data
- ❌ Personal identifiable information (PII)
- ✅ URLs (sanitized)
- ✅ HTTP status codes
- ✅ Retry counts and timing
- ✅ File paths (relative, not absolute with usernames)

## Logging Format

Errors are logged to `scraper/scraper.log` in two formats:

1. **Human-readable** (INFO/WARNING/ERROR level):
```
2025-11-16T05:30:00Z - scraper - ERROR - [navigation_failed] Failed to navigate to usage page after 3 attempts
```

2. **Structured JSON** (for log aggregators):
```
2025-11-16T05:30:00Z - scraper - ERROR - {"error_code": "navigation_failed", "message": "...", ...}
```

## Usage Examples

### Python (scraper/claude_scraper.py)
```python
def emit_error(error_code: str, message: str, details: str = None, diagnostics: dict = None):
    error_obj = {
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if details:
        error_obj["details"] = details
    if diagnostics:
        # Sanitize diagnostics before emitting
        error_obj["diagnostics"] = sanitize_diagnostics(diagnostics)

    print(json.dumps(error_obj), file=sys.stderr)
    logger.error(f"[{error_code}] {message}")
```

### Rust (src-tauri/src/scraper.rs)
```rust
fn parse_stderr_error(stderr: &str) -> Option<ScraperError> {
    if let Ok(err) = serde_json::from_str::<ScraperStderrError>(stderr) {
        match err.error_code.as_str() {
            "session_required" => Some(ScraperError::SessionRequired),
            "timeout" => Some(ScraperError::Timeout(err.message)),
            _ => Some(ScraperError::Protocol(err.message)),
        }
    } else {
        None
    }
}
```

## References

- EPIC-08-STOR-02: Structured error codes story
- Research.md: Error handling requirements
- scraper/retry_handler.py: Retry logic integration