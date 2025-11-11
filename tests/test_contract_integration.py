"""Integration test for risk contract generation."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from risk_assessor.core.risk_engine import RiskEngine
from risk_assessor.core.contracts import RiskContract
from risk_assessor.utils.config import Config


def test_contract_generation_with_mock_data():
    """Test that contract generation works with mocked data."""
    # Create a minimal config
    config = Config()
    config.github.token = None  # Don't initialize GitHub client
    config.github.repo = "test/repo"
    
    # Initialize engine without GitHub client
    engine = RiskEngine(config)
    
    # Now manually set the repo for contract generation
    engine.config.github.repo = "test/repo"
    
    # Create contract directly using the internal method
    contract = engine._generate_risk_contract(
        changeset_id="test-123",
        files_changed=['src/main.py', 'config/settings.yaml', 'tests/test_main.py'],
        additions=100,
        deletions=50,
        commits=3,
        title="Test PR",
        description="Test description",
        repository="test/repo",
        branch="main",
        deployment_region="us-east-1"
    )
    
    # Validate contract structure
    assert isinstance(contract, RiskContract)
    assert contract.repository == "test/repo"
    assert contract.branch == "main"
    assert contract.deployment_region == "us-east-1"
    
    # Validate risk summary
    assert contract.risk_summary.risk_level in ["LOW", "MEDIUM", "HIGH"]
    assert 0.0 <= contract.risk_summary.risk_score <= 1.0
    assert 0.0 <= contract.risk_summary.confidence <= 1.0
    assert len(contract.risk_summary.overall_assessment) > 0
    
    # Validate factors
    assert isinstance(contract.factors, list)
    assert len(contract.factors) > 0
    for factor in contract.factors:
        assert factor.category in ["code", "configuration", "operational", "testing", "ownership"]
        assert 0.0 <= factor.impact_weight <= 1.0
        assert len(factor.observed_value) > 0
        assert len(factor.assessment) > 0
    
    # Validate recommendations
    assert isinstance(contract.recommendations, list)
    assert len(contract.recommendations) > 0
    
    # Validate historical context
    assert contract.historical_context.previous_similar_changes >= 0
    assert contract.historical_context.previous_incidents_in_region >= 0
    
    # Validate model details
    assert contract.model_details.model_version == "2.0.0"
    assert contract.model_details.model_type == "hybrid_rule_ml"
    
    # Validate text summary
    assert len(contract.text_summary) > 0
    
    # Validate JSON serialization
    contract_dict = contract.to_dict()
    assert isinstance(contract_dict, dict)
    assert "id" in contract_dict
    assert "timestamp" in contract_dict
    assert "risk_summary" in contract_dict
    assert "factors" in contract_dict


def test_commits_contract_generation():
    """Test contract generation for commits."""
    config = Config()
    config.github.token = None  # Don't initialize GitHub client
    config.github.repo = "test/repo"
    
    engine = RiskEngine(config)
    
    # Generate contract directly
    contract = engine._generate_risk_contract(
        changeset_id="test-456",
        files_changed=['src/main.py', 'README.md', 'config/settings.yaml'],
        additions=60,
        deletions=25,
        commits=2,
        title="Changes from main to develop",
        description="Analyzing 2 commits",
        repository="test/repo",
        branch="develop",
        deployment_region="eu-west-1"
    )
    
    # Validate contract
    assert isinstance(contract, RiskContract)
    assert contract.repository == "test/repo"
    assert contract.branch == "develop"
    assert contract.deployment_region == "eu-west-1"
    assert contract.risk_summary.risk_level in ["LOW", "MEDIUM", "HIGH"]
    
    # Validate that contract is properly serializable
    contract_dict = contract.to_dict()
    reconstructed = RiskContract.from_dict(contract_dict)
    assert reconstructed.id == contract.id
    assert reconstructed.risk_summary.risk_level == contract.risk_summary.risk_level


def test_risk_level_thresholds():
    """Test that risk levels are correctly assigned based on thresholds."""
    config = Config()
    config.github.token = None
    config.github.repo = "test/repo"
    
    engine = RiskEngine(config)
    
    # Test with minimal changes (should be LOW risk)
    contract = engine._generate_risk_contract(
        changeset_id="test-low",
        files_changed=['README.md'],  # Low risk file
        additions=10,
        deletions=5,
        commits=1,
        title="Test",
        description="Test",
        repository="test/repo",
        branch="main",
        deployment_region="test"
    )
    
    # With minimal changes, should be LOW or MEDIUM risk
    assert contract.risk_summary.risk_level in ["LOW", "MEDIUM"]
    
    # Verify threshold alignment
    if contract.risk_summary.risk_score < 0.33:
        assert contract.risk_summary.risk_level == "LOW"
    elif contract.risk_summary.risk_score < 0.66:
        assert contract.risk_summary.risk_level == "MEDIUM"
    else:
        assert contract.risk_summary.risk_level == "HIGH"


def test_high_risk_contract():
    """Test contract generation for high-risk changes."""
    config = Config()
    config.github.token = None
    config.github.repo = "test/repo"
    
    engine = RiskEngine(config)
    
    # Create a high-risk scenario with many critical files
    critical_files = [
        'config/production.yaml',
        'deploy/kubernetes.yaml',
        'database/migration_001.sql',
        'security/auth.py',
        'config/env.production',
    ]
    
    contract = engine._generate_risk_contract(
        changeset_id="test-high",
        files_changed=critical_files + ['src/main.py'] * 20,  # Many files
        additions=1500,  # Large change
        deletions=800,
        commits=25,  # Many commits
        title="Major refactor",
        description="Large scale changes",
        repository="test/repo",
        branch="main",
        deployment_region="production"
    )
    
    # This should be MEDIUM or HIGH risk
    assert contract.risk_summary.risk_level in ["MEDIUM", "HIGH"]
    assert contract.risk_summary.risk_score >= 0.33
    
    # Should have configuration factor
    config_factors = [f for f in contract.factors if f.category == "configuration"]
    assert len(config_factors) > 0
    
    # Should have recommendations
    assert len(contract.recommendations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
