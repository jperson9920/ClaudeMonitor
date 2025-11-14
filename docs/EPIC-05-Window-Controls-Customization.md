# EPIC-05: Window Controls & Customization

## Problem Statement
Enhance user control over the widget's appearance and behavior by implementing window resizing, always-on-top functionality, color theme customization, and persistent window preferences. Users need the flexibility to adapt the widget to their workspace and visual preferences.

## Goal
Transform the fixed widget into a customizable desktop application that:
- Allows window resizing to user preference
- Can stay always on top of other windows
- Supports custom color themes
- Remembers window position and size across sessions
- Provides a settings interface for configuration

## Success Criteria
- [ ] Window can be resized smoothly
- [ ] Always-on-top toggle works reliably
- [ ] At least 5 color themes available
- [ ] Custom color picker functional
- [ ] Window preferences persist across restarts
- [ ] Settings panel is intuitive and responsive
- [ ] All settings save/load correctly

## Dependencies
- **Completed**: EPIC-01, EPIC-02, EPIC-03, EPIC-04
- All core functionality is in place

## Stories

### STORY-01: Make Window Resizable
**Description**: Enable window resizing and implement responsive layout.

**Tasks**:
- Update tauri.conf.json to enable resizable: true
- Set minimum window dimensions (400x500)
- Update CSS to handle variable dimensions
- Test layout at different sizes
- Ensure all elements scale appropriately

**Acceptance Criteria**:
- Window can be resized by dragging edges
- Minimum size prevents layout breaking
- Content remains readable at all sizes
- Layout is responsive and doesn't overflow

---

### STORY-02: Always on Top Toggle
**Description**: Implement always-on-top functionality with toggle control.

**Tasks**:
- Add Tauri command for set_always_on_top()
- Add toggle button to UI
- Persist always-on-top preference
- Add to settings and system tray menu
- Visual indication when always-on-top is active

**Acceptance Criteria**:
- Toggle button works in UI
- Window stays on top when enabled
- Preference persists across restarts
- System tray menu includes toggle option
- Visual indicator shows current state

---

### STORY-03: Window Position Persistence
**Description**: Save and restore window position and size.

**Tasks**:
- Create window state storage (position, size)
- Implement save on window move/resize
- Restore window state on startup
- Handle multi-monitor scenarios
- Validate saved positions are still valid

**Acceptance Criteria**:
- Window position saved on move
- Window size saved on resize
- Position/size restored on app restart
- Invalid positions default to center
- Works across multiple monitors

---

### STORY-04: Color Theme System
**Description**: Implement color theme infrastructure.

**Tasks**:
- Create theme configuration structure
- Define 5+ preset color themes
- Implement theme switching logic
- Add theme state management
- Persist selected theme

**Acceptance Criteria**:
- At least 5 preset themes available
- Theme can be switched at runtime
- All UI elements update with theme
- Selected theme persists across restarts
- Smooth transition between themes

---

### STORY-05: Custom Color Picker
**Description**: Allow users to create custom color themes.

**Tasks**:
- Implement color picker component
- Allow customization of primary/secondary colors
- Preview theme before applying
- Save custom themes
- Load custom themes

**Acceptance Criteria**:
- Color picker UI is intuitive
- Users can select custom colors
- Preview shows theme before applying
- Custom themes can be saved
- Custom themes persist across restarts

---

### STORY-06: Settings Panel UI
**Description**: Create comprehensive settings panel.

**Tasks**:
- Design settings panel layout
- Organize settings into categories
- Add settings button to main UI
- Implement settings modal/panel
- Include all preference controls

**Acceptance Criteria**:
- Settings accessible from main UI
- Clean, organized layout
- All preferences in one place
- Easy to navigate and understand
- Close/save functionality works

---

### STORY-07: Settings Persistence
**Description**: Implement settings storage and retrieval.

**Tasks**:
- Create settings storage system
- Define settings schema
- Implement save_settings() command
- Implement load_settings() command
- Handle settings migration/defaults

**Acceptance Criteria**:
- All settings save correctly
- Settings load on startup
- Invalid settings revert to defaults
- Settings file is human-readable JSON
- Migration handles version changes

---

### STORY-08: Testing and Polish
**Description**: Test all new features and polish UI.

**Tasks**:
- Test resizing at extreme dimensions
- Test always-on-top across platforms
- Test theme switching performance
- Test settings persistence
- Add animations/transitions
- Fix any bugs found

**Acceptance Criteria**:
- All features work as expected
- No console errors
- Smooth transitions
- Performance is acceptable
- Cross-platform testing complete

## Technical Specifications

### Settings Schema

