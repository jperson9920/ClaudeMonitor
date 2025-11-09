# EPIC-01: Claude Usage Monitor v1.0 - Windows Desktop Tool

## Executive Summary

Build a Windows desktop monitoring tool that extracts Claude usage data from claude.ai, displays it in an always-on-top overlay, and projects usage trends. This tool will help users track their Claude API usage caps (4-hour, 1-week, and Opus 1-week limits) with visual indicators and predictive analytics.

**Version**: 1.0.0  
**Platform**: Windows 11  
**Target Audience**: Single-user local development tool  
**Deployment**: Local Windows machine (no CI/CD or cloud infrastructure)

## Objectives

1. **Real-time Monitoring**: Automatically scrape Claude usage data every 5 minutes
2. **Visual Feedback**: Display usage metrics in an always-on-top overlay window
3. **Predictive Analytics**: Project when usage caps will be reached based on historical trends
4. **Low Resource Usage**: Maintain total RAM usage under 250MB
5. **Reliability**: Handle session expiration, network errors, and data corruption gracefully

## Technical Stack

### Core Technologies
- **Language**: Python 3.8+
- **Web Scraping**: Playwright (persistent browser context)
- **UI Framework**: PyQt5 with qdarktheme
- **Data Storage**: JSON with atomic writes (atomicwrites library)
- **Process Management**: Multi-process architecture (scraper + overlay)

### Key Dependencies
```
playwright==1.40.0
PyQt5==5.15.10
qdarktheme==2.1.0
atomicwrites==1.4.1
```

## System Architecture

### Multi-Process Design

