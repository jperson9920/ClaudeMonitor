"""
Claude Usage Monitor - Web Scraper Module

This module implements the core scraping functionality to extract usage data
from claude.ai/settings/usage using undetected-chromedriver.

Target: https://claude.ai/settings/usage
Strategy: Locate static text "Time until reset" and extract adjacent usage percentages
Components: Current session, Weekly limits (All models), Weekly limits (Opus only)

Reference: EPIC-01-STOR-01, EPIC-02-STOR-01
"""

# Implementation to follow in EPIC-02