# EPIC-04: Overlay UI Implementation & Refinements

## Executive Summary

Implement the complete PyQt5-based overlay UI system for the Claude Usage Monitor, including the always-on-top widget, projection algorithms for usage predictions, file watching for real-time updates, and shared data management modules.

**Version**: 1.0.0
**Status**: In Progress
**Priority**: P0 (Blocker)
**Target Branch**: `claude/epic-05-historical-data-patch-011CUy7PMifh47bVapRGF7WU`

## Objectives

1. **Overlay Widget**: Build PyQt5 frameless, always-on-top window with dark theme
2. **Projection Algorithms**: Implement SMA, linear regression, and time-to-cap estimation
3. **File Watcher**: Real-time monitoring of data changes with automatic UI updates
4. **Shared Modules**: Data schema validation and atomic file writing utilities

## Technical Context

### Components

#### 1. Overlay Widget (`src/overlay/overlay_widget.py`)
- Always-on-top, frameless window (300x400px)
- Dark theme using qdarktheme
- Three color-coded progress bars (4hr, 1wk, Opus 1wk)
- Draggable window positioning
- Real-time data updates via file watching

#### 2. Projection Algorithms (`src/overlay/projection_algorithms.py`)
- Simple Moving Average (SMA) calculation
- Linear regression for usage trends
- Time-to-cap estimation
- Confidence level determination
- Integration with data pipeline

#### 3. Shared Modules
- **data_schema.py**: JSON schema validation and data structure definitions
- **atomic_writer.py**: Atomic file write operations to prevent corruption

## Story List

### Implemented Stories

This EPIC consolidates three EPIC-01 stories into a single implementation:

1. **EPIC-01-STOR-04**: PyQt5 Overlay UI with Always-On-Top
   - Status: Implemented ✅
   - Deliverable: `src/overlay/overlay_widget.py`

2. **EPIC-01-STOR-05**: Usage Projection Algorithms
   - Status: Implemented ✅
   - Deliverable: `src/overlay/projection_algorithms.py`

3. **EPIC-01-STOR-06**: File Watcher Integration
   - Status: Implemented ✅
   - Integration: Built into `overlay_widget.py`

4. **Shared Infrastructure**: Data Schema and Atomic Writer
   - Status: Implemented ✅
   - Deliverables: `src/shared/data_schema.py`, `src/shared/atomic_writer.py`

## Success Criteria

### Functional Requirements
- [ ] Overlay window displays in top-right corner
- [ ] Window stays always-on-top over all applications
- [ ] Three progress bars show current usage with color coding:
  - Blue: <75% usage
  - Orange: 75-90% usage
  - Red: >90% usage
- [ ] Window is draggable by clicking anywhere
- [ ] Data updates automatically when JSON file changes (1-second polling)
- [ ] Projection algorithms calculate accurate usage trends
- [ ] Time-to-cap estimates display correctly

### Technical Requirements
- [ ] Fixed window size: 300x400 pixels
- [ ] Dark theme applied (#1e1e1e background, #cccccc text)
- [ ] QTimer-based file watching with <0.5% CPU usage
- [ ] Atomic file writes prevent data corruption
- [ ] Schema validation ensures data integrity
- [ ] All tests passing (projections, schema, overlay integration)

## Implementation Files

### Created Files
```
src/
├── overlay/
│   ├── __init__.py
│   ├── overlay_widget.py       # Main UI widget
│   └── projection_algorithms.py # Usage predictions
├── shared/
│   ├── __init__.py
│   ├── data_schema.py          # Schema validation
│   └── atomic_writer.py        # Atomic file writes
tests/
├── test_projections.py         # Projection algorithm tests
└── test_overlay.py             # Overlay widget tests (optional)
```

### Modified Files
```
data/usage-data.json            # Updated with complete schema
```

## Architecture

### Data Flow
```
┌─────────────────┐
│   Data File     │ usage-data.json
│   (JSON)        │
└────────┬────────┘
         │
         │ File Watcher (QTimer, 1s poll)
         │
         ▼
┌─────────────────┐
│  Schema         │ Validate structure
│  Validation     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Projection     │ Calculate trends
│  Algorithms     │ Estimate time-to-cap
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Overlay UI     │ Display metrics
│  (PyQt5)        │ Update progress bars
└─────────────────┘
```

### Color Coding Logic
```python
if usage >= 90:
    color = RED    # #e74c3c
elif usage >= 75:
    color = ORANGE # #f39c12
else:
    color = BLUE   # #007acc
```

## Testing Strategy

### Unit Tests
- `test_projections.py`: Test all projection algorithms
  - SMA calculation
  - Linear regression
  - Time-to-cap estimation
  - Confidence determination

### Integration Tests
- Schema validation with real data
- Atomic writes under concurrent access
- File watcher change detection

### Manual Tests
- Window appearance and positioning
- Always-on-top functionality
- Dragging behavior
- Real-time updates
- Multi-monitor support

## Risk Assessment

### Risk Level: MEDIUM

**Challenges**:
1. PyQt5 dependency may not be available in sandbox environment (Linux)
2. Windows-specific API calls (ctypes) won't work on Linux
3. UI testing requires display/X11 (not available in headless environment)

**Mitigation**:
- Implement all core logic (projections, schema, atomic writes)
- Create comprehensive unit tests for testable components
- Document manual testing procedures for Windows deployment
- Provide working code ready for Windows execution

## References

- **EPIC-01 Specification**: [EPIC-01.md](EPIC-01.md)
- **STOR-04 Details**: [EPIC-01-STOR-04.md](EPIC-01-STOR-04.md) - Overlay UI
- **STOR-05 Details**: [EPIC-01-STOR-05.md](EPIC-01-STOR-05.md) - Projections
- **STOR-06 Details**: [EPIC-01-STOR-06.md](EPIC-01-STOR-06.md) - File Watcher

## Notes

- This EPIC consolidates UI-related stories from EPIC-01 into a cohesive implementation
- All code follows EPIC-01 specifications and reference implementations
- PyQt5 code is production-ready but untested in current Linux environment
- Full manual testing should be performed on target Windows 11 platform

---

**Created**: 2025-11-09
**Epic Owner**: Orchestrator Mode
**Target Completion**: 2025-11-09
