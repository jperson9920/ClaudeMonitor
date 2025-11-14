# EPIC-07: Historical Data & Visualization

## Problem Statement
Users want to track their Claude usage patterns over time to understand trends, identify peak usage periods, and better manage their monthly caps. Currently, the application only shows real-time usage without any historical context or visualization. Implementing historical data tracking and charts would provide valuable insights into usage behavior.

## Goal
Implement comprehensive historical data tracking and visualization:
- Record usage data at regular intervals
- Store historical usage in local database
- Visualize usage trends with interactive charts
- Provide daily, weekly, and monthly views
- Export historical data for analysis

## Success Criteria
- [ ] Usage data recorded every polling cycle
- [ ] Historical data stored in SQLite database
- [ ] Interactive charts display usage over time
- [ ] Multiple time range views (24h, 7d, 30d)
- [ ] Chart shows reset periods clearly
- [ ] Data persists across app restarts
- [ ] Historical data can be exported
- [ ] Performance remains acceptable with large datasets

## Dependencies
- **Completed**: EPIC-01 through EPIC-06
- SQLite or similar embedded database
- Chart library (e.g., Chart.js, Recharts)

## Stories

### STORY-01: Database Infrastructure
**Description**: Set up local database for historical data storage.

**Tasks**:
- Add SQLite dependency to Cargo.toml
- Create database schema for usage history
- Implement database initialization
- Create data access layer (queries)
- Add database migration support

**Acceptance Criteria**:
- SQLite database created on first run
- Schema includes: timestamp, usage_percent, tokens_used, tokens_limit
- Database persists in app data directory
- Migrations handle schema changes

---

### STORY-02: Usage Data Recording
**Description**: Record usage data automatically during polling.

**Tasks**:
- Integrate database writes into polling loop
- Record data after each successful poll
- Add timestamp to each record
- Implement data retention policy (90 days)
- Handle database write errors gracefully

**Acceptance Criteria**:
- Data recorded every poll cycle (every 5 minutes)
- Includes all relevant usage metrics
- Old data automatically purged after 90 days
- Write failures don't crash polling

---

### STORY-03: Chart Component
**Description**: Create interactive chart component for visualization.

**Tasks**:
- Add chart library dependency
- Create Chart component in React
- Implement line chart for usage over time
- Add time range selector (24h, 7d, 30d)
- Style chart to match app theme

**Acceptance Criteria**:
- Chart displays usage percentage over time
- Smooth animations when data updates
- Responsive to window resizing
- Matches app color scheme

---

### STORY-04: Data Queries
**Description**: Implement efficient queries for different time ranges.

**Tasks**:
- Create query for last 24 hours
- Create query for last 7 days
- Create query for last 30 days
- Add data aggregation for performance
- Implement caching for recent queries

**Acceptance Criteria**:
- Queries return data in <100ms
- Data properly aggregated for long time ranges
- Cache invalidates on new data
- Handles missing data gracefully

---

### STORY-05: Reset Period Indicators
**Description**: Show usage reset periods clearly on charts.

**Tasks**:
- Detect usage resets in historical data
- Add vertical lines to mark reset times
- Add labels for reset periods
- Calculate usage per period
- Show period statistics

**Acceptance Criteria**:
- Reset periods clearly marked
- Labels show "Period 1", "Period 2", etc.
- Statistics show max usage per period
- Visual distinction between periods

---

### STORY-06: Historical View UI
**Description**: Create dedicated historical view page.

**Tasks**:
- Add "History" tab or button to UI
- Create full-page chart view
- Add statistics panel (avg usage, peak times)
- Implement zoom and pan controls
- Add data export button

**Acceptance Criteria**:
- History accessible from main UI
- Chart takes full content area
- Statistics update with time range
- Intuitive zoom/pan controls

---

## Technical Specifications

### Database Schema

```sql
CREATE TABLE usage_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    usage_percent REAL NOT NULL,
    tokens_used INTEGER NOT NULL,
    tokens_limit INTEGER NOT NULL,
    tokens_remaining INTEGER NOT NULL,
    reset_time TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);

CREATE INDEX idx_timestamp ON usage_history(timestamp);
```

### Data Retention

```rust
// Auto-delete records older than 90 days
fn cleanup_old_data(db: &Connection) -> Result<(), rusqlite::Error> {
    let ninety_days_ago = Utc::now() - Duration::days(90);
    db.execute(
        "DELETE FROM usage_history WHERE timestamp < ?1",
        params![ninety_days_ago.timestamp()],
    )?;
    Ok(())
}
```

### Tauri Commands

```rust
#[tauri::command]
async fn get_usage_history(
    time_range: String,
) -> Result<Vec<UsageHistoryRecord>, String>

#[tauri::command]
async fn get_usage_statistics(
    time_range: String,
) -> Result<UsageStatistics, String>

#[tauri::command]
async fn export_usage_history(
    format: String,
) -> Result<String, String>
```

## File Structure

```
src/
├── components/
│   ├── Chart.tsx                 # Chart visualization component
│   ├── HistoryView.tsx           # Historical view page
│   └── Statistics.tsx            # Usage statistics panel
└── App.tsx

src-tauri/src/
├── database.rs                   # Database layer
└── history.rs                    # Historical data management
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database corruption | High | Regular backups, validation |
| Performance with large datasets | Medium | Data aggregation, indexing |
| Chart rendering lag | Low | Virtualization, sampling |
| Storage growth | Medium | Auto-cleanup, retention policy |

## Performance Considerations

- Aggregate data for time ranges > 7 days
- Index timestamp column for fast queries
- Limit chart data points to 500 max
- Cache recent queries for 1 minute
- Background cleanup during idle time

## Notes

- Historical data provides valuable usage insights
- Charts should be intuitive and interactive
- Data retention balances utility and storage
- Export enables external analysis
