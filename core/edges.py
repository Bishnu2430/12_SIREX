from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid


@dataclass
class Edge:
    from_node: str
    to_node: str
    relation: str
    confidence: float
    explanation: str
    method: str
    evidence: List = field(default_factory=list)

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
