# Selector definitions for Claude usage components
from typing import Dict, Any

SELECTORS: Dict[str, Dict[str, Any]] = {
    "current_session": {
        "label_text": "Current session",
        "percentage_css": "span.text-text-300.whitespace-nowrap.w-20.text-right",
        "percentage_xpath": "//span[@class='text-text-300 whitespace-nowrap w-20 text-right']",
        "reset_css": "p.text-text-500.whitespace-nowrap.text-sm",
    },
    "weekly_all_models": {
        "label_text": "All models",
        "percentage_css": "span.text-text-300.whitespace-nowrap.w-20.text-right",
        "percentage_xpath": "//span[@class='text-text-300 whitespace-nowrap w-20 text-right']",
        "reset_css": "p.text-text-500.whitespace-nowrap.text-sm",
    },
    "weekly_opus": {
        "label_text": "Opus only",
        "percentage_css": "span.text-text-300.whitespace-nowrap.w-20.text-right",
        "percentage_xpath": "//span[@class='text-text-300 whitespace-nowrap w-20 text-right']",
        "reset_css": "p.text-text-500.whitespace-nowrap.text-sm",
    },
}