# EPIC-06: Notifications & Alerts System

## Problem Statement
Users need to be proactively notified when they approach or reach their usage limits to prevent unexpected service interruptions. Currently, users must manually check the dashboard to monitor their usage. A notification system would provide timely alerts via desktop notifications, system tray indicators, and configurable thresholds.

## Goal
Implement a comprehensive notification and alert system that:
- Sends desktop notifications at configurable usage thresholds
- Shows visual indicators in the system tray icon
- Provides notification history and management
- Allows users to customize notification preferences
- Includes snooze and mute functionality

## Success Criteria
- [ ] Desktop notifications appear at configured thresholds
- [ ] System tray icon changes color based on usage status
- [ ] Notification sound can be toggled on/off
- [ ] Users can configure custom thresholds (e.g., 80%, 90%, 95%)
- [ ] Notification history is accessible and clearable
- [ ] Snooze functionality works correctly
- [ ] Do Not Disturb mode prevents notifications
- [ ] All notification preferences persist across restarts

## Dependencies
- **Completed**: EPIC-01 through EPIC-05
- Tauri notification API
- System tray icon management

## Stories

### STORY-01: Desktop Notifications Foundation
**Description**: Implement basic desktop notification infrastructure.

**Tasks**:
- Add Tauri notification permissions to tauri.conf.json
- Create notification module in Rust
- Implement send_notification() command
- Test notifications on startup
- Handle notification permissions

**Acceptance Criteria**:
- Desktop notifications can be triggered from Rust
- Notifications display title, body, and icon
- Notifications appear in system notification center
- Permission errors are handled gracefully

---

### STORY-02: Usage Threshold Notifications
**Description**: Trigger notifications when usage crosses thresholds.

