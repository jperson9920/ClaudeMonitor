# EPIC-TROUBLE: Critical Cloudflare Gate & Process Multiplication Issue

## Status
🔴 **CRITICAL** - Active Investigation Required

## Overview
A critical regression has occurred where Chrome windows are triggering Cloudflare's anti-bot gate, causing the scraper to fail and spawn multiple Chrome instances in a runaway process multiplication loop.

## Problem Statement
1. Chrome window gets stuck on Cloudflare challenge page
2. Scraper cannot proceed, generates error popups
3. System spawns additional Chrome windows with their own scrapers
4. Process multiplication creates cascading failures

## Objectives
- Identify root cause of Cloudflare gate triggering
- Determine why process multiplication is occurring
- Implement fix to prevent both issues
- Add safeguards against runaway process creation

## Stories
- [EPIC-TROUBLE-STOR-01](./EPIC-TROUBLE-STOR-01.md) - Investigate and resolve Cloudflare gate & process multiplication
- [EPIC-TROUBLE-STOR-02](./EPIC-TROUBLE-STOR-02.md) - Implement P0 conservative mitigations to prevent process multiplication
- [EPIC-TROUBLE-STOR-03](./EPIC-TROUBLE-STOR-03.md) - Session validation failure ("relogin_failed") blocking automated usage extraction
- [EPIC-TROUBLE-STOR-04](./EPIC-TROUBLE-STOR-04.md) - Live run: browser closed early, erroneous 568% extraction, UI not updated
- [EPIC-TROUBLE-STOR-05](./EPIC-TROUBLE-STOR-05.md) - Remediation tasks: session checks, parser fixes, logging, tests

## Timeline
- Created: 2025-11-17
- Priority: P0 (Critical)

## Dependencies
- Review EPIC-02-STOR-01 changes (likely trigger point)
- Examine scraper process management code
- Review Chrome profile and session handling

## Success Criteria
- [ ] Root cause identified and documented
- [ ] Cloudflare gate no longer triggered
- [ ] Process multiplication eliminated
- [ ] Safeguards implemented to prevent recurrence