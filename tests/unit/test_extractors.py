import pytest
from src.scraper.extractors import UsageExtractor
from src.scraper.selectors import SELECTORS

SAMPLE_FRAGMENT = """
<div>
  <p class="text-text-500 whitespace-nowrap text-sm">Current session</p>
  <span class="text-text-300 whitespace-nowrap w-20 text-right">3% used</span>
</div>
"""

def test_css_extraction():
    ex = UsageExtractor(SAMPLE_FRAGMENT)
    res = ex.extract_component("current_session")
    assert res["label"] == "Current session"
    assert res["raw_text"] == "3% used"
    assert res["percent"] == 3.0

def test_xpath_fallback():
    # provide CSS that doesn't match but XPath does
    fragment = SAMPLE_FRAGMENT.replace("text-text-300", "text-text-XYZ")
    # add an element matching xpath (simulate class string exactly)
    fragment += '<span class="text-text-300 whitespace-nowrap w-20 text-right">3% used</span>'
    ex = UsageExtractor(fragment)
    # intentionally remove css selector to force xpath path by altering SELECTORS at runtime
    sel = SELECTORS["current_session"].copy()
    sel["percentage_css"] = ".nonexistent-class"
    ex.SELECTORS = {"current_session": sel}  # monkeypatch local only
    res = ex.extract_component("current_session")
    assert res["percent"] == 3.0

def test_text_fallback():
    fragment = "<div>Usage: 36% used - All models</div>"
    ex = UsageExtractor(fragment)
    res = ex.extract_component("weekly_all_models")
    # should find 36% via text fallback
    assert res["percent"] == 36.0

def test_missing_elements():
    fragment = "<html><body>No usage info here</body></html>"
    ex = UsageExtractor(fragment)
    res = ex.extract_component("current_session")
    assert res["percent"] is None
    assert res["raw_text"] == ""