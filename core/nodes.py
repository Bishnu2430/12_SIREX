from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import uuid


@dataclass
class Node:
    type: str
    value: str
    source: str
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)
    evidence: List = field(default_factory=list)

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def update_confidence(self, new_conf):
        self.confidence = max(self.confidence, new_conf)
        self.last_updated = datetime.utcnow()
