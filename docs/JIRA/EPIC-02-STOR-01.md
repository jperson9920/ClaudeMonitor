# EPIC-02-STOR-01: Chrome Session Connection Fix

## Status
**RESOLVED** - Fix implemented and ready for testing

## Root Cause Analysis

### Symptom
`
selenium.common.exceptions.SessionNotCreatedException: Message: session not created: 
cannot connect to chrome at 127.0.0.1:<random-port>
`

### Investigation Timeline
1. **Evidence discovered**: Lockfile present in scraper/chrome-profile/ directory
2. **Error location**: src/scraper/claude_scraper.py:176 during uc.Chrome() instantiation
3. **Root cause**: Chrome locks user-data-dir on startup. When previous instances crash or don't exit cleanly, they leave lock files that prevent new Chrome instances from using the same profile.

### Technical Details
- **Primary issue**: Zombie Chrome/chromedriver processes holding profile locks
- **Secondary issue**: Stale lock files (lockfile, SingletonLock, SingletonSocket, SingletonCookie)
- **Port behavior**: Each chromedriver attempt uses random remote-debugging-port, but connection fails because Chrome can't start with locked profile

## Solution Implemented

### Changes Made

1. **Added cleanup_profile_locks() function** (src/scraper/claude_scraper.py:98-157)
   - Kills zombie Chrome/chromedriver processes using profile directory
   - Removes stale lock files from profile directory
   - Uses psutil for robust process enumeration and termination
   - Gracefully degrades if psutil not available

2. **Integrated cleanup in create_driver()** (src/scraper/claude_scraper.py:176)
   - Calls cleanup_profile_locks(profile_path) before attempting uc.Chrome()
   - Ensures clean state before each driver creation

3. **Added psutil dependency** (src/scraper/requirements.txt:10)
   - psutil>=5.9.0 for cross-platform process management

### Code Changes Summary

**File: src/scraper/claude_scraper.py**
- Lines 98-157: New cleanup_profile_locks() function
- Line 176: Added cleanup call in create_driver()

**File: src/scraper/requirements.txt**
- Line 10: Added psutil>=5.9.0

## Testing Plan

### Manual Verification Steps
1. Install dependencies: pip install -r src/scraper/requirements.txt
2. Run scraper: python -m src.scraper.claude_scraper --poll_once
3. Verify:
   - No "cannot connect to chrome" errors
   - Chrome launches successfully
   - If logged in: extraction completes, JSON output to stdout
   - If logged out: manual login flow triggers
   - No zombie Chrome/chromedriver processes after exit
   - Lock files removed from scraper/chrome-profile/

### Expected Behavior
- **First run**: May require manual login if session expired
- **Subsequent runs**: Reuses session successfully without connection errors
- **After crashes**: Cleanup function removes locks, allowing next run to succeed

## Risk Assessment
- **Low risk**: Changes are additive and defensive
- **Graceful degradation**: Works without psutil (logs warning, skips process cleanup)
- **Reversible**: Can be rolled back by removing cleanup call

## Acceptance Criteria Status
-  Root cause identified (profile locking from zombie processes/stale lock files)
-  Minimal fix implemented (cleanup function + integration point)
-  Dependencies added (psutil in requirements.txt)
-  Testing pending (requires Chrome + potential manual login)
-  JIRA docs updated (this document)

## Next Steps
1. **Immediate**: Commit changes with reference to EPIC-02-STOR-01
2. **Verification**: Run manual test with Chrome available
3. **Long-term monitoring**: Track if issue recurs in production

## Implementation Reference
- **Commit ID**: (Pending - see git commit below)
- **Files modified**: 
  - src/scraper/claude_scraper.py (function + integration)
  - src/scraper/requirements.txt (psutil dependency)

---
**Updated**: 2025-11-16 13:21:26  
**Resolution**: Implemented profile lock cleanup mechanism  
**Tested**: Manual testing required (Chrome automation with potential login)