**Tasks**:
- Create notification thresholds configuration
- Add threshold checking logic in polling
- Implement notification deduplication (don't spam)
- Track which thresholds have already fired
- Reset notification state on usage reset

**Acceptance Criteria**:
- Notifications fire at 80%, 90%, and 100% usage
- Each threshold notification fires only once per period
- Notifications reset when usage resets
- Clear, informative notification messages

---

### STORY-03: System Tray Icon Status
**Description**: Change system tray icon based on usage level.

**Tasks**:
- Create multiple tray icon variants (normal, warning, critical)
- Add Rust function to update tray icon
- Update icon when usage changes
- Add icon legend to settings
- Test icon changes

**Acceptance Criteria**:
- Icon is green/normal below 80%
- Icon is orange/warning at 80-99%
- Icon is red/critical at 100%
- Icon updates in real-time
- Icon states are visually distinct

---

### STORY-04: Notification Configuration UI
**Description**: Add notification settings to Settings panel.

**Tasks**:
- Add Notifications section to Settings UI
- Create threshold configuration inputs
- Add notification sound toggle
- Add notification preview button
- Save notification preferences

**Acceptance Criteria**:
- Users can enable/disable notifications
- Custom thresholds can be configured
- Notification sound can be toggled
- Preview button tests notifications
- Settings persist correctly

---

### STORY-05: Notification History
**Description**: Track and display notification history.

**Tasks**:
- Create notification history storage
- Implement history limit (last 50 notifications)
- Add history UI component
- Implement clear history function
- Add timestamp to notifications

**Acceptance Criteria**:
- Last 50 notifications are stored
- History displays notification time and message
- History can be cleared
- History persists across restarts
- Old notifications are automatically pruned

---

### STORY-06: Snooze Functionality
**Description**: Allow users to snooze notifications temporarily.

**Tasks**:
- Add snooze button to notification settings
- Implement snooze duration options (15m, 30m, 1h, 2h)
- Track snooze state and expiry
- Show snooze status in UI
- Auto-resume after snooze expires

**Acceptance Criteria**:
- Snooze prevents new notifications
- Snooze duration is configurable
- UI shows remaining snooze time
- Snooze can be cancelled early
- Notifications resume after snooze

---

### STORY-07: Do Not Disturb Mode
**Description**: Implement Do Not Disturb scheduling.

**Tasks**:
- Add DND toggle to settings
- Implement DND schedule (start/end times)
- Suppress notifications during DND
- Show DND status indicator
- Allow DND override for critical alerts

**Acceptance Criteria**:
- DND can be enabled manually
- DND can be scheduled (e.g., 10PM-8AM)
- Notifications are suppressed during DND
- Critical (100% usage) can override DND
- DND status visible in UI

---

### STORY-08: Notification Sounds
**Description**: Add audio alerts for notifications.

**Tasks**:
- Add notification sound assets
- Implement sound playback in Tauri
- Add volume control
- Create sound selection UI
- Test cross-platform compatibility

**Acceptance Criteria**:
- Notification sound plays when enabled
- Volume is adjustable (0-100%)
- Multiple sound options available
- Sounds work on all platforms
- Sounds respect system volume

---

### STORY-09: Testing and Polish
**Description**: Test all notification features and polish UI.

**Tasks**:
- Test notifications at all thresholds
- Test notification history
- Test DND and snooze
- Verify tray icon changes
- Add notification animations
- Fix any bugs

**Acceptance Criteria**:
- All notification scenarios work correctly
- No duplicate notifications
- Notification timing is accurate
- UI is polished and intuitive
- Performance is acceptable

## Technical Specifications

### Notification Settings Schema

```json
{
  "notifications": {
    "enabled": true,
    "thresholds": [80, 90, 100],
    "sound": {
      "enabled": true,
      "volume": 50,
      "sound_name": "default"
    },
    "dnd": {
      "enabled": false,
      "schedule": {
        "start_time": "22:00",
        "end_time": "08:00"
      },
      "allow_critical": true
    },
    "snooze": {
      "active": false,
      "until": null,
      "duration_minutes": 30
    }
  }
}
```

### Notification History Schema

```json
{
  "history": [
    {
      "timestamp": "2025-01-14T15:30:00Z",
      "title": "Usage Warning",
      "message": "You've used 80% of your Claude usage cap",
      "level": "warning"
    }
  ]
}
```

### Tauri Commands

```rust
#[tauri::command]
async fn send_notification(title: String, body: String) -> Result<(), String>

#[tauri::command]
async fn update_tray_icon(status: String) -> Result<(), String>

#[tauri::command]
async fn get_notification_history() -> Result<Vec<NotificationRecord>, String>

#[tauri::command]
async fn clear_notification_history() -> Result<(), String>

#[tauri::command]
async fn set_snooze(duration_minutes: u32) -> Result<(), String>

#[tauri::command]
async fn cancel_snooze() -> Result<(), String>
```

### Notification Triggers

```rust
fn check_and_notify(usage_percent: f64, settings: &NotificationSettings) {
    // Skip if notifications disabled or snoozed
    if !settings.enabled || is_snoozed() {
        return;
    }

    // Skip if DND active (unless critical and override enabled)
    if is_dnd_active() && !(usage_percent >= 100.0 && settings.dnd.allow_critical) {
        return;
    }

    // Check thresholds
    for threshold in &settings.thresholds {
        if usage_percent >= *threshold && !has_notified_for_threshold(*threshold) {
            send_notification(usage_percent, *threshold);
            mark_threshold_notified(*threshold);
        }
    }
}
```

## UI Specifications

### Notification Settings UI

```
┌─────────────────────────────────┐
│  Notifications                  │
├─────────────────────────────────┤
│  [x] Enable notifications       │
│                                 │
│  Alert Thresholds:              │
│  [x] 80%  [x] 90%  [x] 100%    │
│  [ ] Custom: [__]%  [Add]      │
│                                 │
│  Sound                          │
│  [x] Play notification sound    │
│  Volume: [====•-----] 50%       │
│  Sound: [Default ▼]            │
│  [🔊 Test]                     │
│                                 │
│  Do Not Disturb                 │
│  [ ] Enable DND                 │
│  Schedule: [22:00] to [08:00]  │
│  [x] Allow critical alerts      │
│                                 │
│  Snooze: [Not active]           │
│  [Snooze 15m] [30m] [1h] [2h]  │
│                                 │
│  History ([3] notifications)    │
│  [View History] [Clear]         │
└─────────────────────────────────┘
```

### Notification History UI

```
┌─────────────────────────────────┐
│  Notification History   [Clear] │
├─────────────────────────────────┤
│  ⚠️  15:30 - Usage Warning      │
│     You've used 90% of your     │
│     usage cap.                  │
│  ─────────────────────────────  │
│  ⚠️  14:15 - Usage Warning      │
│     You've used 80% of your     │
│     usage cap.                  │
│  ─────────────────────────────  │
│  ✓  09:00 - Usage Reset         │
│     Your usage cap has reset.   │
└─────────────────────────────────┘
```

## File Structure

```
src/
├── components/
│   ├── Settings.tsx              # Update with notifications section
│   ├── NotificationHistory.tsx   # Notification history component
│   └── NotificationPreview.tsx   # Preview notification UI
├── hooks/
│   └── useNotifications.ts       # Notification management hook
└── App.tsx

src-tauri/src/
├── notifications.rs              # Notification module
└── tray.rs                       # Tray icon management

src-tauri/resources/
├── icons/
│   ├── tray-normal.png
│   ├── tray-warning.png
│   └── tray-critical.png
└── sounds/
    ├── default.mp3
    └── gentle.mp3
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Notification spam | High | Implement deduplication, track fired thresholds |
| Permission denied | Medium | Handle gracefully, show setup instructions |
| Sound playback issues | Low | Test on all platforms, fallback to silent |
| DND not working | Low | Test time calculations, add manual override |
| Tray icon not updating | Medium | Test on all platforms, add fallback text |

## Performance Considerations

- Notification history limited to 50 items to prevent unbounded growth
- DND time calculations cached to avoid repeated parsing
- Tray icon updates batched to prevent flicker
- Notification deduplication uses in-memory set for speed

## Accessibility

- Notifications use system notification center for screen reader support
- Visual indicators (tray icon) supplement audio alerts
- High contrast notification icons
- Clear, concise notification text

## Testing Strategy

### Manual Testing
- [ ] Trigger notifications at each threshold
- [ ] Test notification sounds
- [ ] Verify DND blocking
- [ ] Test snooze functionality
- [ ] Verify tray icon changes
- [ ] Test notification history
- [ ] Cross-platform testing

### Edge Cases
- [ ] Notifications when app is minimized
- [ ] Notifications when app is not focused
- [ ] DND during threshold crossing
- [ ] Snooze expiry during usage change
- [ ] Rapid threshold crossings
- [ ] System notification center full

## Future Enhancements (Beyond Epic 6)

- Email/SMS notifications
- Webhook integration for external alerts
- Notification templates
- Priority levels for notifications
- Notification grouping
- Rich notifications with actions

## Notes

- Notifications should be helpful, not annoying
- Default to conservative thresholds (80%, 90%, 100%)
- Respect user's system notification preferences
- Clear notifications when usage resets
- Tray icon should be subtle but clear
