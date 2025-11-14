# EPIC-01: Python Web Scraper Foundation

## Problem Statement
Build a reliable Python-based web scraper that can authenticate to Claude.ai and extract usage metrics from the settings/usage page. This scraper must bypass Cloudflare protection using undetected-chromedriver and provide a JSON interface for integration with the desktop widget.

## Goal
Create a standalone Python scraper that:
- Performs one-time manual login with session persistence
- Navigates to claude.ai/settings/usage
- Extracts usage metrics (tokens used, limit, percentage, reset time)
- Outputs structured JSON data
- Handles errors gracefully with retry logic

## Success Criteria
- [ ] Scraper successfully bypasses Cloudflare protection (85-95% success rate)
- [ ] Manual login process saves session for future use
- [ ] Automated polling works with saved session
- [ ] Accurate data extraction from DOM
- [ ] Clean JSON output for downstream consumption
- [ ] Comprehensive error handling and logging

## Stories

### STORY-01: Project Structure and Dependencies
**Description**: Set up the Python project structure with required dependencies and configuration files.

**Tasks**:
- Create scraper directory structure
- Create requirements.txt with undetected-chromedriver and selenium
- Set up virtual environment configuration
- Create .gitignore for Python artifacts

**Acceptance Criteria**:
- requirements.txt exists with correct dependencies
- Directory structure is clean and organized
- Virtual environment can be created and activated

---

### STORY-02: Chrome Driver Configuration
**Description**: Implement Chrome driver initialization with anti-detection measures and session persistence.

**Tasks**:
- Create ClaudeUsageScraper class skeleton
- Implement create_driver() method with anti-detection options
- Configure browser profile for session persistence
- Add proper logging configuration

**Acceptance Criteria**:
- Chrome driver initializes successfully
- Browser profile directory is created
- Anti-detection measures are properly configured
- Logging works to both file and stderr

---

### STORY-03: Manual Login Flow
**Description**: Implement one-time manual login process with session saving.

**Tasks**:
- Implement manual_login() method
- Add user instructions for login process
- Implement save_session() to persist cookies
- Add session validation

**Acceptance Criteria**:
- Browser opens to claude.ai
- User can complete login manually
- Session cookies are saved to disk
- Session metadata includes timestamp

---

### STORY-04: Session Management
**Description**: Implement session loading and validation for automated polling.

**Tasks**:
- Implement load_session() method
- Add session age validation (7 day expiry)
- Implement check_session_valid() to verify authentication
- Handle session expiry gracefully

**Acceptance Criteria**:
- Saved sessions can be loaded successfully
- Expired sessions are detected and reported
- Session validation checks for login redirects
- Clear error messages for session issues

---

### STORY-05: Page Navigation
**Description**: Implement navigation to the usage page with proper wait conditions.

**Tasks**:
- Implement navigate_to_usage_page() method
- Add WebDriverWait for page load
- Verify correct URL after navigation
- Handle navigation failures

**Acceptance Criteria**:
- Successfully navigates to claude.ai/settings/usage
- Waits for page to fully load
- Detects navigation failures
- Returns appropriate error status

---

### STORY-06: Data Extraction
**Description**: Extract usage metrics from the DOM using multiple fallback strategies.

**Tasks**:
- Implement extract_usage_data() with JavaScript execution
- Create _parse_extracted_data() for structured output
- Implement _parse_plain_text() as fallback
- Extract: usage_percent, tokens_used, tokens_limit, reset_time

**Acceptance Criteria**:
- Primary extraction strategy works via JavaScript
- Fallback text extraction handles edge cases
- All required fields are extracted
- Data is properly typed and formatted

---

### STORY-07: Main Polling Function
**Description**: Implement the main polling function that orchestrates the entire scraping process.

**Tasks**:
- Implement poll_usage() method
- Integrate navigation, validation, and extraction
- Add comprehensive error handling
- Return structured JSON responses

**Acceptance Criteria**:
- poll_usage() executes full workflow
- Errors are caught and returned as JSON
- Success responses include all metrics
- Browser cleanup happens properly

---

### STORY-08: CLI Interface
**Description**: Create command-line interface for standalone testing.

**Tasks**:
- Implement main() entry point
- Add argparse for --login flag
- Add --profile-dir argument
- Output JSON to stdout, logs to stderr

**Acceptance Criteria**:
- python claude_scraper.py --login performs manual login
- python claude_scraper.py polls usage with saved session
- JSON output is valid and parseable
- Exit codes indicate success/failure

---

### STORY-09: Testing and Validation
**Description**: Create tests and validate the scraper works end-to-end.

**Tasks**:
- Create test_scraper.py with unit tests
- Test session management functions
- Test data extraction with mock data
- Perform manual end-to-end test

**Acceptance Criteria**:
- Unit tests pass for all methods
- Manual login workflow completes successfully
- Automated polling returns valid data
- Error scenarios are handled gracefully

## Technical Specifications

### Dependencies
```
undetected-chromedriver>=3.5.0
selenium>=4.10.0
```

### File Structure
```
scraper/
├── claude_scraper.py          # Main scraper implementation
├── requirements.txt            # Python dependencies
├── test_scraper.py            # Unit tests
├── chrome-profile/            # Browser profile (gitignored)
└── scraper.log                # Log file (gitignored)
```

### JSON Output Format
```json
{
  "status": "success",
  "usage_percent": 45.2,
  "tokens_used": 39856,
  "tokens_limit": 88000,
  "tokens_remaining": 48144,
  "reset_time": "2025-11-15T19:30:00Z",
  "last_updated": "2025-11-14T16:05:23Z"
}
```

### Error Response Format
```json
{
  "status": "error",
  "error": "error_code",
  "message": "Human readable error message"
}
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cloudflare detection | High | Use undetected-chromedriver in headed mode |
| DOM structure changes | Medium | Multiple extraction strategies with fallbacks |
| Session expiry | Low | 7-day expiry with re-login prompt |
| Rate limiting | Low | Reasonable polling intervals (5+ minutes) |

## Dependencies on Other Epics
None - This is the foundation epic.

## Follow-up Epics
- EPIC-02: Tauri Desktop Application Setup
- EPIC-03: Rust Backend Integration
- EPIC-04: React Frontend UI
