use chrono::{DateTime, Duration, Utc};
use rusqlite::{params, Connection, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tauri::AppHandle;

use crate::scraper::UsageData;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageHistoryRecord {
    pub id: i64,
    pub timestamp: i64,
    pub usage_percent: f64,
    pub tokens_used: i64,
    pub tokens_limit: i64,
    pub tokens_remaining: i64,
    pub reset_time: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UsageStatistics {
    pub average_usage: f64,
    pub peak_usage: f64,
    pub min_usage: f64,
    pub total_records: i64,
}

pub struct Database {
    conn: Connection,
}

impl Database {
    /// Initialize database with schema
    pub fn new(app: &AppHandle) -> Result<Self, String> {
        let db_path = Self::get_db_path(app)?;
        let conn = Connection::open(&db_path)
            .map_err(|e| format!("Failed to open database: {}", e))?;

        // Create table if not exists
        conn.execute(
            "CREATE TABLE IF NOT EXISTS usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                usage_percent REAL NOT NULL,
                tokens_used INTEGER NOT NULL,
                tokens_limit INTEGER NOT NULL,
                tokens_remaining INTEGER NOT NULL,
                reset_time TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )",
            [],
        )
        .map_err(|e| format!("Failed to create table: {}", e))?;

        // Create index on timestamp
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_history(timestamp)",
            [],
        )
        .map_err(|e| format!("Failed to create index: {}", e))?;

        eprintln!("Database initialized at {:?}", db_path);

        Ok(Self { conn })
    }

    /// Get database file path
    fn get_db_path(app: &AppHandle) -> Result<PathBuf, String> {
        let app_dir = app
            .path_resolver()
            .app_data_dir()
            .ok_or("Failed to get app data directory")?;

        if !app_dir.exists() {
            std::fs::create_dir_all(&app_dir)
                .map_err(|e| format!("Failed to create app data directory: {}", e))?;
        }

        Ok(app_dir.join("usage_history.db"))
    }

    /// Record usage data
    pub fn record_usage(&self, data: &UsageData) -> Result<(), String> {
        let timestamp = Utc::now().timestamp();

        self.conn
            .execute(
                "INSERT INTO usage_history (timestamp, usage_percent, tokens_used, tokens_limit, tokens_remaining, reset_time)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
                params![
                    timestamp,
                    data.usage_percent,
                    data.tokens_used,
                    data.tokens_limit,
                    data.tokens_remaining,
                    data.reset_time,
                ],
            )
            .map_err(|e| format!("Failed to insert usage data: {}", e))?;

        eprintln!("Recorded usage: {}%", data.usage_percent);
        Ok(())
    }

    /// Get usage history for a time range
    pub fn get_history(
        &self,
        hours: i64,
    ) -> Result<Vec<UsageHistoryRecord>, String> {
        let cutoff = (Utc::now() - Duration::hours(hours)).timestamp();

        let mut stmt = self
            .conn
            .prepare(
                "SELECT id, timestamp, usage_percent, tokens_used, tokens_limit, tokens_remaining, reset_time
                 FROM usage_history
                 WHERE timestamp >= ?1
                 ORDER BY timestamp ASC",
            )
            .map_err(|e| format!("Failed to prepare statement: {}", e))?;

        let records = stmt
            .query_map(params![cutoff], |row| {
                Ok(UsageHistoryRecord {
                    id: row.get(0)?,
                    timestamp: row.get(1)?,
                    usage_percent: row.get(2)?,
                    tokens_used: row.get(3)?,
                    tokens_limit: row.get(4)?,
                    tokens_remaining: row.get(5)?,
                    reset_time: row.get(6)?,
                })
            })
            .map_err(|e| format!("Failed to query history: {}", e))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Failed to collect results: {}", e))?;

        Ok(records)
    }

    /// Get usage statistics for a time range
    pub fn get_statistics(&self, hours: i64) -> Result<UsageStatistics, String> {
        let cutoff = (Utc::now() - Duration::hours(hours)).timestamp();

        let mut stmt = self
            .conn
            .prepare(
                "SELECT
                    AVG(usage_percent) as avg_usage,
                    MAX(usage_percent) as peak_usage,
                    MIN(usage_percent) as min_usage,
                    COUNT(*) as total_records
                 FROM usage_history
                 WHERE timestamp >= ?1",
            )
            .map_err(|e| format!("Failed to prepare statement: {}", e))?;

        let stats = stmt
            .query_row(params![cutoff], |row| {
                Ok(UsageStatistics {
                    average_usage: row.get(0).unwrap_or(0.0),
                    peak_usage: row.get(1).unwrap_or(0.0),
                    min_usage: row.get(2).unwrap_or(0.0),
                    total_records: row.get(3).unwrap_or(0),
                })
            })
            .map_err(|e| format!("Failed to query statistics: {}", e))?;

        Ok(stats)
    }

    /// Cleanup old data (older than 90 days)
    pub fn cleanup_old_data(&self) -> Result<usize, String> {
        let ninety_days_ago = (Utc::now() - Duration::days(90)).timestamp();

        let deleted = self
            .conn
            .execute(
                "DELETE FROM usage_history WHERE timestamp < ?1",
                params![ninety_days_ago],
            )
            .map_err(|e| format!("Failed to cleanup old data: {}", e))?;

        if deleted > 0 {
            eprintln!("Cleaned up {} old records", deleted);
        }

        Ok(deleted)
    }

    /// Export all history as JSON string
    pub fn export_json(&self, hours: i64) -> Result<String, String> {
        let records = self.get_history(hours)?;
        serde_json::to_string_pretty(&records)
            .map_err(|e| format!("Failed to serialize JSON: {}", e))
    }

    /// Export all history as CSV string
    pub fn export_csv(&self, hours: i64) -> Result<String, String> {
        let records = self.get_history(hours)?;

        let mut csv = String::from("Timestamp,Usage Percent,Tokens Used,Tokens Limit,Tokens Remaining,Reset Time\n");

        for record in records {
            let dt = DateTime::from_timestamp(record.timestamp, 0)
                .unwrap_or_default();
            let reset = record.reset_time.unwrap_or_default();

            csv.push_str(&format!(
                "{},{},{},{},{},{}\n",
                dt.format("%Y-%m-%d %H:%M:%S"),
                record.usage_percent,
                record.tokens_used,
                record.tokens_limit,
                record.tokens_remaining,
                reset
            ));
        }

        Ok(csv)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_usage_statistics_default() {
        let stats = UsageStatistics {
            average_usage: 0.0,
            peak_usage: 0.0,
            min_usage: 0.0,
            total_records: 0,
        };
        assert_eq!(stats.total_records, 0);
    }
}
