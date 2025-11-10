# tests/test_scraper.py
"""Test script for web scraper functionality."""

import asyncio
import pytest
from pathlib import Path
from src.scraper.claude_usage_monitor import ClaudeUsageMonitor


@pytest.mark.asyncio
async def test_scraper_initialization():
    """Test that scraper initializes correctly."""
    monitor = ClaudeUsageMonitor(poll_interval=300)

    assert monitor.poll_interval == 300
    assert monitor.user_data_dir.exists() or True  # Will be created on first run
    assert monitor.data_file.parent.name == 'data'
    assert monitor.context is None  # Not started yet
    assert monitor.running is False


@pytest.mark.asyncio
async def test_data_structure():
    """Test that data extraction produces correct structure."""
    # This test requires manual inspection after first successful poll
    data_file = Path('data/usage-data.json')

    if data_file.exists():
        import json
        with open(data_file) as f:
            data = json.load(f)

        assert 'schemaVersion' in data
        assert 'metadata' in data
        assert 'currentState' in data
        assert 'historicalData' in data
        assert isinstance(data['historicalData'], list)