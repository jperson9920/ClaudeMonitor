# EPIC-04: React UI Implementation with Real Data

## Problem Statement
Implement the complete React UI that displays real-time Claude.ai usage data from the integrated Rust-Python backend. Transform the placeholder UI into a fully functional desktop widget that shows usage metrics, alerts, and provides user interaction for login and manual refresh.

## Goal
Create a production-ready user interface that:
- Displays real-time usage data (percentage, tokens, reset time)
- Provides visual feedback with progress bars and alerts
- Handles login flow gracefully
- Updates automatically with polling
- Shows meaningful error states
- Provides excellent user experience

## Success Criteria
- [ ] UI displays all usage metrics accurately
- [ ] Progress bar shows visual usage representation
- [ ] Alerts appear when approaching/exceeding limits
- [ ] Login flow works seamlessly
- [ ] Automatic updates reflect latest data
- [ ] Error states are user-friendly
- [ ] UI is responsive and performant
- [ ] Styling matches design specifications

## Dependencies
- **Completed**: EPIC-01, EPIC-02, EPIC-03
- All backend integration complete

## Stories

### STORY-01: Usage Data Display Component
**Description**: Create component to display current usage metrics.

**Tasks**:
- Create UsageDisplay component
- Show usage_percent prominently
- Display tokens_used, tokens_limit, tokens_remaining
- Format numbers with commas
- Show last_updated timestamp

**Acceptance Criteria**:
- All metrics display correctly
- Numbers are formatted for readability
- Component updates when data changes
- Handles null/undefined data gracefully

---

### STORY-02: Progress Bar Component
**Description**: Visual progress bar showing usage percentage.

**Tasks**:
- Create ProgressBar component
- Implement smooth transitions
- Color coding (green <80%, orange 80-99%, red >=100%)
- Animated fill based on percentage

**Acceptance Criteria**:
- Progress bar fills to correct percentage
- Colors change based on thresholds
- Smooth animation on updates
- Responsive to container size

---

### STORY-03: Reset Timer Component
**Description**: Countdown timer showing time until usage resets.

**Tasks**:
- Create ResetTimer component
- Parse reset_time ISO string
- Calculate time remaining
- Update every minute
- Handle null reset_time

**Acceptance Criteria**:
- Shows "Xh Ym" format
- Updates in real-time
- Handles edge cases (expired, null)
- Clear display of countdown

---

### STORY-04: Alert System
**Description**: Alert banners for approaching/exceeding limits.

**Tasks**:
- Create Alert component
- Warning alert at >80% usage
- Critical alert at >=100% usage
- Clear, actionable messaging
- Dismissible (optional)

**Acceptance Criteria**:
- Warning appears at 80%
- Critical appears at 100%
- Messages are clear and helpful
- Alerts are visually distinct

---

### STORY-05: Login Flow UI
**Description**: User interface for first-time login.

**Tasks**:
- Create LoginScreen component
- Clear instructions for manual login
- "Start Login" button
- Loading state during login
- Success/error feedback

**Acceptance Criteria**:
- Instructions are clear
- Button triggers manual_login command
- Loading state shows during login
- Success transitions to main UI
- Errors show meaningful messages

---

### STORY-06: Error Handling UI
**Description**: User-friendly error states and messages.

**Tasks**:
- Create ErrorDisplay component
- Map error codes to user messages
- Retry button for recoverable errors
- Help text for common issues
- Link to troubleshooting docs

**Acceptance Criteria**:
- All error types have clear messages
- Retry button works for transient errors
- Help text provides actionable guidance
- UI doesn't crash on errors

---

### STORY-07: Integration with Backend
**Description**: Connect UI components to Tauri backend commands.

**Tasks**:
- Implement useEffect for initial data load
- Call check_session on mount
- Handle manual_login flow
- Implement poll_usage for refresh
- Start automatic polling after login
- Listen for usage-update events

**Acceptance Criteria**:
- All Tauri commands work from UI
- Events are handled correctly
- State updates trigger re-renders
- No memory leaks from event listeners

---

