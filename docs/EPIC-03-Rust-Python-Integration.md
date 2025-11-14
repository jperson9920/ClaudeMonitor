# EPIC-03: Rust-Python Integration

## Problem Statement
Integrate the Python web scraper (from EPIC-01) with the Tauri Rust backend (from EPIC-02) to enable the desktop application to poll Claude.ai usage data. This requires spawning Python subprocesses from Rust, parsing JSON output, managing state, and implementing error handling.

## Goal
Create a fully functional integration between the Rust backend and Python scraper that:
- Spawns Python scraper as a subprocess
- Parses JSON output from the scraper
- Manages scraper state (session validation, polling)
- Handles errors gracefully
- Implements automatic polling with configurable intervals
- Exposes Tauri commands for frontend interaction

## Success Criteria
- [ ] Rust can successfully spawn Python scraper
- [ ] JSON parsing works for both success and error responses
- [ ] Session check command works from frontend
- [ ] Manual login command works from frontend
- [ ] Polling command returns usage data to frontend
- [ ] Automatic polling runs every 5 minutes
- [ ] Error handling provides meaningful feedback
- [ ] State management prevents concurrent scraper runs

## Dependencies
- **Completed**: EPIC-01 (Python Scraper), EPIC-02 (Tauri App)
- **Requires**: Python 3.9+ installed on system

## Stories

### STORY-01: Python Process Spawning
**Description**: Implement Rust module for spawning and managing Python subprocess.

**Tasks**:
- Create `src-tauri/src/scraper.rs` module
- Implement `ScraperInterface` struct
- Add method to detect Python executable path
- Implement `spawn_python()` to run scraper script
- Add stdout/stderr capture
- Handle process exit codes

**Acceptance Criteria**:
- Can spawn Python process from Rust
- Captures stdout and stderr separately
- Returns exit code and output
- Works cross-platform (Windows/Mac/Linux)

---

### STORY-02: JSON Response Parsing
**Description**: Parse JSON output from Python scraper into Rust structures.

**Tasks**:
- Define `UsageData` Rust struct matching Python output
- Define `ErrorResponse` Rust struct
- Implement JSON parsing with serde
- Add validation for required fields
- Handle malformed JSON gracefully

**Acceptance Criteria**:
- Successfully parses success responses
- Successfully parses error responses
- Validates required fields exist
- Returns meaningful errors for invalid JSON

---

### STORY-03: Scraper Commands
**Description**: Implement Tauri commands for scraper operations.

**Tasks**:
- Implement `check_session()` command
- Implement `manual_login()` command
- Implement `poll_usage()` command
- Add command error handling
- Document command signatures

**Acceptance Criteria**:
- `check_session` verifies session file exists
- `manual_login` triggers login flow
- `poll_usage` returns usage data
- All commands have proper error handling
- Commands are async/non-blocking

---

### STORY-04: State Management
**Description**: Implement application state to manage scraper lifecycle.

**Tasks**:
- Create `AppState` struct
- Add `ScraperState` to track scraper status
- Implement Mutex for thread-safe state access
- Add methods to prevent concurrent scraper runs
- Track last poll time

**Acceptance Criteria**:
- State prevents multiple simultaneous polls
- State tracks scraper status
- Thread-safe state access
- Last poll timestamp is tracked

---

### STORY-05: Automatic Polling
**Description**: Implement background task for automatic polling every 5 minutes.

**Tasks**:
- Create polling background task with tokio
- Implement configurable polling interval
- Add start/stop polling commands
- Emit events to frontend on poll completion
- Handle polling errors without crashing

**Acceptance Criteria**:
- Polling runs every 5 minutes
- Frontend receives poll results via events
- Polling can be started/stopped
- Errors don't crash the polling loop
- Polling respects state locks

---

### STORY-06: Error Handling and Logging
**Description**: Comprehensive error handling and logging throughout integration.

**Tasks**:
- Add detailed logging to all scraper operations
- Implement error propagation to frontend
- Add retry logic for transient failures
- Log scraper output for debugging
- Create user-friendly error messages

**Acceptance Criteria**:
- All errors are logged with context
- Frontend receives clear error messages
- Retry logic handles transient failures
- Debug logs available for troubleshooting

---

### STORY-07: Integration Testing
**Description**: Test the full Rust-Python integration end-to-end.

**Tasks**:
- Create integration test suite
- Test successful scraper execution
- Test error scenarios (no Python, no session, etc.)
- Test concurrent request handling
- Verify cross-platform compatibility

**Acceptance Criteria**:
- Integration tests pass
- Error scenarios handled correctly
- No race conditions in concurrent requests
- Works on target platforms

## Technical Specifications

### Rust Structures

```rust
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

#[derive(Debug, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub status: String,
    pub error: String,
    pub message: String,
}

pub struct ScraperInterface {
    scraper_path: PathBuf,
    python_cmd: String,
}

pub struct AppState {
    scraper: Arc<Mutex<ScraperInterface>>,
    polling: Arc<Mutex<PollingState>>,
    last_poll: Arc<Mutex<Option<Instant>>>,
}
```

### Tauri Commands

```rust
#[tauri::command]
async fn check_session(state: State<'_, AppState>) -> Result<bool, String>

#[tauri::command]
async fn manual_login(state: State<'_, AppState>) -> Result<String, String>

#[tauri::command]
async fn poll_usage(state: State<'_, AppState>) -> Result<UsageData, String>

#[tauri::command]
async fn start_polling(app: AppHandle, state: State<'_, AppState>) -> Result<(), String>

#[tauri::command]
async fn stop_polling(state: State<'_, AppState>) -> Result<(), String>
```

### Event Emissions

```rust
// Emitted when automatic poll completes successfully
app.emit_all("usage-update", usage_data)?;

// Emitted when poll encounters error
app.emit_all("usage-error", error_message)?;

// Emitted for force refresh from system tray
app.emit_all("force-refresh", ())?;
```

## File Structure

```
src-tauri/src/
├── main.rs                 # Entry point, command handlers
├── scraper.rs              # Python process spawning
├── state.rs                # Application state management
└── polling.rs              # Background polling task
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Python not installed | High | Check for Python at startup, clear error message |
| Process spawn failure | Medium | Retry logic, detailed error logging |
| JSON parse errors | Medium | Robust error handling, schema validation |
| Concurrent access | Medium | Mutex-based state management |
| Polling crashes app | High | Error handling in polling loop, don't panic |

## Testing Strategy

### Unit Tests
- Test JSON parsing with various inputs
- Test Python path detection
- Test state management logic

### Integration Tests
- Test full scraper execution flow
- Test error scenarios
- Test concurrent requests

### Manual Testing
- Run manual login flow
- Verify automatic polling
- Test error conditions

## Performance Considerations

- Python subprocess overhead: ~1-2 seconds per poll
- JSON parsing: Negligible
- Polling interval: 5 minutes (configurable)
- Memory: Minimal (only holds latest data)

## Follow-up Epics
- EPIC-04: React UI Implementation with Real Data

## Notes
- Python must be in system PATH or specified explicitly
- Scraper directory is bundled with application
- Session data persists in app data directory
