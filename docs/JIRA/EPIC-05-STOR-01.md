# EPIC-05-STOR-01

Title: Implement frontend UsageDisplay component and data model

Epic: [`EPIC-05`](docs/JIRA/EPIC-LIST.md:54)

Status: DONE

## Description
As a frontend developer, I need a React component that receives parsed usage JSON from the Rust backend and renders the three usage components (percentage, progress bar, reset timer, last_updated) so users can view current Claude usage at a glance.

This implements:
- `src/components/UsageDisplay.tsx`
- Types in `src/types/usage.ts` matching scraper JSON schema (components[], status, found_components)

UI must be accessible and accept props for `components: Component[]` and event handlers for manual refresh and manual login.

## Acceptance Criteria
- [ ] `src/types/usage.ts` exports interfaces:
  - `Component { id: string; name: string; usage_percent: number; tokens_used?: number; tokens_limit?: number; reset_time?: string | null; raw_reset_text?: string; last_updated: string; status: 'ok'|'partial'|'error' }`
  - `UsagePayload { components: Component[]; found_components: number; status: 'ok'|'partial'|'error'; diagnostics?: any }`
- [ ] `src/components/UsageDisplay.tsx` renders exactly three component rows (or fewer if `found_components < 3`) each with progress bar, percentage label, reset timer, and last_updated label.
- [ ] Component exposes props: `onRefresh(): void`, `onLogin(): void`.
- [ ] Accessibility: progress bars include `aria-valuenow`, `aria-valuemin=0`, `aria-valuemax=100` and labels readable by screen readers.
- [ ] Unit tests under `src/components/__tests__/UsageDisplay.test.tsx` mount the component with sample payload and assert DOM contains percentages and reset text.

## Dependencies
- EPIC-04 (backend commands to provide data)
- EPIC-02 (JSON schema in scraper/protocol.md)

## Tasks (1-4 hours)
- [ ] Add type definitions `src/types/usage.ts` (0.5h)
  - Exact exports: `export interface Component { ... } export interface UsagePayload { ... }`
- [ ] Implement `src/components/UsageDisplay.tsx` (1.5h)
  - Use Tailwind classes; example ProgressBar subcomponent may live in `src/components/ProgressBar.tsx`
  - Props: `payload: UsagePayload`, `onRefresh: () => void`, `onLogin: () => void`
- [ ] Add unit tests using React Testing Library `src/components/__tests__/UsageDisplay.test.tsx` (1.0h)
- [ ] Document frontend usage in `docs/JIRA/EPIC-05-FRONTEND.md` with example `window.__TAURI__.invoke('poll_usage_once')` usage and expected JSON (0.5h)

## Estimate
Total: 3.5 hours

## Research References
- EPIC-LIST UI requirements: `docs/JIRA/EPIC-LIST.md:54-61`
- Research.md: UI responsibilities and update frequency (lines 26-31, 67-76) [`docs/Research.md:26-31`, `docs/Research.md:67-76`]

## Risks & Open Questions
- Risk: Timezone handling for `reset_time` display — frontend must normalize ISO8601 to local time; decide format (short vs relative). Document in EPIC-05-FRONTEND.md.
- Open question: Should progress bars animate on update? Defer to UX decision.