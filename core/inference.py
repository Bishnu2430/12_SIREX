from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid


@dataclass
class InferenceRecord:
    hypothesis: str
    nodes_involved: List[str]
    edges_created: List[str]
    agent_reasoning: str
    confidence: float
    status: str = "pending"

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
