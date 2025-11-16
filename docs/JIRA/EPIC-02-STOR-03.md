# EPIC-02-STOR-03
Title: Scheduler and periodic collection
Epic: EPIC-02
Status: TODO

## Description
Add scheduling capability to run scraper every 5 minutes and collect usage data.

## Acceptance Criteria
- [ ] Implement scheduler using APScheduler or similar
- [ ] Configure 5-minute polling interval
- [ ] Add retry logic for failed scrapes
- [ ] Store results with timestamps