```
┌─────────────────────────────────────────────────────────┐
│                   MONITORING SYSTEM                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐         ┌──────────────────┐       │
│  │  Scraper       │────────▶│ JSON Data Store  │       │
│  │  Process       │  Write  │ (Atomic)         │       │
│  │                │         │                  │       │
│  │ - Playwright   │         │ usage-data.json  │       │
│  │ - Every 5 min  │         │                  │       │
│  │ - Session mgmt │         └────────┬─────────┘       │
│  └────────────────┘                  │                  │
│                                      │ Watch            │
│                                      │                  │
│  ┌────────────────┐         ┌───────▼─────────┐       │
│  │  Overlay UI    │◀────────│ File Watcher    │       │
│  │  Process       │  Read   │ (QTimer poll)   │       │
│  │                │         │                  │       │
│  │ - PyQt5        │         └─────────────────┘       │
│  │ - Always-on-top│                                    │
│  │ - Dark theme   │         ┌─────────────────┐       │
│  └────────────────┘         │  Projection     │       │
│         │                   │  Algorithm      │       │
│         └──────────────────▶│  (In UI)        │       │
│           Calculate         │                  │       │
│                             └─────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Process Separation Benefits
- **Fault Isolation**: UI crash doesn't stop scraping
- **True Parallelism**: No GIL limitations
- **Independent Restart**: Update components separately
- **Better Resource Management**: Dedicated memory per process

### Communication Pattern
- Scraper writes to JSON atomically every 5 minutes
- UI watches JSON file for changes (1-second polling)
- No complex IPC required
- Easy debugging (inspect JSON manually)

## Success Criteria

### Functional Requirements
- ✅ Scraper successfully polls claude.ai/settings/usage every 5 minutes
- ✅ Manual login flow with persistent session across restarts
- ✅ Overlay displays three usage metrics: 4-hour cap, 1-week cap, Opus 1-week
- ✅ Progress bars with color coding (blue <75%, orange 75-90%, red >90%)
- ✅ Projection algorithms calculate time-to-cap estimates
- ✅ Always-on-top window positioning in top-right corner
- ✅ Draggable window without title bar

### Performance Requirements
- ✅ Total RAM usage < 250MB (scraper ~150MB, UI ~80MB)
- ✅ CPU usage < 1% idle, 5-10% during scraping
- ✅ UI startup time < 1 second
- ✅ Scraper startup time < 5 seconds
- ✅ Data file size < 5MB (7 days historical data)

### Reliability Requirements
- ✅ Handle session expiration gracefully (prompt re-login)
- ✅ Retry logic with exponential backoff (max 3 attempts)
- ✅ Corrupted JSON recovery
- ✅ Network timeout handling (30s page load, 10s selectors)
- ✅ Historical data retention (7 days, 2016 data points)

## Project Structure

```
ClaudeMonitor/
├── src/
│   ├── scraper/
│   │   ├── claude_usage_monitor.py
│   │   ├── session_manager.py
│   │   └── selector_discovery.py
│   ├── overlay/
│   │   ├── overlay_widget.py
│   │   ├── projection_algorithms.py
│   │   └── file_watcher.py
│   ├── shared/
│   │   ├── data_schema.py
│   │   └── atomic_writer.py
│   └── run_system.py
├── data/
│   └── usage-data.json
├── browser-data/  (Playwright persistent context)
├── tests/
│   ├── test_scraper.py
│   ├── test_overlay.py
│   └── test_projections.py
├── docs/
│   └── JIRA/
│       ├── EPIC-01.md (this file)
│       ├── EPIC-01-STOR-01.md
│       ├── ... (STOR-02 through STOR-11)
│       └── compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md
├── requirements.txt
├── README.md
└── launch.ps1
```

## Story List

### [EPIC-01-STOR-01](EPIC-01-STOR-01.md): Project Setup and Dependencies
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 2 hours  
**Dependencies**: None

**Objective**: Set up Python environment, install all dependencies, and create project directory structure.

### [EPIC-01-STOR-02](EPIC-01-STOR-02.md): Playwright Web Scraper with Persistent Authentication
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 8 hours  
**Dependencies**: STOR-01

**Objective**: Implement Playwright-based web scraper with persistent browser context, manual login flow, and basic data extraction.

### [EPIC-01-STOR-03](EPIC-01-STOR-03.md): JSON Data Schema and Atomic Writes
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 4 hours  
**Dependencies**: STOR-01

**Objective**: Define JSON schema for usage data and implement atomic write pattern to prevent data corruption.

### [EPIC-01-STOR-04](EPIC-01-STOR-04.md): PyQt5 Overlay UI with Always-On-Top
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 10 hours  
**Dependencies**: STOR-01, STOR-03

**Objective**: Build PyQt5 overlay window with frameless design, always-on-top functionality, dark theme, and progress bars.

### [EPIC-01-STOR-05](EPIC-01-STOR-05.md): Usage Projection Algorithms
**Status**: Not Started  
**Priority**: P1 (High)  
**Estimated Effort**: 6 hours  
**Dependencies**: STOR-03

**Objective**: Implement SMA, linear regression, and time-to-cap estimation algorithms for usage prediction.

### [EPIC-01-STOR-06](EPIC-01-STOR-06.md): File Watcher Integration
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 3 hours  
**Dependencies**: STOR-03, STOR-04

**Objective**: Integrate QTimer-based file watching to reload JSON data and update UI in real-time.

### [EPIC-01-STOR-07](EPIC-01-STOR-07.md): Process Orchestration
**Status**: Not Started  
**Priority**: P1 (High)  
**Estimated Effort**: 5 hours  
**Dependencies**: STOR-02, STOR-04

**Objective**: Create run_system.py to launch and manage both scraper and overlay processes with graceful shutdown.

### [EPIC-01-STOR-08](EPIC-01-STOR-08.md): Error Handling and Retry Logic
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 6 hours  
**Dependencies**: STOR-02, STOR-04

**Objective**: Implement exponential backoff retry, session expiration handling, corrupted JSON recovery, and rate limiting.

### [EPIC-01-STOR-09](EPIC-01-STOR-09.md): Selector Discovery and Validation
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 4 hours  
**Dependencies**: STOR-02

**Objective**: Manually inspect claude.ai/settings/usage page to discover correct selectors and implement fallback selector strategy.

### [EPIC-01-STOR-10](EPIC-01-STOR-10.md): Testing and Validation
**Status**: Not Started  
**Priority**: P1 (High)  
**Estimated Effort**: 8 hours  
**Dependencies**: STOR-02, STOR-04, STOR-05, STOR-06, STOR-07, STOR-08, STOR-09

**Objective**: Validate all components including selector accuracy, atomic writes, projection algorithms, and 24-hour resource monitoring.

### [EPIC-01-STOR-11](EPIC-01-STOR-11.md): Documentation and Packaging
**Status**: Not Started  
**Priority**: P2 (Medium)  
**Estimated Effort**: 4 hours  
**Dependencies**: STOR-10

**Objective**: Create README.md, requirements.txt, PowerShell launch script, and troubleshooting guide.

## Story Execution Order

### Phase 1: Foundation (Parallel)
1. **STOR-01**: Project Setup (Day 1)
2. **STOR-03**: JSON Data Schema (Day 1-2)

### Phase 2: Core Components (Parallel after Phase 1)
3. **STOR-02**: Playwright Web Scraper (Day 2-3)
4. **STOR-04**: PyQt5 Overlay UI (Day 2-4)

### Phase 3: Integration (Sequential)
5. **STOR-09**: Selector Discovery (Day 4)
6. **STOR-05**: Usage Projection Algorithms (Day 4-5)
7. **STOR-06**: File Watcher Integration (Day 5)
8. **STOR-07**: Process Orchestration (Day 5-6)
9. **STOR-08**: Error Handling and Retry Logic (Day 6-7)

### Phase 4: Validation & Polish (Sequential)
10. **STOR-10**: Testing and Validation (Day 7-8)
11. **STOR-11**: Documentation and Packaging (Day 8-9)

**Total Estimated Effort**: 60 hours (~9 working days for single developer)

## Risk Assessment

### High-Risk Items
1. **Selector Stability**: Claude.ai may change page structure, breaking selectors
   - **Mitigation**: Implement multiple fallback selectors, add selector validation tests
   
2. **Session Expiration**: Browser sessions may expire unpredictably
   - **Mitigation**: Implement session validation, auto-detection, and re-login prompts

3. **Rate Limiting**: Too frequent polling may trigger rate limits
   - **Mitigation**: Use 5-minute intervals with rate limiter class

### Medium-Risk Items
1. **Multi-Monitor Behavior**: Window positioning may be inconsistent
   - **Mitigation**: Test on multi-monitor setups, add configuration option

2. **Windows API Compatibility**: Extended styles may vary across Windows versions
   - **Mitigation**: Test on Windows 10 and 11, add fallback for older versions

### Low-Risk Items
1. **Memory Leaks**: Long-running processes may accumulate memory
   - **Mitigation**: Implement periodic resource monitoring, optional daily restart

## Resource Requirements

### Development Environment
- **OS**: Windows 11
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended for development)
- **Disk Space**: 500MB for dependencies and browser data
- **Network**: Stable internet connection for claude.ai access

### Runtime Environment
- **Scraper Process**: ~150MB RAM, <1% CPU idle, 5-10% during scrape
- **Overlay Process**: ~80MB RAM, <1% CPU idle
- **Total System Impact**: ~250MB RAM, negligible CPU when idle
- **Disk I/O**: Minimal (one JSON write every 5 minutes, ~5KB)

## References

### Source Documentation
- **Technical Specification**: [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md)
- **Mode Permissions**: `MODE-PERMISSIONS.md` (project root)
- **Delegation Workflow**: `DELEGATION-WORKFLOW.md` (project root)

### External Documentation
- **Playwright Python**: https://playwright.dev/python/docs/intro
- **PyQt5 Documentation**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **Windows API Reference**: https://docs.microsoft.com/en-us/windows/win32/api/

## Notes for Workers

### General Guidelines
1. **Use Sequential Thinking**: For complex tasks (especially PowerShell scripts), use the `sequentialthinking` MCP tool to plan before implementing
2. **Update JIRA Docs**: Update your STOR-XX.md file with progress, blockers, and implementation notes
3. **Reference Source**: All code examples are in the compass_artifact document - adapt them to fit the modular structure
4. **Local Execution**: All code runs on a single Windows machine - no cloud/deployment considerations needed
5. **File References**: Use markdown link syntax with line numbers: [`filename`](path/to/file.ext:line) or [`Class.method()`](path/to/file.ext:line)

### Code Style Requirements
- **Modular Files**: Keep files under 500 lines - split into logical modules
- **Type Hints**: Use Python type hints for all function signatures
- **Docstrings**: Google-style docstrings for all classes and functions
- **Error Handling**: Explicit try-except blocks with logging
- **Constants**: Use UPPER_CASE for configuration constants

### Testing Requirements
- **Unit Tests**: Required for projection algorithms and data schema
- **Integration Tests**: Required for scraper ↔ JSON ↔ UI data flow
- **Manual Validation**: Required for UI appearance, selector discovery, and multi-monitor behavior

## Acceptance Criteria for EPIC-01 Completion

- [ ] All 11 stories marked as DONE
- [ ] Scraper successfully polls claude.ai/settings/usage every 5 minutes
- [ ] Overlay displays all three usage metrics with accurate data
- [ ] Projection algorithms calculate time-to-cap estimates
- [ ] Always-on-top window works correctly on Windows 11
- [ ] Manual login flow persists session across restarts
- [ ] Error handling covers session expiration, network errors, and corrupted JSON
- [ ] Resource usage < 250MB RAM total
- [ ] 24-hour continuous operation test passes
- [ ] README.md with installation and usage instructions complete
- [ ] All code committed with EPIC-01 references in commit messages

---

**Last Updated**: 2025-11-08  
**Epic Owner**: Orchestrator Mode  
**Target Completion**: 2025-11-17