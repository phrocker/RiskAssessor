"""Tests for regional validation functionality."""

import pytest
from risk_assessor.core.regional_info import (
    RegionalInfo, RegionalFeature, CloudProvider
)
from risk_assessor.analyzers.regional_validator import (
    AWSRegionalValidator,
    AzureRegionalValidator,
    GCPRegionalValidator,
    CustomRegionalValidator,
    get_regional_validator
)


def test_regional_feature_creation():
    """Test creating a regional feature."""
    feature = RegionalFeature(
        name='lambda',
        available=True,
        metadata={'version': '2.0'}
    )
    
    assert feature.name == 'lambda'
    assert feature.available is True
    assert feature.metadata['version'] == '2.0'
    
    # Test to_dict
    feature_dict = feature.to_dict()
    assert feature_dict['name'] == 'lambda'
    assert feature_dict['available'] is True


def test_regional_info_creation():
    """Test creating regional info."""
    features = [
        RegionalFeature('ec2', True),
        RegionalFeature('s3', True),
        RegionalFeature('lambda', False)
    ]
    
    info = RegionalInfo(
        region_name='us-east-1',
        cloud_provider=CloudProvider.AWS,
        features=features,
        metadata={'zones': 3}
    )
    
    assert info.region_name == 'us-east-1'
    assert info.cloud_provider == CloudProvider.AWS
    assert len(info.features) == 3
    assert info.metadata['zones'] == 3


def test_regional_info_get_feature():
    """Test getting a feature from regional info."""
    features = [
        RegionalFeature('ec2', True),
        RegionalFeature('lambda', False)
    ]
    
    info = RegionalInfo(
        region_name='us-west-2',
        cloud_provider=CloudProvider.AWS,
        features=features
    )
    
    # Test getting existing feature
    feature = info.get_feature('ec2')
    assert feature is not None
    assert feature.name == 'ec2'
    assert feature.available is True
    
    # Test getting non-existent feature
    feature = info.get_feature('nonexistent')
    assert feature is None


def test_regional_info_is_feature_available():
    """Test checking feature availability."""
    features = [
        RegionalFeature('ec2', True),
        RegionalFeature('lambda', False)
    ]
    
    info = RegionalInfo(
        region_name='us-west-2',
        cloud_provider=CloudProvider.AWS,
        features=features
    )
    
    assert info.is_feature_available('ec2') is True
    assert info.is_feature_available('lambda') is False
    assert info.is_feature_available('nonexistent') is False


def test_regional_info_get_missing_features():
    """Test getting missing features."""
    features = [
        RegionalFeature('ec2', True),
        RegionalFeature('lambda', False),
        RegionalFeature('eks', False)
    ]
    
    info = RegionalInfo(
        region_name='us-west-2',
        cloud_provider=CloudProvider.AWS,
        features=features
    )
    
    missing = info.get_missing_features()
    assert len(missing) == 2
    assert all(not f.available for f in missing)
    assert set(f.name for f in missing) == {'lambda', 'eks'}


def test_regional_info_serialization():
    """Test serialization and deserialization."""
    features = [
        RegionalFeature('ec2', True, {'version': '1.0'}),
        RegionalFeature('lambda', False)
    ]
    
    info = RegionalInfo(
        region_name='us-east-1',
        cloud_provider=CloudProvider.AWS,
        features=features,
        metadata={'zones': 3}
    )
    
    # Test to_dict
    info_dict = info.to_dict()
    assert info_dict['region_name'] == 'us-east-1'
    assert info_dict['cloud_provider'] == 'aws'
    assert len(info_dict['features']) == 2
    
    # Test from_dict
    restored = RegionalInfo.from_dict(info_dict)
    assert restored.region_name == 'us-east-1'
    assert restored.cloud_provider == CloudProvider.AWS
    assert len(restored.features) == 2
    assert restored.metadata['zones'] == 3


def test_aws_regional_validator_default():
    """Test AWS regional validator with defaults."""
    validator = AWSRegionalValidator()
    
    info = validator.validate_region('us-east-1')
    
    assert info.region_name == 'us-east-1'
    assert info.cloud_provider == CloudProvider.AWS
    assert len(info.features) > 0
    
    # All standard features should be available by default
    for feature in info.features:
        assert feature.available is True


def test_aws_regional_validator_with_config():
    """Test AWS regional validator with custom config."""
    config = {
        'us-gov-west-1': {
            'features': ['ec2', 's3', 'rds'],  # Limited features in GovCloud
            'region_type': 'govcloud',
            'availability_zones': 2
        }
    }
    
    validator = AWSRegionalValidator(config)
    info = validator.validate_region('us-gov-west-1')
    
    assert info.region_name == 'us-gov-west-1'
    assert info.metadata['region_type'] == 'govcloud'
    assert info.metadata['availability_zones'] == 2
    
    # Check feature availability
    assert info.is_feature_available('ec2') is True
    assert info.is_feature_available('s3') is True
    assert info.is_feature_available('lambda') is False


