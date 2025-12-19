from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AbsaResultDTO:
    source_id: str          # ID của comment
    source_text: str        # Nội dung comment
    aspect: str             # Khía cạnh (VD: Price, Food)
    sentiment: str          # Cảm xúc (Positive, Negative)
    confidence: float       # Độ tin cậy
    correction: str = None  # Chỗ để con người sửa sai
    processed_at: datetime = field(default_factory=datetime.utcnow)