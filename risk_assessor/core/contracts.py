"""Risk assessment contract models."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class RiskFactor:
    """Individual risk factor in the assessment."""
    category: str  # configuration, code, operational, testing, ownership
    factor_name: str
    impact_weight: float  # 0.0 to 1.0
    observed_value: str
    assessment: str


@dataclass
class RiskSummary:
    """Overall risk summary."""
    risk_score: float  # 0.0 to 1.0
    risk_level: str  # LOW, MEDIUM, HIGH
    confidence: float  # 0.0 to 1.0
    overall_assessment: str


@dataclass
class HistoricalContext:
    """Historical context for the risk assessment."""
    previous_similar_changes: int
    previous_incidents_in_region: int
    last_incident_cause: Optional[str]
    time_since_last_outage_days: Optional[int]


@dataclass
class ModelDetails:
    """Details about the risk assessment model."""
    model_version: str
    model_type: str
    trained_on_releases: Optional[int] = None
    last_updated: Optional[str] = None


@dataclass
class RiskContract:
    """Complete risk assessment contract."""
    id: str
    timestamp: str
    repository: str
    branch: str
    deployment_region: str
    risk_summary: RiskSummary
    factors: List[RiskFactor]
    recommendations: List[str]
    historical_context: HistoricalContext
    model_details: ModelDetails
    text_summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary format."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskContract':
        """Create contract from dictionary."""
        return cls(
            id=data['id'],
            timestamp=data['timestamp'],
            repository=data['repository'],
            branch=data['branch'],
            deployment_region=data['deployment_region'],
            risk_summary=RiskSummary(**data['risk_summary']),
            factors=[RiskFactor(**f) for f in data['factors']],
            recommendations=data['recommendations'],
            historical_context=HistoricalContext(**data['historical_context']),
            model_details=ModelDetails(**data['model_details']),
            text_summary=data['text_summary']
        )
