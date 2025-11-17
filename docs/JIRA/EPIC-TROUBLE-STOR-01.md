# EPIC-TROUBLE-STOR-01: Investigate Cloudflare Gate & Process Multiplication

## Status
🔴 **IN PROGRESS** - Investigation Phase

## Description
Investigate and resolve critical regression where Chrome windows trigger Cloudflare's anti-bot detection, causing scraper failures and runaway process multiplication.

## Problem Details

### Symptoms
1. **Cloudflare Gate Triggered**
   - Chrome window shows Cloudflare challenge page
   - Browser stuck, cannot proceed to Claude interface
   - Scraper unable to extract data

2. **Process Multiplication**
   - Error popups appear from failed scraper
   - Additional Chrome windows spawn
   - Each new window spawns its own scraper process
   - Exponential process growth pattern

### Likely Trigger
- Recent changes in EPIC-02-STOR-01 (profile cleanup work)
- Possible correlation with session/profile management changes

## Acceptance Criteria
- [ ] Root cause analysis completed and documented
- [ ] Identify what changed to trigger Cloudflare detection
- [ ] Identify why process multiplication occurs
- [ ] Identify all affected code paths
- [ ] Propose fix strategy with implementation plan
- [ ] Document prevention measures for future

## Investigation Areas

### 1. Cloudflare Detection Trigger
- [ ] Review Chrome profile changes (EPIC-02-STOR-01)
- [ ] Check user-agent and browser fingerprinting
- [ ] Examine undetected-chromedriver configuration
- [ ] Review Chrome flags and startup parameters
- [ ] Check for profile lock issues causing fresh profiles

### 2. Process Multiplication
- [ ] Review scraper error handling and restart logic
- [ ] Check Tauri polling service restart behavior
- [ ] Examine supervisor/monitoring process management
- [ ] Identify process lifecycle management gaps
- [ ] Check for race conditions in process spawning

### 3. Recent Changes Review
- [ ] Git diff from working state to current
- [ ] Review EPIC-02-STOR-01 commits (708da69, 27f9e8d, d58d658)
- [ ] Check profile cleanup implementation
- [ ] Review session manager changes

## Files to Examine
- src/scraper/claude_scraper.py - Main scraper logic
- src/scraper/session_manager.py - Session/profile handling
- src/scraper/supervisor.py - Process management (if exists)
- src/scraper/monitoring.py - Monitoring logic (if exists)
- src-tauri/src/polling.rs - Tauri polling service
- Recent commits: 708da69, 27f9e8d, d58d658

## Delegation
**Assigned To:** Project Research mode

**Research Tasks:**
1. Read and analyze all EPIC-02-STOR-01 related tickets
2. Examine codebase changes in recent commits
3. Use semantic search to find process management code
4. Identify Cloudflare detection triggers
5. Map out process lifecycle and spawning logic
6. Document findings with file references and line numbers
7. Propose root cause analysis and fix strategy

## Timeline
- Created: 2025-11-17
- Target Resolution: ASAP (P0)

## Notes
- This is blocking all scraper functionality
- May need to rollback recent changes if fix is not immediate
- Consider rate limiting or circuit breaker patterns for process spawning