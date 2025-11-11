"""Integration tests for regional validation with RiskEngine."""

import pytest
from risk_assessor.core.risk_engine import RiskEngine
from risk_assessor.utils.config import Config, RegionalConfig


def test_risk_engine_with_aws_regional_config():
    """Test RiskEngine with AWS regional configuration."""
    config = Config()
    config.regional = RegionalConfig(
        cloud_provider='aws',
        regions={
            'us-gov-west-1': {
                'features': ['ec2', 's3'],  # Limited features
                'region_type': 'govcloud'
            }
        }
    )
    
    engine = RiskEngine(config)
    
    # Verify regional validator is initialized
    assert engine.regional_validator is not None
    
    # Validate a region
    info = engine.regional_validator.validate_region('us-gov-west-1')
    assert info.region_name == 'us-gov-west-1'
    assert info.is_feature_available('ec2') is True
    assert info.is_feature_available('lambda') is False


def test_risk_engine_with_azure_regional_config():
    """Test RiskEngine with Azure regional configuration."""
    config = Config()
    config.regional = RegionalConfig(
        cloud_provider='azure',
        regions={
            'westeurope': {
                'features': ['virtual_machines', 'storage'],
                'paired_region': 'northeurope'
            }
        }
    )
    
    engine = RiskEngine(config)
    
    assert engine.regional_validator is not None
    info = engine.regional_validator.validate_region('westeurope')
    assert info.is_feature_available('virtual_machines') is True
    assert info.is_feature_available('aks') is False


def test_risk_engine_with_gcp_regional_config():
    """Test RiskEngine with GCP regional configuration."""
    config = Config()
    config.regional = RegionalConfig(
        cloud_provider='gcp',
        regions={
            'us-central1': {
                'features': ['compute_engine', 'cloud_storage'],
                'zones': 3
            }
        }
    )
    
    engine = RiskEngine(config)
    
    assert engine.regional_validator is not None
    info = engine.regional_validator.validate_region('us-central1')
    assert info.is_feature_available('compute_engine') is True
    assert info.is_feature_available('gke') is False


def test_risk_engine_with_custom_regional_config():
    """Test RiskEngine with custom/bare-metal regional configuration."""
    config = Config()
    config.regional = RegionalConfig(
        cloud_provider='custom',
        regions={
            'datacenter-1': {
                'features': ['kubernetes', 'postgresql'],
                'metadata': {'location': 'on-premises'}
            },
            'datacenter-2': {
                'features': [
                    {
                        'name': 'kubernetes',
                        'available': True
                    },
                    {
                        'name': 'mongodb',
                        'available': False
                    }
                ]
            }
        }
    )
    
    engine = RiskEngine(config)
    
    assert engine.regional_validator is not None
    
    # Test datacenter-1
    info1 = engine.regional_validator.validate_region('datacenter-1')
    assert info1.is_feature_available('kubernetes') is True
    assert info1.is_feature_available('postgresql') is True
    
    # Test datacenter-2
    info2 = engine.regional_validator.validate_region('datacenter-2')
    assert info2.is_feature_available('kubernetes') is True
    assert info2.is_feature_available('mongodb') is False


def test_risk_engine_without_regional_config():
    """Test RiskEngine without regional configuration."""
    config = Config()
    engine = RiskEngine(config)
    
    # Regional validator should not be initialized
    assert engine.regional_validator is None


def test_risk_engine_regional_validator_integration():
    """Test that regional validator integrates correctly with risk assessment."""
    config = Config()
    config.regional = RegionalConfig(
        cloud_provider='aws',
        regions={
            'us-west-2': {
                'features': ['ec2', 's3', 'lambda'],
            },
            'us-gov-west-1': {
                'features': ['ec2', 's3'],  # Missing lambda
            }
        }
    )
    
    engine = RiskEngine(config)
    
    # Test that validator can check multiple regions
    validator = engine.regional_validator
    
    # us-west-2 has all features
    us_west_2 = validator.validate_region('us-west-2')
    assert len(us_west_2.get_missing_features()) < len(
        validator.validate_region('us-gov-west-1').get_missing_features()
    )
    
    # us-gov-west-1 is missing lambda and others
    us_gov = validator.validate_region('us-gov-west-1')
    missing = us_gov.get_missing_features()
    assert len(missing) > 0
    feature_names = [f.name for f in missing]
    assert 'lambda' in feature_names
