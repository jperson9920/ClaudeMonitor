# EPIC-05-STOR-02

Title: Implement ProgressBar and ResetTimer UI components

Epic: [`EPIC-05`](docs/JIRA/EPIC-LIST.md:54)

Status: DONE

## Description
As a frontend developer I need reusable UI components for the progress bar and reset countdown so the dashboard shows usage percentage and time-until-reset consistently.

This implements:
- `src/components/ProgressBar.tsx`
- `src/components/ResetTimer.tsx`
- Unit tests for both components

ProgressBar accepts numeric usage (0-100) and optional thresholds; ResetTimer accepts ISO8601 `reset_time` or `raw_reset_text` and displays a human-friendly countdown or raw text when parsing fails.

## Acceptance Criteria
- [ ] `ProgressBar` props signature:
  - `interface ProgressBarProps { value: number; size?: 'sm'|'md'|'lg'; thresholds?: { warning: number; critical: number }; ariaLabel?: string }`
  - Renders a semantic progress element with `role="progressbar"` and ARIA attributes: `aria-valuenow`, `aria-valuemin=0`, `aria-valuemax=100`.
- [ ] `ResetTimer` props signature:
  - `interface ResetTimerProps { resetTimeISO?: string | null; rawResetText?: string | null }`
  - If `resetTimeISO` parseable, shows countdown "Resets in 12m" updating every 30s; else shows `rawResetText`.
- [ ] Unit tests:
  - `src/components/__tests__/ProgressBar.test.tsx` verifies color class at 50% and warning/critical thresholds.
  - `src/components/__tests__/ResetTimer.test.tsx` verifies ISO parsing and fallback to raw text.
- [ ] Documentation in `docs/JIRA/EPIC-05-FRONTEND.md` shows example imports and usage:
  - `import ProgressBar from 'src/components/ProgressBar';`
  - `import ResetTimer from 'src/components/ResetTimer';`

## Dependencies
- EPIC-05-STOR-01 (UsageDisplay integration)
- Research.md: UI requirements and accessibility notes (see `docs/Research.md:26-31`, `docs/JIRA/EPIC-LIST.md:56-60`)

## Tasks (1-3 hours each)
- [ ] Implement `src/components/ProgressBar.tsx` with props and ARIA attributes; include Tailwind classes and color thresholds (1.5h)
- [ ] Implement `src/components/ResetTimer.tsx` which accepts ISO string or raw text, uses `Intl.RelativeTimeFormat` or `date-fns` for formatting (1.5h)
  - If `date-fns` chosen, add to frontend `package.json` deps: `date-fns`.
- [ ] Write unit tests for both components (1.0h)
- [ ] Add example usage snippet to `docs/JIRA/EPIC-05-FRONTEND.md` (0.25h)

## Estimate
Total: 4.25 hours

## Research References
- UI requirements: `docs/JIRA/EPIC-LIST.md:54-61`
- Accessibility requirement for labels: `docs/JIRA/EPIC-LIST.md:57-60` and Research.md UI notes `docs/Research.md:26-31`

## Risks & Open Questions
- Risk: Choosing a date library increases bundle size; prefer `Intl.RelativeTimeFormat` for small dependency footprint.
- Open question: Desired refresh cadence for countdowns (30s suggested) — confirm with UX.