# EPIC-09: Critical Bug Fixes

## Problem Statement
Critical production blockers were discovered after the initial deployment. These issues prevent expected application behavior (window sizing, scraper integration) and generate misleading error messages that confuse users and block regular use.

## Current State
- EPIC-01 through EPIC-04: COMPLETE (30 stories implemented)
- EPIC-05 (Window Controls) and EPIC-06 (Notifications): documented but NOT IMPLEMENTED
- Application is running but has critical bugs reported by users:
  - Window opens much larger than the configured 450x650px
  - Misleading "Python not installed" error after login, caused by scraper/Chrome session failures
  - Selenium/undetected_chromedriver reports: `SessionNotCreatedException: cannot connect to chrome`

## Goal
Resolve production-blocking defects so the app launches with correct window size, the scraper reliably creates Chrome sessions, and errors shown to users are accurate and actionable.

## Stories (not started)
- [ ] EPIC-09-STOR-03 — Fix Chrome Session Creation Errors (PRIORITY: Critical)
- [ ] EPIC-09-STOR-02 — Fix Misleading Python Error Message (PRIORITY: Critical)
- [ ] EPIC-09-STOR-01 — Fix Window Size on Launch (PRIORITY: Critical)

## Acceptance Criteria for Epic
- All three story acceptance criteria are met
- No regression in existing functionality (smoke tests pass)
- Updated documentation in docs/JIRA/ for tracking and audit
- Clear developer runbook for validating scraper and launcher behavior

## Priority
1. EPIC-09-STOR-03 (Fix Chrome connection) - CRITICAL BLOCKER  
2. EPIC-09-STOR-02 (Fix error messages) - HIGH  
3. EPIC-09-STOR-01 (Fix window size) - MEDIUM

## Notes
- Work should include small, testable changes with clear validation steps.
- Where the scraper is involved, add improved logging to distinguish interpreter missing vs runtime/Chrome issues.