### STORY-08: Polish and Testing
**Description**: Final polish, animations, and testing.

**Tasks**:
- Add loading states
- Smooth transitions
- Test all user flows
- Cross-browser testing (if applicable)
- Accessibility improvements
- Final styling tweaks

**Acceptance Criteria**:
- No console errors
- Smooth user experience
- All flows tested manually
- Meets accessibility standards

## Technical Specifications

### Component Structure

```typescript
src/
├── components/
│   ├── UsageDisplay.tsx       // Main usage metrics display
│   ├── ProgressBar.tsx         // Visual progress bar
│   ├── ResetTimer.tsx          // Countdown timer
│   ├── Alert.tsx               // Alert banners
│   ├── LoginScreen.tsx         // First-time login UI
│   └── ErrorDisplay.tsx        // Error states
├── hooks/
│   ├── useUsageData.ts         // Custom hook for usage data
│   └── usePolling.ts           // Custom hook for polling
├── utils/
│   ├── formatters.ts           // Number/time formatting
│   └── timeUtils.ts            // Time calculations
├── App.tsx                     // Main app component
└── App.css                     // Global styles
```

### Data Flow

```
1. App mounts → check_session()
2. If no session → show LoginScreen
3. User clicks login → manual_login()
4. On success → poll_usage()
5. Start automatic polling → start_polling()
6. Listen for usage-update events
7. Update UI with new data
8. On error → show ErrorDisplay
```

### Interface Types

```typescript
interface UsageData {
  status: string;
  usage_percent: number;
  tokens_used: number;
  tokens_limit: number;
  tokens_remaining: number;
  reset_time: string | null;
  last_updated: string;
}

interface AppState {
  loading: boolean;
  needsLogin: boolean;
  usageData: UsageData | null;
  error: string | null;
}
```

## Styling Specifications

### Colors
- Primary gradient: `#667eea` to `#764ba2`
- Success (green): `#22c55e`
- Warning (orange): `#f97316`
- Critical (red): `#ef4444`
- Background overlay: `rgba(255, 255, 255, 0.1)`

### Typography
- Heading: 28px, weight 600
- Percentage: 64px, weight 700
- Metrics: 20px, weight 600
- Body: 14px, weight 400

### Spacing
- Container padding: 24px
- Section margin: 16px
- Component gap: 12px

## User Experience Requirements

### Loading States
- Initial load: Spinner with "Loading..."
- Manual refresh: Button disabled state
- Login: "Waiting for login..." message

### Error Messages
- session_required: "Please log in to Claude.ai"
- session_expired: "Your session expired. Please log in again"
- navigation_failed: "Couldn't reach Claude.ai. Check internet connection"
- extraction_failed: "Couldn't read usage data. Try refreshing"

### Accessibility
- Proper ARIA labels
- Keyboard navigation
- Screen reader support
- High contrast support

## Testing Strategy

### Manual Testing
- [ ] Fresh install flow (no session)
- [ ] Login flow
- [ ] Successful data display
- [ ] Automatic polling updates
- [ ] Manual refresh
- [ ] Error scenarios
- [ ] System tray integration
- [ ] Window show/hide

### Edge Cases
- [ ] No internet connection
- [ ] Python not installed
- [ ] Session expired mid-use
- [ ] 100% usage
- [ ] Null reset_time
- [ ] Very long reset times

## Performance Considerations

- Minimize re-renders with React.memo
- Debounce rapid updates
- Efficient event listener cleanup
- Small bundle size (CSS-in-JS or minimal CSS)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data update lag | Low | Show last_updated timestamp |
| Event listener leaks | Medium | Proper cleanup in useEffect |
| Error state confusion | Medium | Clear, specific error messages |
| Poor mobile display | Low | Not targeting mobile currently |

## Follow-up Work (Future Epics)

- Historical usage tracking
- Desktop notifications at thresholds
- Custom polling intervals
- Multi-account support
- Usage export functionality

## Notes
- Focus on desktop widget experience
- Fixed 450x650 window size
- No responsive mobile design needed
- Prioritize clarity over complexity
