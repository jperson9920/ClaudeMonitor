# EPIC-02: Tauri Application Setup

## Problem Statement
Set up the Tauri desktop application framework that will serve as the foundation for the Claude Usage Monitor widget. This includes initializing the Tauri project, configuring the build system, and creating a minimal working desktop application.

## Goal
Create a functional Tauri desktop application with:
- Proper project structure (Rust backend + React frontend)
- Build configuration for development and production
- System tray integration
- Window management
- Basic communication between frontend and backend

## Success Criteria
- [ ] Tauri project initializes successfully
- [ ] Development server runs without errors
- [ ] Application builds for current platform
- [ ] System tray icon appears and works
- [ ] Frontend can communicate with Rust backend via IPC
- [ ] Window can be shown/hidden from system tray

## Dependencies
- **Completed**: EPIC-01 (Python scraper will be integrated later)
- **Requires**: Node.js 18+, Rust 1.70+

## Stories

### STORY-01: Initialize Tauri Project
**Description**: Create and configure a new Tauri project with React frontend.

**Tasks**:
- Initialize Tauri project with React template
- Configure package.json with required dependencies
- Set up project directory structure
- Verify initial build works

**Acceptance Criteria**:
- Project structure follows Tauri conventions
- npm install completes successfully
- npm run dev launches application
- Initial "Hello Tauri" window appears

---

### STORY-02: Configure Tauri Settings
**Description**: Configure Tauri for our specific use case as a desktop widget.

**Tasks**:
- Update tauri.conf.json with app metadata
- Configure window size and positioning
- Set resizable: false for fixed widget size
- Configure app identifier and version

**Acceptance Criteria**:
- Window opens at correct size (450x650)
- Window is not resizable
- App identifier is set correctly
- Window is centered on screen

---

### STORY-03: System Tray Integration
**Description**: Add system tray icon with menu for showing/hiding the widget.

**Tasks**:
- Add system tray dependency to Tauri
- Create tray icon assets
- Implement tray menu (Show, Refresh, Quit)
- Handle tray menu events

**Acceptance Criteria**:
- Tray icon appears in system tray
- Click "Show" brings window to front
- Click "Quit" closes application
- Left-click on tray shows window

---

### STORY-04: Frontend Scaffolding
**Description**: Set up basic React component structure and styling.

**Tasks**:
- Create App.tsx with basic layout
- Add Tailwind CSS or basic CSS
- Create placeholder components for usage display
- Set up basic routing (if needed)

**Acceptance Criteria**:
- App renders without errors
- Basic layout is visible
- Styling is applied correctly
- Components are properly organized

---

### STORY-05: Rust Backend Setup
**Description**: Set up Rust backend with basic command structure.

**Tasks**:
- Create src-tauri/src/main.rs with basic structure
- Set up Cargo.toml with required dependencies
- Create placeholder Tauri commands
- Test IPC communication with frontend

**Acceptance Criteria**:
- Rust code compiles without errors
- At least one test command works from frontend
- Proper error handling in commands
- State management is initialized

---

### STORY-06: Build Configuration
**Description**: Configure build process for development and production.

**Tasks**:
- Set up development build configuration
- Configure production build settings
- Test cross-platform build (if applicable)
- Document build process

**Acceptance Criteria**:
- npm run tauri dev works
- npm run tauri build produces executable
- Build artifacts are in expected locations
- Build process is documented

---

### STORY-07: Testing and Validation
**Description**: Ensure the Tauri application works correctly across all platforms.

**Tasks**:
- Test application startup
- Test system tray functionality
- Test window show/hide
- Verify IPC communication

**Acceptance Criteria**:
- Application starts without errors
- All tray menu items work
- Window management works correctly
- Frontend-backend communication is reliable

## Technical Specifications

### Dependencies
```json
{
  "devDependencies": {
    "@tauri-apps/cli": "^1.5.0",
    "@tauri-apps/api": "^1.5.0",
    "vite": "^5.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0"
  }
}
```

### File Structure
```
ClaudeMonitor/
├── src-tauri/
│   ├── src/
│   │   └── main.rs
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── icons/
├── src/
│   ├── App.tsx
│   ├── App.css
│   ├── main.tsx
│   └── index.html
├── package.json
└── vite.config.ts
```

### Window Configuration
```json
{
  "windows": [{
    "title": "Claude Usage Monitor",
    "width": 450,
    "height": 650,
    "resizable": false,
    "center": true,
    "decorations": true,
    "visible": true
  }]
}
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Platform compatibility | Medium | Test on target platforms early |
| Build complexity | Low | Follow Tauri documentation closely |
| System tray limitations | Medium | Test on different desktop environments |

## Follow-up Epics
- EPIC-03: Rust-Python Integration
- EPIC-04: React UI Implementation

## Notes
- This epic focuses solely on Tauri setup and does not integrate the Python scraper
- Python scraper integration will be handled in EPIC-03
- UI implementation will be minimal - just enough to verify Tauri works
