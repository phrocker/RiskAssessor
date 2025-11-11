#!/usr/bin/env python3
"""
Example demonstrating regional validation in RiskAssessor.

This example shows how to configure and use cloud-agnostic regional
validation to assess deployment risks based on feature availability.
"""

from risk_assessor.utils.config import Config, RegionalConfig
from risk_assessor.analyzers.regional_validator import get_regional_validator


def example_aws_regional_validation():
    """Example: AWS regional validation."""
    print("=" * 60)
    print("AWS Regional Validation Example")
    print("=" * 60)
    
    # Configure AWS regions with different feature sets
    config = Config()
    config.regional = RegionalConfig(
        cloud_provider='aws',
        regions={
            'us-east-1': {
                'features': ['ec2', 's3', 'lambda', 'rds', 'dynamodb', 'eks', 'ecs'],
                'region_type': 'standard',
                'availability_zones': 3
            },
            'us-gov-west-1': {
                'features': ['ec2', 's3', 'rds'],  # Limited features in GovCloud
                'region_type': 'govcloud',
                'availability_zones': 2
            }
        }
    )
    
    validator = get_regional_validator(
        config.regional.cloud_provider,
        config.regional.regions
    )
    
    # Validate us-east-1 (standard region)
    print("\nValidating us-east-1 (Standard Region):")
    us_east_1 = validator.validate_region('us-east-1')
    print(f"  Region: {us_east_1.region_name}")
    print(f"  Cloud Provider: {us_east_1.cloud_provider.value}")
    print(f"  Total Features: {len(us_east_1.features)}")
    missing = us_east_1.get_missing_features()
    print(f"  Missing Features: {len(missing)}")
    if missing:
        print(f"    - {', '.join([f.name for f in missing])}")
    
    # Validate us-gov-west-1 (GovCloud with limited features)
    print("\nValidating us-gov-west-1 (GovCloud - Limited Features):")
    us_gov = validator.validate_region('us-gov-west-1')
    print(f"  Region: {us_gov.region_name}")
    print(f"  Cloud Provider: {us_gov.cloud_provider.value}")
    print(f"  Total Features: {len(us_gov.features)}")
    missing = us_gov.get_missing_features()
    print(f"  Missing Features: {len(missing)}")
    if missing:
        print(f"    - {', '.join([f.name for f in missing[:5]])}")
    print(f"  Risk Factor: Deploying to this region has {len(missing)} unavailable services")


def example_azure_regional_validation():
    """Example: Azure regional validation."""
    print("\n" + "=" * 60)
    print("Azure Regional Validation Example")
    print("=" * 60)
    
    config = Config()
    config.regional = RegionalConfig(
        cloud_provider='azure',
        regions={
            'eastus': {
                'features': ['virtual_machines', 'app_service', 'sql_database', 
                           'storage', 'functions', 'aks'],
                'paired_region': 'westus'
            },
            'westeurope': {
                'features': ['virtual_machines', 'storage'],  # Limited features
                'paired_region': 'northeurope'
            }
        }
    )
    
    validator = get_regional_validator(
        config.regional.cloud_provider,
        config.regional.regions
    )
    
    print("\nValidating eastus:")
    eastus = validator.validate_region('eastus')
    missing = eastus.get_missing_features()
    print(f"  Missing Features: {len(missing)}")
    
    print("\nValidating westeurope (Limited Features):")
    westeurope = validator.validate_region('westeurope')
    missing = westeurope.get_missing_features()
    print(f"  Missing Features: {len(missing)}")
    if missing:
        print(f"    - {', '.join([f.name for f in missing[:5]])}")


def example_custom_regional_validation():
    """Example: Custom/bare-metal regional validation."""
    print("\n" + "=" * 60)
    print("Custom/Bare-Metal Regional Validation Example")
    print("=" * 60)
    
    config = Config()
    config.regional = RegionalConfig(
        cloud_provider='custom',
        regions={
            'datacenter-nyc-1': {
                'features': ['kubernetes', 'postgresql', 'redis', 'rabbitmq', 'nginx'],
                'metadata': {
                    'location': 'New York, USA',
                    'capacity': 'high',
                    'network': '10Gbps'
                }
            },
            'datacenter-london-1': {
                'features': [
                    {
                        'name': 'kubernetes',
                        'available': True,
                        'metadata': {'version': '1.28'}
                    },
                    {
                        'name': 'postgresql',
                        'available': True,
                        'metadata': {'version': '15.3'}
                    },
                    {
                        'name': 'mongodb',
                        'available': False,
                        'metadata': {'reason': 'Not yet deployed'}
                    }
                ],
                'metadata': {
                    'location': 'London, UK',
                    'capacity': 'medium'
                }
            }
        }
    )
    
    validator = get_regional_validator(
        config.regional.cloud_provider,
        config.regional.regions
    )
    
    print("\nValidating datacenter-nyc-1:")
    nyc = validator.validate_region('datacenter-nyc-1')
    print(f"  Location: {nyc.metadata['location']}")
    print(f"  Available Features: {', '.join([f.name for f in nyc.features])}")
    
    print("\nValidating datacenter-london-1:")
    london = validator.validate_region('datacenter-london-1')
    print(f"  Location: {london.metadata['location']}")
    available = [f for f in london.features if f.available]
    unavailable = [f for f in london.features if not f.available]
    print(f"  Available: {', '.join([f.name for f in available])}")
    print(f"  Unavailable: {', '.join([f.name for f in unavailable])}")
    if unavailable:
        for f in unavailable:
            print(f"    - {f.name}: {f.metadata.get('reason', 'Unknown')}")


def main():
    """Run all examples."""
    print("\nRegional Validation Examples")
    print("=" * 60)
    print("\nThese examples demonstrate how to use RiskAssessor's")
    print("cloud-agnostic regional validation to assess deployment")
    print("risks based on feature availability in different regions.")
    print()
    
    example_aws_regional_validation()
    example_azure_regional_validation()
    example_custom_regional_validation()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("\nRegional validation helps identify deployment risks by:")
    print("  1. Checking feature availability in target regions")
    print("  2. Identifying missing services that could impact deployments")
    print("  3. Providing region-specific risk factors")
    print("\nFor more examples, see: examples/regional_config_examples.md")
    print()


if __name__ == '__main__':
    main()
