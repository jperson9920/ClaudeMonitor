use std::env;
use std::path::PathBuf;
 // `tauri::api::path::resource_dir` removed for newer tauri versions.
 // Prefer reading TAURI_RESOURCE_DIR env var at runtime instead.

/// Resolve the path to the scraper executable or script.
///
/// Resolution order:
/// 1. If environment variable CLAUDE_SCRAPER_PATH is set, use that (must exist).
/// 2. If environment variable TAURI_RESOURCE_DIR_MOCK is set (testing), treat it as the Tauri resource dir.
/// 3. If tauri::api::path::resource_dir() returns Some(path), assume a bundled app and return
///    resource_dir()/scraper/claude_scraper{.exe} (OS-aware).
/// 4. Fallback to development path: ../scraper/claude_scraper.py (project-relative).
///
/// Returns Err(String) with actionable diagnostics if the resolved candidate does not exist.
pub fn resolve_scraper_path() -> Result<PathBuf, String> {
    // 1) Allow explicit override for testing / manual runs
    if let Ok(override_path) = env::var("CLAUDE_SCRAPER_PATH") {
        let p = PathBuf::from(&override_path);
        if p.exists() {
            return Ok(p);
        } else {
            return Err(format!(
                "CLAUDE_SCRAPER_PATH is set to '{}' but the file does not exist",
                override_path
            ));
        }
    }

    // 2) Testing hook: let tests mock the resource dir via env var
    if let Ok(mock_res_dir) = env::var("TAURI_RESOURCE_DIR_MOCK") {
        // avoid moving the String into PathBuf so we can reference it in diagnostics
        let candidate = PathBuf::from(&mock_res_dir);
        let mut candidate = candidate;
        candidate.push("scraper");
        let exe_name = if cfg!(windows) {
            "claude_scraper.exe"
        } else {
            "claude_scraper"
        };
        candidate.push(exe_name);
        if candidate.exists() {
            return Ok(candidate);
        } else {
            return Err(format!(
                "Mocked resource_dir '{}' -> candidate '{}' does not exist",
                mock_res_dir,
                candidate.display()
            ));
        }
    }

    // 3) Check if running as bundled Tauri app
    // Newer tauri versions don't expose `tauri::api::path::resource_dir` on the root crate.
    // Use the TAURI_RESOURCE_DIR environment variable (set by the runtime) as a fallback.
    if let Ok(res_dir_str) = env::var("TAURI_RESOURCE_DIR") {
        let res_dir = PathBuf::from(&res_dir_str);
        let mut candidate = res_dir.clone();
        candidate.push("scraper");
        let exe_name = if cfg!(windows) {
            "claude_scraper.exe"
        } else {
            "claude_scraper"
        };
        candidate.push(exe_name);
        if candidate.exists() {
            return Ok(candidate);
        } else {
            return Err(format!(
                "Tauri resource dir detected at '{}' but expected bundled scraper at '{}' was not found. \
                 Ensure the scraper binary was included in the Tauri build resources.",
                res_dir.display(),
                candidate.display()
            ));
        }
    }

    // 4) Development fallback: project-relative python script
    let candidate = PathBuf::from("../scraper/claude_scraper.py");
    if candidate.exists() {
        return Ok(candidate);
    }

    Err(format!(
        "Could not locate scraper. Checked (in order): CLAUDE_SCRAPER_PATH, TAURI resource dir, and development path '{}'. \
         For development use a local Python environment and place the script at ../scraper/claude_scraper.py, \
         or set CLAUDE_SCRAPER_PATH to point to your python script/executable. \
         (candidate '{}' not found)",
        "../scraper/claude_scraper.py",
        candidate.display()
    ))
}