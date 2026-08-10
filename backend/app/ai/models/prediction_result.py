from dataclasses import dataclass, field
from typing import Any


@dataclass
class PredictionResult:
    disease: str
    confidence: float
    top_predictions: list[dict[str, Any]] = field(default_factory=list)