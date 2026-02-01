"""
Exposure Detection Models
Data structures for exposure-centric analysis
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class ExposureCategory(Enum):
    """Categories of information exposure"""
    LOCATION = "location"
    IDENTITY = "identity"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    OPERATIONAL = "operational"
    TEMPORAL = "temporal"


class SeverityLevel(Enum):
    """Risk severity levels"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Significant risk
    MEDIUM = "medium"      # Moderate concern
    LOW = "low"            # Minor issue
    INFO = "info"          # Informational only


@dataclass
class Exposure:
    """Represents a single detected exposure"""
    id: str
    category: ExposureCategory
    severity: SeverityLevel
    title: str
    description: str
    evidence: Dict[str, Any]
    risk_explanation: str
    recommendations: List[str]
    confidence: float = 1.0  # 0.0 to 1.0
    discovered_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "risk_explanation": self.risk_explanation,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None
        }


@dataclass
class ExposureReport:
    """Complete exposure analysis report"""
    exposures: List[Exposure] = field(default_factory=list)
    total_count: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    primary_risks: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate summary statistics"""
        self.total_count = len(self.exposures)
        
        # Count by severity
        self.by_severity = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        # Count by category
        self.by_category = {
            "location": 0,
            "identity": 0,
            "technical": 0,
            "behavioral": 0,
            "operational": 0,
            "temporal": 0
        }
        
        # Extract primary risks
        self.primary_risks = []
        
        for exp in self.exposures:
            # Count severity
            self.by_severity[exp.severity.value] += 1
            
            # Count category
            self.by_category[exp.category.value] += 1
            
            # Collect high-impact risks
            if exp.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                if exp.risk_explanation not in self.primary_risks:
                    self.primary_risks.append(exp.risk_explanation)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "exposures": [exp.to_dict() for exp in self.exposures],
            "summary": {
                "total_count": self.total_count,
                "by_severity": self.by_severity,
                "by_category": self.by_category,
                "primary_risks": self.primary_risks
            }
        }
