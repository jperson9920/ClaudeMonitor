import json
from pathlib import Path
from src.scraper.claude_scraper import ClaudeUsageScraper

def test_e2e_scraper(tmp_path):
    md_path = Path("docs/manual-inspection-results.md")
    assert md_path.exists(), "docs/manual-inspection-results.md must exist for integration test"
    md = md_path.read_text(encoding="utf-8")
    scraper = ClaudeUsageScraper(md)
    payload = scraper.extract_usage_data()
    components = payload["components"]
    # Expect three components
    assert len(components) == 3
    # Map by id
    by_id = {c["component_id"]: c for c in components}
    assert "current_session" in by_id
    assert "weekly_all_models" in by_id
    assert "weekly_opus" in by_id
    assert by_id["current_session"]["percent"] == 3.0
    assert by_id["weekly_all_models"]["percent"] == 36.0
    assert by_id["weekly_opus"]["percent"] == 19.0

    out_dir = Path("docs/scraper-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "sample-usage.json"
    # Write the components array as the expected artifact
    with out_file.open("w", encoding="utf-8") as fh:
        json.dump(components, fh, indent=2, ensure_ascii=False)

    # Basic check that file was written and contains expected keys
    saved = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(saved, list)
    assert saved[0]["component_id"]  # has id