from typing import Optional, Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup
import re

from .selectors import SELECTORS
from .utils import parse_percentage_safe

"""
Rewritten extractor that avoids lxml to simplify local testing environments
(avoids compiling lxml on Windows). Extraction strategy:

1. CSS selector via BeautifulSoup
2. Search near label: find an element containing the label text, then look for
   nearby span elements or elements containing '%' in the same container.
3. Text fallback (regex search)
4. Progress bar style parsing (width: NN%)
"""


class UsageExtractor:
    PERCENT_RE = re.compile(r"(\d{1,3})\s*%")

    def __init__(self, html: str):
        self.html = html or ""
        # Use the built-in parser to avoid requiring lxml in test environments.
        self.soup = BeautifulSoup(self.html, "html.parser")

    def _by_css(self, selector: str) -> Optional[str]:
        if not selector:
            return None
        try:
            el = self.soup.select_one(selector)
        except Exception:
            return None
        if el:
            return el.get_text(strip=True)
        return None

    def _find_near_label(self, label_text: Optional[str]) -> Optional[str]:
        if not label_text:
            return None
        # Find elements whose text equals or contains the label (case-insensitive)
        label_lower = label_text.strip().lower()
        # Search common tag candidates first
        candidates = self.soup.find_all(
            lambda tag: tag.string and label_lower in tag.string.strip().lower()
        )
        for lab in candidates:
            # Look in the same parent for a span with percent-looking text
            parent = lab.parent
            if parent:
                # look for spans under parent
                spans = parent.find_all("span")
                for s in spans:
                    txt = s.get_text(strip=True)
                    if self.PERCENT_RE.search(txt):
                        return txt
                # look for any text nodes under parent containing %
                txt = parent.get_text(" ", strip=True)
                m = self.PERCENT_RE.search(txt)
                if m:
                    return m.group(0)
            # look at next siblings
            sib = lab.find_next_sibling()
            while sib:
                txt = sib.get_text(strip=True)
                if self.PERCENT_RE.search(txt):
                    return txt
                sib = sib.find_next_sibling()
        return None

    def _from_progress_style(self) -> Optional[str]:
        # Look for inline style width: XX% on elements (progress bars)
        for el in self.soup.find_all(style=True):
            style = el.get("style") or ""
            m = re.search(r"width\s*:\s*(\d{1,3})\s*%?", style)
            if m:
                return f"{m.group(1)}% used"
        return None

    def _by_text_fallback(self, label_text: Optional[str]) -> Optional[str]:
        if not label_text:
            # global first percent match
            m = self.PERCENT_RE.search(self.html)
            return m.group(0) if m else None
        idx = self.html.lower().find(label_text.lower())
        if idx == -1:
            m = self.PERCENT_RE.search(self.html)
            return m.group(0) if m else None
        window = self.html[idx : idx + 600]
        m = self.PERCENT_RE.search(window)
        return m.group(0) if m else None

    def extract_component(self, component_id: str) -> Dict[str, Any]:
        cfg = SELECTORS.get(component_id, {})
        label = cfg.get("label_text", component_id)
        scraped_at = datetime.utcnow()
        raw_text = None
        percent = None
        selector_used = None

        # 1) CSS percentage selector — attempt ancestor-scoped search near the label first,
        # then fall back to a global selector. Walk up a few ancestor levels to find
        # the percentage element that belongs to the same block as the label.
        css = cfg.get("percentage_css")
        if css:
            raw = None
            selector_used = None
            try:
                label_lower = label.strip().lower()
                label_el = self.soup.find(
                    lambda tag: tag.string and label_lower in tag.string.strip().lower()
                )
            except Exception:
                label_el = None

            if label_el:
                # try ancestors up to 4 levels for a scoped match
                max_levels = 4
                level = 0
                ancestor = label_el
                while ancestor is not None and level <= max_levels:
                    try:
                        scoped = ancestor.select_one(css)
                        if scoped:
                            raw = scoped.get_text(strip=True)
                            selector_used = f"scoped_css(level={level}):{css}"
                            break
                    except Exception:
                        pass
                    ancestor = ancestor.parent
                    level += 1

            # fallback to global css selector if scoping didn't yield a result
            if raw is None:
                try:
                    raw_global = self._by_css(css)
                    if raw_global:
                        raw = raw_global
                        selector_used = f"css:{css}"
                except Exception:
                    raw = None

            if raw:
                raw_text = raw

        # 2) Look near label (sibling/parent search)
        if raw_text is None:
            near = self._find_near_label(label)
            if near:
                raw_text = near
                selector_used = "near_label_search"

        # 3) Try reset_css sibling heuristic
        if raw_text is None:
            reset_css = cfg.get("reset_css")
            if reset_css:
                try:
                    el = self.soup.select_one(reset_css)
                    if el:
                        # search following siblings for percent text
                        sib = el.find_next_sibling()
                        while sib:
                            txt = sib.get_text(strip=True)
                            if txt and self.PERCENT_RE.search(txt):
                                raw_text = txt
                                selector_used = f"reset_sibling_css:{reset_css}"
                                break
                            sib = sib.find_next_sibling()
                except Exception:
                    pass

        # 4) Progress bar style width
        if raw_text is None:
            prog = self._from_progress_style()
            if prog:
                raw_text = prog
                selector_used = "style_width_progress"

        # 5) Text fallback
        if raw_text is None:
            fb = self._by_text_fallback(label)
            if fb:
                raw_text = fb
                selector_used = "text_fallback"

        # 6) Last resort: any percent in doc
        if raw_text is None:
            m = self.PERCENT_RE.search(self.html)
            if m:
                raw_text = m.group(0)
                selector_used = "any_percent_in_doc"

        if raw_text:
            percent = parse_percentage_safe(raw_text)
        else:
            raw_text = ""
            percent = None

        return {
            "component_id": component_id,
            "label": label,
            "percent": percent,
            "raw_text": raw_text,
            "scraped_at": scraped_at,
            "selector_used": selector_used,
        }

    def extract_all(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for comp in SELECTORS.keys():
            results.append(self.extract_component(comp))
        return results