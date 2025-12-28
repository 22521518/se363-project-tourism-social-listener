from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AbsaResultDTO:
    source_id: str
    source_text: str
    aspect: str
    sentiment: str
    confidence: float
    correction: str = None
    processed_at: datetime = field(default_factory=datetime.utcnow)
