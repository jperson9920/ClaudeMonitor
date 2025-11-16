from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UsageComponent(BaseModel):
    component_id: str
    label: str
    percent: Optional[float]
    raw_text: str
    scraped_at: datetime