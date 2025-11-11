"""Cloud-agnostic regional information and validation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class CloudProvider(Enum):
    """Supported cloud providers."""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    CUSTOM = "custom"
    BARE_METAL = "bare_metal"


@dataclass
class RegionalFeature:
    """Represents a feature available in a region."""
    name: str
    available: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'available': self.available,
            'metadata': self.metadata
        }


@dataclass
class RegionalInfo:
    """Information about a specific deployment region."""
    region_name: str
    cloud_provider: CloudProvider
    features: List[RegionalFeature] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_feature(self, feature_name: str) -> Optional[RegionalFeature]:
        """Get a feature by name."""
        for feature in self.features:
            if feature.name == feature_name:
                return feature
        return None
    
    def is_feature_available(self, feature_name: str) -> bool:
        """Check if a feature is available in this region."""
        feature = self.get_feature(feature_name)
        return feature.available if feature else False
    
    def get_missing_features(self) -> List[RegionalFeature]:
        """Get list of missing/unavailable features."""
        return [f for f in self.features if not f.available]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'region_name': self.region_name,
            'cloud_provider': self.cloud_provider.value,
            'features': [f.to_dict() for f in self.features],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegionalInfo':
        """Create RegionalInfo from dictionary."""
        return cls(
            region_name=data['region_name'],
            cloud_provider=CloudProvider(data['cloud_provider']),
            features=[
                RegionalFeature(**f) for f in data.get('features', [])
            ],
            metadata=data.get('metadata', {})
        )
