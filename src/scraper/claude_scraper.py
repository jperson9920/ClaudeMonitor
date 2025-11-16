"""
Claude usage scraper - high level orchestration.

Provides:
- ClaudeUsageScraper.extract_usage_data() -> dict
- ClaudeUsageScraper.dump_json(path)
- fallback helper extract_from_text(page_source)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re

from .extractors import UsageExtractor
from .models import UsageComponent

PERCENT_RE = re.compile(r"(\d{1,3})\s*%")

class ClaudeUsageScraper:
    def __init__(self, html: str):
        self.html = html
        self.extractor = UsageExtractor(html)

    def extract_usage_data(self) -> Dict[str, Any]:
        """
        Returns a payload:
        {
          "components": [ {id,label,percent,raw_text,scraped_at}, ... ],
          "found_components": int,
          "status": "ok"|"partial"|"error",
          "diagnostics": { "selectors_attempted": [...] },
          "timestamp": ISO8601
        }
        """
        scraped = self.extractor.extract_all()
        components = []
        found = 0
        diagnostics = {"selectors_attempted": []}
        status = "ok"

        for item in scraped:
            comp_id = item.get("component_id")
            label = item.get("label")
            percent = item.get("percent")
            raw_text = item.get("raw_text", "")
            scraped_at = item.get("scraped_at") or datetime.utcnow()
            selector_used = item.get("selector_used")
            if selector_used:
                diagnostics["selectors_attempted"].append({comp_id: selector_used})

            if percent is not None:
                found += 1

            # Build plain dicts to avoid Pydantic serialization differences across environments
            comp_dict = {
                "component_id": comp_id,
                "label": label,
                "percent": percent,
                "raw_text": raw_text,
                "scraped_at": scraped_at,
            }
            components.append(comp_dict)

        if found < len(components):
            status = "partial"
        if found == 0:
            status = "error"

        # Normalize components to plain dicts and convert datetimes to ISO strings
        normalized = []
        for c in components:
            # c may already be a dict or a Pydantic model; handle both
            if hasattr(c, "dict"):
                cd = c.dict()
            else:
                cd = dict(c)
            sa = cd.get("scraped_at")
            if isinstance(sa, datetime):
                cd["scraped_at"] = sa.isoformat() + "Z"
            normalized.append(cd)

        return {
            "components": normalized,
            "found_components": found,
            "status": status,
            "diagnostics": diagnostics,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def dump_json(self, path: str) -> None:
        payload = self.extract_usage_data()
        # Convert datetime objects to ISO strings inside components
        for c in payload["components"]:
            if isinstance(c.get("scraped_at"), datetime):
                c["scraped_at"] = c["scraped_at"].isoformat() + "Z"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload["components"], fh, indent=2, ensure_ascii=False)


def extract_from_text(page_source: str) -> List[Dict[str, Any]]:
    """
    Fallback text extractor: returns list of found {raw_text, percent}
    Uses regex to find all occurrences of '\d+% used' or '\d+%'.
    """
    results = []
    for m in PERCENT_RE.finditer(page_source or ""):
        txt = m.group(0)
        try:
            pct = float(m.group(1))
        except Exception:
            pct = None
        results.append({"raw_text": txt, "percent": pct})
    return results