```json
{
  "window": {
    "width": 450,
    "height": 650,
    "x": 100,
    "y": 100,
    "alwaysOnTop": false
  },
  "theme": {
    "preset": "default",
    "custom": {
      "primary": "#667eea",
      "secondary": "#764ba2",
      "accent": "#22c55e",
      "warning": "#f97316",
      "critical": "#ef4444"
    }
  },
  "polling": {
    "interval": 300
  }
}
```

### Preset Themes

1. **Default** - Purple gradient (current)
2. **Ocean** - Blue/teal gradient
3. **Forest** - Green/emerald gradient
4. **Sunset** - Orange/pink gradient
5. **Midnight** - Dark blue/purple gradient
6. **Monochrome** - Gray scale
7. **Custom** - User-defined colors

### Tauri Commands

```rust
#[tauri::command]
async fn set_always_on_top(window: Window, enabled: bool) -> Result<(), String>

#[tauri::command]
async fn get_window_position(window: Window) -> Result<WindowPosition, String>

#[tauri::command]
async fn save_settings(settings: Settings) -> Result<(), String>

#[tauri::command]
async fn load_settings() -> Result<Settings, String>

#[tauri::command]
async fn apply_theme(theme: Theme) -> Result<(), String>
```

### CSS Variables for Theming

```css
:root {
  --primary-start: #667eea;
  --primary-end: #764ba2;
  --accent: #22c55e;
  --warning: #f97316;
  --critical: #ef4444;
  --overlay: rgba(255, 255, 255, 0.1);
}
```

## UI Specifications

### Settings Panel Layout

```
┌─────────────────────────────────┐
│  ⚙️  Settings                   │
├─────────────────────────────────┤
│                                 │
│  Window                         │
│  [ ] Always on top             │
│                                 │
│  Theme                          │
│  [Select Theme ▼]              │
│  [🎨 Custom Colors...]         │
│                                 │
│  Polling                        │
│  Interval: [5] minutes         │
│                                 │
│  [Reset to Defaults] [Save]    │
└─────────────────────────────────┘
```

### Color Picker UI

```
┌─────────────────────────────────┐
│  🎨 Custom Theme                │
├─────────────────────────────────┤
│  Primary Start: [#667eea] 🎨   │
│  Primary End:   [#764ba2] 🎨   │
│  Accent:        [#22c55e] 🎨   │
│  Warning:       [#f97316] 🎨   │
│  Critical:      [#ef4444] 🎨   │
│                                 │
│  Preview:                       │
│  [────────────────────────]     │
│                                 │
│  [Cancel] [Apply]              │
└─────────────────────────────────┘
```

## File Structure

```
src/
├── components/
│   ├── Settings.tsx              # Settings panel component
│   ├── ColorPicker.tsx           # Color picker component
│   └── ThemePreview.tsx          # Theme preview component
├── hooks/
│   ├── useSettings.ts            # Settings management hook
│   └── useTheme.ts               # Theme management hook
├── themes/
│   ├── themes.ts                 # Theme definitions
│   └── ThemeProvider.tsx         # Theme context provider
└── App.tsx

src-tauri/src/
├── settings.rs                   # Settings management module
└── window.rs                     # Window control utilities
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Layout breaking at small sizes | Medium | Test thoroughly, set minimum dimensions |
| Theme switching performance | Low | Use CSS variables, minimize re-renders |
| Settings corruption | Medium | Validate on load, provide defaults |
| Window position off-screen | Low | Validate coordinates, default to center |
| Color contrast issues | Medium | Provide theme preview, warn about contrast |

## Performance Considerations

- Use CSS variables for instant theme switching
- Debounce window resize/move events
- Lazy load color picker component
- Cache computed theme values
- Minimize re-renders with React.memo

## Accessibility

- Keyboard navigation for settings
- ARIA labels for all controls
- Color contrast validation
- Focus indicators
- Screen reader support

## Testing Strategy

### Manual Testing
- [ ] Resize to various dimensions
- [ ] Toggle always-on-top
- [ ] Switch between all themes
- [ ] Create custom theme
- [ ] Save and restore settings
- [ ] Multi-monitor scenarios
- [ ] Restart app and verify persistence

### Edge Cases
- [ ] Extremely small window size
- [ ] Saved position off-screen
- [ ] Invalid color values
- [ ] Corrupted settings file
- [ ] Very fast theme switching

## Future Enhancements (Beyond Epic 5)

- Import/export themes
- Theme sharing/marketplace
- Keyboard shortcuts for common actions
- Window snapping
- Opacity control

## Notes

- Window resizing must maintain usability at all sizes
- Always-on-top should be easily toggleable
- Color themes must maintain readability
- Settings should be discoverable
- All preferences must persist reliably
