# EPIC-TROUBLE-STOR-01: Investigate Cloudflare Gate & Process Multiplication

## Status
🔴 IN PROGRESS — Investigation completed; mitigation & fix plan proposed

## Executive summary
Recent profile-lock cleanup changes (EPIC-02-STOR-01) introduced an aggressive cross-process kill + lockfile removal behavior that races with Chrome startup. This increases profile/session volatility and leads to Cloudflare anti-bot challenges. The scraper then fails, and supervising components (supervisor and poller) repeatedly restart scraper subprocesses, producing exponential Chrome window/process multiplication.

This ticket documents root cause evidence, why Cloudflare is triggered now, how process multiplication occurs, and a prioritized, actionable fix plan the next engineer can implement.

## Root cause (evidence)
- Aggressive cleanup function and integration:
  - cleanup implementation: [`src/scraper/claude_scraper.py:99-158`](src/scraper/claude_scraper.py:99-158)
  - Called before driver creation: [`src/scraper/claude_scraper.py:167-181`](src/scraper/claude_scraper.py:167-181)
  - Called on exit/finally: [`src/scraper/claude_scraper.py:596-616`](src/scraper/claude_scraper.py:596-616) and during manual-login cancel: [`src/scraper/claude_scraper.py:340-373`](src/scraper/claude_scraper.py:340-373)
- Supervisor/poller restart behavior that re-invokes cleanup on each child failure:
  - supervisor restart loop & cleanup: [`src/scraper/supervisor.py:52-99`](src/scraper/supervisor.py:52-99)
  - Tauri poller spawns scraper periodically: [`src-tauri/src/polling.rs:69-85`](src-tauri/src/polling.rs:69-85)
- Rust spawn logic: child timeout and kill may not reliably reap Chrome child trees:
  - spawn/timeout & kill behavior: [`src-tauri/src/scraper.rs:221-249`](src-tauri/src/scraper.rs:221-249)

## Why Cloudflare gate is triggered now
- The cleanup removes lockfiles or kills processes while Chrome may be mid-start (race). This leads to:
  - Scraper launching Chrome with a fresh/partial profile or failing to restore valid cookies (see session restore logic: [`src/scraper/session_manager.py:129-166`](src/scraper/session_manager.py:129-166))
  - Browser fingerprint/session flux causes Cloudflare to present an anti-bot challenge page. Scraper navigation/validation then times out or detects invalid session and exits with error.
- create_driver uses a persistent profile (`user-data-dir`) which, when mutated mid-start, causes the observed behavior: [`src/scraper/claude_scraper.py:183-206`](src/scraper/claude_scraper.py:183-206)

## How process multiplication happens
- Failure loop:
  1. Scraper spawns Chrome → Chrome hits Cloudflare challenge or startup error.
  2. Python scraper exits non-zero (or times out); supervisor/poller detect failure and schedule restart.
  3. cleanup_profile_locks is called (may kill processes by profile cmdline), but can leave orphaned Chrome children or kill the wrong process if racing with a fresh start.
  4. New restart spawns additional Chrome instances while previous nodes are still present → multiple Chrome instances accumulate. Concurrent supervisors/pollers or overlapping retry logic amplify this.
- Code paths:
  - Supervisor restart/backoff loop and cleanup: [`src/scraper/supervisor.py:66-99`](src/scraper/supervisor.py:66-99)
  - Poller spawn tick and spawn_scraper call: [`src-tauri/src/polling.rs:71-85`](src-tauri/src/polling.rs:71-85)
  - Rust spawn kill semantics that kill the direct child but may not kill grandchildren (Chrome): [`src-tauri/src/scraper.rs:232-249`](src-tauri/src/scraper.rs:232-249)

## Proposed fix strategy (prioritized, actionable)
P0 — Immediate conservative mitigations (apply ASAP)
1. Make cleanup_profile_locks conservative:
   - Only remove lockfiles or kill processes if they are confirmed zombies (age threshold e.g., >30s) OR when no profile owner marker exists.
   - Avoid unconditional pre-create cleanup. See pre-create call: [`src/scraper/claude_scraper.py:167-181`](src/scraper/claude_scraper.py:167-181)
   - File to edit: [`src/scraper/claude_scraper.py:99-158`](src/scraper/claude_scraper.py:99-158)
