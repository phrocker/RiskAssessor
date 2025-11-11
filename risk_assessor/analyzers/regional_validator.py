"""Regional validators for different cloud providers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from risk_assessor.core.regional_info import RegionalInfo, RegionalFeature, CloudProvider


class RegionalValidator(ABC):
    """Base class for regional validators."""
    
    @abstractmethod
    def validate_region(self, region_name: str) -> RegionalInfo:
        """
        Validate and gather information about a region.
        
        Args:
            region_name: Name of the region to validate
            
        Returns:
            RegionalInfo object with region details
        """
        pass
    
    @abstractmethod
    def get_feature_availability(
        self, 
        region_name: str, 
        features: List[str]
    ) -> Dict[str, bool]:
        """
        Check feature availability in a region.
        
        Args:
            region_name: Name of the region
            features: List of feature names to check
            
        Returns:
            Dictionary mapping feature names to availability
        """
        pass


class AWSRegionalValidator(RegionalValidator):
    """Regional validator for AWS."""
    
    # Standard AWS features that might not be available in all regions
    STANDARD_FEATURES = [
        'ec2',
        'rds',
        's3',
        'lambda',
        'dynamodb',
        'eks',
        'ecs',
        'elasticache',
        'kinesis',
        'sqs',
        'sns'
    ]
    
    def __init__(self, region_configs: Optional[Dict[str, Any]] = None):
        """
        Initialize AWS regional validator.
        
        Args:
            region_configs: Optional configuration mapping regions to features
        """
        self.region_configs = region_configs or {}
    
    def validate_region(self, region_name: str) -> RegionalInfo:
        """Validate AWS region and gather information."""
        features = []
        
        # Get region-specific config or use defaults
        region_config = self.region_configs.get(region_name, {})
        available_features = region_config.get('features', self.STANDARD_FEATURES)
        
        for feature in self.STANDARD_FEATURES:
            features.append(RegionalFeature(
                name=feature,
                available=feature in available_features,
                metadata={'service_name': feature}
            ))
        
        return RegionalInfo(
            region_name=region_name,
            cloud_provider=CloudProvider.AWS,
            features=features,
            metadata={
                'region_type': region_config.get('region_type', 'standard'),
                'availability_zones': region_config.get('availability_zones', 3)
            }
        )
    
    def get_feature_availability(
        self, 
        region_name: str, 
        features: List[str]
    ) -> Dict[str, bool]:
        """Check AWS feature availability."""
        region_config = self.region_configs.get(region_name, {})
        available_features = region_config.get('features', self.STANDARD_FEATURES)
        
        return {
            feature: feature in available_features
            for feature in features
        }


class AzureRegionalValidator(RegionalValidator):
    """Regional validator for Azure."""
    
    STANDARD_FEATURES = [
        'virtual_machines',
        'app_service',
        'sql_database',
        'cosmos_db',
        'storage',
        'functions',
        'aks',
        'container_instances',
        'redis_cache',
        'service_bus'
    ]
    
    def __init__(self, region_configs: Optional[Dict[str, Any]] = None):
        """
        Initialize Azure regional validator.
        
        Args:
            region_configs: Optional configuration mapping regions to features
        """
        self.region_configs = region_configs or {}
    
    def validate_region(self, region_name: str) -> RegionalInfo:
        """Validate Azure region and gather information."""
        features = []
        
        region_config = self.region_configs.get(region_name, {})
        available_features = region_config.get('features', self.STANDARD_FEATURES)
        
        for feature in self.STANDARD_FEATURES:
            features.append(RegionalFeature(
                name=feature,
                available=feature in available_features,
                metadata={'service_name': feature}
            ))
        
        return RegionalInfo(
            region_name=region_name,
            cloud_provider=CloudProvider.AZURE,
            features=features,
            metadata={
                'region_type': region_config.get('region_type', 'standard'),
                'paired_region': region_config.get('paired_region')
            }
        )
    
    def get_feature_availability(
        self, 
        region_name: str, 
        features: List[str]
    ) -> Dict[str, bool]:
        """Check Azure feature availability."""
        region_config = self.region_configs.get(region_name, {})
        available_features = region_config.get('features', self.STANDARD_FEATURES)
        
        return {
            feature: feature in available_features
            for feature in features
        }


class GCPRegionalValidator(RegionalValidator):
    """Regional validator for Google Cloud Platform."""
    
    STANDARD_FEATURES = [
        'compute_engine',
        'cloud_sql',
        'cloud_storage',
        'cloud_functions',
        'cloud_run',
        'gke',
        'firestore',
        'bigtable',
        'memorystore',
        'pub_sub'
    ]
    
    def __init__(self, region_configs: Optional[Dict[str, Any]] = None):
        """
        Initialize GCP regional validator.
        
        Args:
            region_configs: Optional configuration mapping regions to features
        """
        self.region_configs = region_configs or {}
    
    def validate_region(self, region_name: str) -> RegionalInfo:
        """Validate GCP region and gather information."""
        features = []
        
        region_config = self.region_configs.get(region_name, {})
        available_features = region_config.get('features', self.STANDARD_FEATURES)
        
        for feature in self.STANDARD_FEATURES:
            features.append(RegionalFeature(
                name=feature,
                available=feature in available_features,
                metadata={'service_name': feature}
            ))
        
        return RegionalInfo(
            region_name=region_name,
            cloud_provider=CloudProvider.GCP,
            features=features,
            metadata={
                'region_type': region_config.get('region_type', 'standard'),
                'zones': region_config.get('zones', 3)
            }
        )
    
    def get_feature_availability(
        self, 
        region_name: str, 
        features: List[str]
    ) -> Dict[str, bool]:
        """Check GCP feature availability."""
        region_config = self.region_configs.get(region_name, {})
        available_features = region_config.get('features', self.STANDARD_FEATURES)
        
        return {
            feature: feature in available_features
            for feature in features
        }


class CustomRegionalValidator(RegionalValidator):
    """Regional validator for custom/bare-metal infrastructure."""
    
    def __init__(self, region_configs: Dict[str, Any]):
        """
        Initialize custom regional validator.
        
        Args:
            region_configs: Configuration mapping regions to features
                Format: {
                    'region-name': {
                        'features': ['feature1', 'feature2'],
                        'metadata': {...}
                    }
                }
        """
        self.region_configs = region_configs
    
    def validate_region(self, region_name: str) -> RegionalInfo:
        """Validate custom region and gather information."""
        region_config = self.region_configs.get(region_name, {})
        
        if not region_config:
            # Return empty region info if not configured
            return RegionalInfo(
                region_name=region_name,
                cloud_provider=CloudProvider.CUSTOM,
                features=[],
                metadata={'configured': False}
            )
        
        features = []
        feature_configs = region_config.get('features', [])
        
        # Support both simple list and detailed feature configs
        for feature_config in feature_configs:
            if isinstance(feature_config, str):
                features.append(RegionalFeature(
                    name=feature_config,
                    available=True,
                    metadata={}
                ))
            elif isinstance(feature_config, dict):
                features.append(RegionalFeature(
                    name=feature_config['name'],
                    available=feature_config.get('available', True),
                    metadata=feature_config.get('metadata', {})
                ))
        
        return RegionalInfo(
            region_name=region_name,
            cloud_provider=CloudProvider.CUSTOM,
            features=features,
            metadata=region_config.get('metadata', {'configured': True})
        )
    
    def get_feature_availability(
        self, 
        region_name: str, 
        features: List[str]
    ) -> Dict[str, bool]:
        """Check custom region feature availability."""
        region_config = self.region_configs.get(region_name, {})
        
        if not region_config:
            return {feature: False for feature in features}
        
        feature_configs = region_config.get('features', [])
        available_features = set()
        
        for feature_config in feature_configs:
            if isinstance(feature_config, str):
                available_features.add(feature_config)
            elif isinstance(feature_config, dict):
                if feature_config.get('available', True):
                    available_features.add(feature_config['name'])
        
        return {
            feature: feature in available_features
            for feature in features
        }


def get_regional_validator(
    cloud_provider: str,
    region_configs: Optional[Dict[str, Any]] = None
) -> RegionalValidator:
    """
    Factory function to get the appropriate regional validator.
    
    Args:
        cloud_provider: Cloud provider name (aws, azure, gcp, custom, bare_metal)
        region_configs: Optional region configuration
        
    Returns:
        RegionalValidator instance
        
    Raises:
        ValueError: If cloud provider is not supported
    """
    provider_lower = cloud_provider.lower()
    
    if provider_lower == 'aws':
        return AWSRegionalValidator(region_configs)
    elif provider_lower == 'azure':
        return AzureRegionalValidator(region_configs)
    elif provider_lower == 'gcp':
        return GCPRegionalValidator(region_configs)
    elif provider_lower in ('custom', 'bare_metal'):
        if not region_configs:
            raise ValueError("region_configs required for custom/bare_metal providers")
        return CustomRegionalValidator(region_configs)
    else:
        raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
