use std::env;
use std::fs;
use std::path::PathBuf;

/// Integration tests for resource resolution.
///
/// These tests exercise the three resolution paths:
/// - CLAUDE_SCRAPER_PATH override
/// - Bundled (mocked) resource_dir via TAURI_RESOURCE_DIR_MOCK
/// - Development fallback ../scraper/claude_scraper.py
///
/// Note: tests create and remove small temp files/directories and clean up env vars.
#[test]
fn test_env_override() {
    // Create a temp file to act as the override
    let mut tmp = env::temp_dir();
    tmp.push(format!("claude_scraper_test_override_{}.tmp", std::process::id()));
    fs::write(&tmp, b"print('ok')").expect("create override file");
    // Set override env
    env::set_var("CLAUDE_SCRAPER_PATH", &tmp);
    // Call resolver
    let resolved =
        tauri_app_lib::resource::resolve_scraper_path().expect("resolve_scraper_path should succeed");
    // Compare canonicalized paths
    let rcanon = resolved.canonicalize().expect("canonicalize resolved");
    let tcanon = tmp.canonicalize().expect("canonicalize tmp");
    assert_eq!(rcanon, tcanon);
    // Cleanup
    env::remove_var("CLAUDE_SCRAPER_PATH");
    let _ = fs::remove_file(&tmp);
}

#[test]
fn test_mock_resource_dir_bundle() {
    // Create a mock resource dir with scraper/<exe>
    let mut base = env::temp_dir();
    base.push(format!("claude_res_mock_{}", std::process::id()));
    let scraper_dir = base.join("scraper");
    fs::create_dir_all(&scraper_dir).expect("create scraper dir");
    let exe_name = if cfg!(windows) { "claude_scraper.exe" } else { "claude_scraper" };
    let exe_path = scraper_dir.join(exe_name);
    fs::write(&exe_path, b"").expect("create exe placeholder");
    // Set mock env for tests
    env::set_var("TAURI_RESOURCE_DIR_MOCK", &base);
    // Resolve
    let resolved =
        tauri_app_lib::resource::resolve_scraper_path().expect("resolve_scraper_path should succeed");
    let rcanon = resolved.canonicalize().expect("canonicalize resolved");
    let tcanon = exe_path.canonicalize().expect("canonicalize expected");
    assert_eq!(rcanon, tcanon);
    // Cleanup
    env::remove_var("TAURI_RESOURCE_DIR_MOCK");
    let _ = fs::remove_file(&exe_path);
    let _ = fs::remove_dir_all(&base);
}

#[test]
fn test_dev_fallback() {
    // Ensure no override or mock is present
    env::remove_var("CLAUDE_SCRAPER_PATH");
    env::remove_var("TAURI_RESOURCE_DIR_MOCK");

    // Create the development fallback file at ../scraper/claude_scraper.py relative to crate dir
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let dev_candidate = manifest_dir.join("../scraper/claude_scraper.py");
    if let Some(parent) = dev_candidate.parent() {
        fs::create_dir_all(parent).expect("create ../scraper dir");
    }
    fs::write(&dev_candidate, b"print('dev')").expect("create dev script");

    // Resolve
    let resolved =
        tauri_app_lib::resource::resolve_scraper_path().expect("resolve_scraper_path should succeed");
    // Compare canonicalized paths
    let rcanon = resolved.canonicalize().expect("canonicalize resolved");
    let dcanon = dev_candidate.canonicalize().expect("canonicalize dev_candidate");
    assert_eq!(rcanon, dcanon);

    // Cleanup
    let _ = fs::remove_file(&dev_candidate);
}