2. Add circuit-breaker in supervisor/poller:
   - If `consecutive_failures >= critical_after`, stop auto-restart and set health/alert state instead of continuous spawning.
   - Files to edit: [`src/scraper/supervisor.py:66-99`](src/scraper/supervisor.py:66-99) and [`src-tauri/src/polling.rs:71-95`](src-tauri/src/polling.rs:71-95)
3. Gate post-quit cleanup behind owner-check or config flag to avoid mutating profile while other instances may be active.

P1 — Short-term improvements (1–2 days)
1. Profile ownership lock:
   - Implement `profile_owner.pid` or `profile.lock` inside profile dir when a scraper run starts; clear on clean exit.
   - All other processes must wait/backoff if owner present.
   - Integrate in create_driver start/finally and supervisor spawn checks.
   - Files: [`src/scraper/claude_scraper.py`], [`src/scraper/supervisor.py`], [`src-tauri/src/polling.rs`]
2. Improve cleanup to kill process trees via psutil's parent/children traversal and use `create_time()` to avoid killing recently-started processes.

P2 — Medium-term robustness (1+ days)
1. Add explicit Cloudflare detection in `navigate_to_usage` and emit `cloudflare_detected` structured error; map in Rust to long-backoff/manual intervention.
   - Files: [`src/scraper/claude_scraper.py` navigate_to_usage], [`src-tauri/src/scraper.rs:56-76`](src-tauri/src/scraper.rs:56-76)
2. Ensure Rust `spawn_scraper` kills full process tree on timeout (platform-specific approaches).
   - File: [`src-tauri/src/scraper.rs:232-249`](src-tauri/src/scraper.rs:232-249)
3. Add logging/metrics for pid, owner, spawn timestamps to aid RCA and monitoring.

## Acceptance tests / verification
- Unit/integration tests to simulate:
  - Race where cleanup runs during Chrome startup; assert it waits and does not kill fresh instances.
  - spawn_scraper timeout leaves no orphan Chrome processes.
  - Poller circuit-breaker prevents repeated restarts after repeated `cloudflare_detected`.
- Manual verification:
  - Reproduce failing scenario with Cloudflare challenge and confirm poller/supervisor stop auto-restarts and require manual intervention.

## Acceptance criteria (ticket)
- [ ] Cleanup no longer kills legitimate Chrome instances during startup (unit/integration verified)
- [ ] Poller and supervisor do not create runaway Chrome process multiplication under error conditions
- [ ] Cloudflare challenge is detected as `cloudflare_detected` and triggers appropriate backoff/manual workflow
- [ ] Profile ownership lock prevents concurrent processes using same profile

## Next actions (owner: Project Research / Engineering)
1. Apply P0 conservative changes immediately (safest, low-risk).
2. Implement profile_owner lock and improved cleanup (P1).
3. Implement Cloudflare error code and robust kill semantics (P2).
4. Add integration tests that simulate races and orphaned processes.

## References (quick jump links)
- [`src/scraper/claude_scraper.py:99-158`](src/scraper/claude_scraper.py:99-158) — cleanup_profile_locks implementation
- [`src/scraper/claude_scraper.py:167-181`](src/scraper/claude_scraper.py:167-181) — pre-create cleanup call
- [`src/scraper/claude_scraper.py:596-616`](src/scraper/claude_scraper.py:596-616) — post-quit cleanup in finally
- [`src/scraper/session_manager.py:79-124`](src/scraper/session_manager.py:79-124) — validate_session heuristics
- [`src/scraper/supervisor.py:52-99`](src/scraper/supervisor.py:52-99) — supervisor restart & cleanup logic
- [`src-tauri/src/polling.rs:69-85`](src-tauri/src/polling.rs:69-85) — poller spawns scraper periodically
- [`src-tauri/src/scraper.rs:221-249`](src-tauri/src/scraper.rs:221-249) — spawn_scraper timeout / kill handling

## Notes
- This document is intended to be directly actionable by the engineer tasked with implementing fixes. The short (P0) mitigations are intentionally conservative to reduce risk and should be applied first.
- If an immediate rollback is required, disable pre-create/post-quit cleanup calls and pause supervisor/poller restarts until a safe change is deployed.