def test_aws_feature_availability():
    """Test AWS feature availability check."""
    config = {
        'us-west-2': {
            'features': ['ec2', 's3', 'lambda']
        }
    }
    
    validator = AWSRegionalValidator(config)
    availability = validator.get_feature_availability(
        'us-west-2',
        ['ec2', 's3', 'lambda', 'eks']
    )
    
    assert availability['ec2'] is True
    assert availability['s3'] is True
    assert availability['lambda'] is True
    assert availability['eks'] is False


def test_azure_regional_validator():
    """Test Azure regional validator."""
    validator = AzureRegionalValidator()
    
    info = validator.validate_region('eastus')
    
    assert info.region_name == 'eastus'
    assert info.cloud_provider == CloudProvider.AZURE
    assert len(info.features) > 0


def test_azure_regional_validator_with_config():
    """Test Azure regional validator with custom config."""
    config = {
        'westeurope': {
            'features': ['virtual_machines', 'storage', 'sql_database'],
            'region_type': 'standard',
            'paired_region': 'northeurope'
        }
    }
    
    validator = AzureRegionalValidator(config)
    info = validator.validate_region('westeurope')
    
    assert info.metadata['paired_region'] == 'northeurope'
    assert info.is_feature_available('virtual_machines') is True
    assert info.is_feature_available('aks') is False


def test_gcp_regional_validator():
    """Test GCP regional validator."""
    validator = GCPRegionalValidator()
    
    info = validator.validate_region('us-central1')
    
    assert info.region_name == 'us-central1'
    assert info.cloud_provider == CloudProvider.GCP
    assert len(info.features) > 0


def test_gcp_regional_validator_with_config():
    """Test GCP regional validator with custom config."""
    config = {
        'asia-northeast1': {
            'features': ['compute_engine', 'cloud_storage', 'gke'],
            'zones': 3
        }
    }
    
    validator = GCPRegionalValidator(config)
    info = validator.validate_region('asia-northeast1')
    
    assert info.metadata['zones'] == 3
    assert info.is_feature_available('compute_engine') is True
    assert info.is_feature_available('cloud_functions') is False


def test_custom_regional_validator_simple():
    """Test custom regional validator with simple config."""
    config = {
        'datacenter-1': {
            'features': ['kubernetes', 'postgresql', 'redis'],
            'metadata': {
                'location': 'on-premises',
                'capacity': 'high'
            }
        }
    }
    
    validator = CustomRegionalValidator(config)
    info = validator.validate_region('datacenter-1')
    
    assert info.region_name == 'datacenter-1'
    assert info.cloud_provider == CloudProvider.CUSTOM
    assert len(info.features) == 3
    assert info.is_feature_available('kubernetes') is True
    assert info.is_feature_available('postgresql') is True
    assert info.metadata['location'] == 'on-premises'


def test_custom_regional_validator_detailed():
    """Test custom regional validator with detailed feature config."""
    config = {
        'bare-metal-region': {
            'features': [
                {
                    'name': 'load_balancer',
                    'available': True,
                    'metadata': {'type': 'nginx'}
                },
                {
                    'name': 'object_storage',
                    'available': False,
                    'metadata': {'reason': 'not yet deployed'}
                }
            ],
            'metadata': {'provider': 'bare-metal'}
        }
    }
    
    validator = CustomRegionalValidator(config)
    info = validator.validate_region('bare-metal-region')
    
    assert len(info.features) == 2
    assert info.is_feature_available('load_balancer') is True
    assert info.is_feature_available('object_storage') is False
    
    lb_feature = info.get_feature('load_balancer')
    assert lb_feature.metadata['type'] == 'nginx'


def test_custom_regional_validator_unconfigured():
    """Test custom regional validator with unconfigured region."""
    config = {
        'region-1': {
            'features': ['feature1']
        }
    }
    
    validator = CustomRegionalValidator(config)
    info = validator.validate_region('unconfigured-region')
    
    assert info.region_name == 'unconfigured-region'
    assert len(info.features) == 0
    assert info.metadata['configured'] is False


def test_get_regional_validator_aws():
    """Test factory function for AWS."""
    validator = get_regional_validator('aws')
    assert isinstance(validator, AWSRegionalValidator)
    
    validator = get_regional_validator('AWS')  # Test case insensitive
    assert isinstance(validator, AWSRegionalValidator)


def test_get_regional_validator_azure():
    """Test factory function for Azure."""
    validator = get_regional_validator('azure')
    assert isinstance(validator, AzureRegionalValidator)


def test_get_regional_validator_gcp():
    """Test factory function for GCP."""
    validator = get_regional_validator('gcp')
    assert isinstance(validator, GCPRegionalValidator)


def test_get_regional_validator_custom():
    """Test factory function for custom provider."""
    config = {
        'region-1': {'features': ['feature1']}
    }
    
    validator = get_regional_validator('custom', config)
    assert isinstance(validator, CustomRegionalValidator)
    
    validator = get_regional_validator('bare_metal', config)
    assert isinstance(validator, CustomRegionalValidator)


def test_get_regional_validator_custom_without_config():
    """Test factory function for custom provider without config raises error."""
    with pytest.raises(ValueError, match="region_configs required"):
        get_regional_validator('custom')


def test_get_regional_validator_unsupported():
    """Test factory function with unsupported provider."""
    with pytest.raises(ValueError, match="Unsupported cloud provider"):
        get_regional_validator('unknown-provider')
