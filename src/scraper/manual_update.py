#!/usr/bin/env python3
"""
Manual data entry script for Claude usage monitoring.

Use this when automated scraping is blocked by bot detection.
Simply enter the values you see on claude.ai/usage page.
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.shared.atomic_writer import atomic_write_json
from src.overlay.projection_algorithms import integrate_projections_into_data

DATA_FILE = ROOT / "data" / "usage-data.json"


def load_existing_data():
    """Load existing data to preserve historical data."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"historicalData": []}


def get_number(prompt, default=None):
    """Get a number from user input."""
    while True:
        value = input(prompt).strip()
        if not value and default is not None:
            return default
        try:
            return int(value)
        except ValueError:
            print("Please enter a valid number.")


def main():
    print("\n" + "="*60)
    print("Claude Usage Monitor - Manual Data Entry")
    print("="*60)
    print("\nOpen https://claude.ai/usage in your browser")
    print("Enter the values you see on the page:\n")

    # Get 4-Hour Cap
    print("4-Hour Cap")
    print("-" * 40)
    four_used = get_number("  Used: ")
    four_limit = get_number("  Limit [50]: ", 50)
    four_pct = round((four_used / four_limit) * 100, 1)

    # Get 1-Week Cap
    print("\n1-Week Cap")
    print("-" * 40)
    week_used = get_number("  Used: ")
    week_limit = get_number("  Limit [1000]: ", 1000)
    week_pct = round((week_used / week_limit) * 100, 1)

    # Get Opus 1-Week Cap
    print("\nOpus 1-Week Cap")
    print("-" * 40)
    opus_used = get_number("  Used: ")
    opus_limit = get_number("  Limit [500]: ", 500)
    opus_pct = round((opus_used / opus_limit) * 100, 1)

    # Build data structure
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    existing = load_existing_data()
    historical = existing.get("historicalData", [])
    
    # Add new historical point
    hd_point = {
        "timestamp": now_iso,
        "fourHourUsed": four_used,
        "weekUsed": week_used,
        "opusWeekUsed": opus_used,
    }
    historical.append(hd_point)
    historical = historical[-2016:]  # Keep last 7 days (2016 points at 5-min intervals)

    data = {
        "lastUpdated": now_iso,
        "metrics": {
            "fourHourCap": {
                "used": four_used,
                "limit": four_limit,
                "percentage": four_pct
            },
            "weekCap": {
                "used": week_used,
                "limit": week_limit,
                "percentage": week_pct
            },
            "opusWeekCap": {
                "used": opus_used,
                "limit": opus_limit,
                "percentage": opus_pct
            }
        },
        "historicalData": historical
    }

    # Integrate projections
    data = integrate_projections_into_data(data)

    # Display summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"4-Hour Cap:      {four_used} / {four_limit} ({four_pct}%)")
    print(f"1-Week Cap:      {week_used} / {week_limit} ({week_pct}%)")
    print(f"Opus 1-Week Cap: {opus_used} / {opus_limit} ({opus_pct}%)")
    print(f"\nHistorical data points: {len(historical)}")
    print("="*60)

    # Confirm
    confirm = input("\nSave this data? [Y/n]: ").strip().lower()
    if confirm in ('', 'y', 'yes'):
        atomic_write_json(DATA_FILE, data)
        print(f"\n✅ Data saved to {DATA_FILE}")
        print("The overlay UI should update within 1 second.\n")
    else:
        print("\n❌ Cancelled. No changes made.\n")


if __name__ == "__main__":
    main()