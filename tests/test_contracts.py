"""Tests for risk contract models and generation."""

import pytest
import json
from datetime import datetime
from risk_assessor.core.contracts import (
    RiskContract, RiskSummary, RiskFactor, 
    HistoricalContext, ModelDetails
)


def test_risk_factor_creation():
    """Test creating a risk factor."""
    factor = RiskFactor(
        category="code",
        factor_name="Change Volume",
        impact_weight=0.30,
        observed_value="1,200 lines changed across 18 files",
        assessment="Above 95th percentile of normal changes"
    )
    
    assert factor.category == "code"
    assert factor.factor_name == "Change Volume"
    assert factor.impact_weight == 0.30
    assert "1,200 lines" in factor.observed_value


def test_risk_summary_creation():
    """Test creating a risk summary."""
    summary = RiskSummary(
        risk_score=0.78,
        risk_level="HIGH",
        confidence=0.87,
        overall_assessment="High risk of outage"
    )
    
    assert summary.risk_score == 0.78
    assert summary.risk_level == "HIGH"
    assert summary.confidence == 0.87


def test_historical_context_creation():
    """Test creating historical context."""
    context = HistoricalContext(
        previous_similar_changes=14,
        previous_incidents_in_region=3,
        last_incident_cause="Config misalignment in env vars",
        time_since_last_outage_days=7
    )
    
    assert context.previous_similar_changes == 14
    assert context.previous_incidents_in_region == 3
    assert context.time_since_last_outage_days == 7


def test_model_details_creation():
    """Test creating model details."""
    details = ModelDetails(
        model_version="2.0.0",
        model_type="hybrid_rule_ml",
        trained_on_releases=1542,
        last_updated="2025-11-01"
    )
    
    assert details.model_version == "2.0.0"
    assert details.model_type == "hybrid_rule_ml"


def test_risk_contract_creation():
    """Test creating a complete risk contract."""
    contract = RiskContract(
        id="changeset-abc123",
        timestamp="2025-11-11T14:32:00Z",
        repository="sentrius-core",
        branch="feature/abac-risk-eval",
        deployment_region="us-east-1",
        risk_summary=RiskSummary(
            risk_score=0.78,
            risk_level="HIGH",
            confidence=0.87,
            overall_assessment="High risk of outage"
        ),
        factors=[
            RiskFactor(
                category="code",
                factor_name="Change Volume",
                impact_weight=0.30,
                observed_value="1,200 lines changed",
                assessment="Large change"
            )
        ],
        recommendations=["Perform canary deployment"],
        historical_context=HistoricalContext(
            previous_similar_changes=14,
            previous_incidents_in_region=3,
            last_incident_cause="Config issue",
            time_since_last_outage_days=7
        ),
        model_details=ModelDetails(
            model_version="2.0.0",
            model_type="hybrid_rule_ml",
            trained_on_releases=1542,
            last_updated="2025-11-01"
        ),
        text_summary="High risk deployment detected."
    )
    
    assert contract.id == "changeset-abc123"
    assert contract.repository == "sentrius-core"
    assert contract.risk_summary.risk_level == "HIGH"
    assert len(contract.factors) == 1
    assert len(contract.recommendations) == 1


def test_risk_contract_to_dict():
    """Test converting contract to dictionary."""
    contract = RiskContract(
        id="test-123",
        timestamp="2025-11-11T14:32:00Z",
        repository="test-repo",
        branch="main",
        deployment_region="us-west-2",
        risk_summary=RiskSummary(
            risk_score=0.45,
            risk_level="MEDIUM",
            confidence=0.80,
            overall_assessment="Moderate risk"
        ),
        factors=[],
        recommendations=["Review carefully"],
        historical_context=HistoricalContext(
            previous_similar_changes=5,
            previous_incidents_in_region=1,
            last_incident_cause=None,
            time_since_last_outage_days=None
        ),
        model_details=ModelDetails(
            model_version="2.0.0",
            model_type="hybrid_rule_ml"
        ),
        text_summary="Test summary"
    )
    
    contract_dict = contract.to_dict()
    
    assert isinstance(contract_dict, dict)
    assert contract_dict['id'] == "test-123"
    assert contract_dict['risk_summary']['risk_level'] == "MEDIUM"
    assert contract_dict['risk_summary']['risk_score'] == 0.45
    
    # Verify JSON serialization works
    json_str = json.dumps(contract_dict, indent=2)
    assert "test-123" in json_str


def test_risk_contract_from_dict():
    """Test creating contract from dictionary."""
    data = {
        "id": "test-456",
        "timestamp": "2025-11-11T14:32:00Z",
        "repository": "test-repo",
        "branch": "develop",
        "deployment_region": "eu-west-1",
        "risk_summary": {
            "risk_score": 0.25,
            "risk_level": "LOW",
            "confidence": 0.90,
            "overall_assessment": "Low risk deployment"
        },
        "factors": [
            {
                "category": "code",
                "factor_name": "Test Factor",
                "impact_weight": 0.2,
                "observed_value": "test value",
                "assessment": "test assessment"
            }
        ],
        "recommendations": ["Standard deployment"],
        "historical_context": {
            "previous_similar_changes": 0,
            "previous_incidents_in_region": 0,
            "last_incident_cause": None,
            "time_since_last_outage_days": None
        },
        "model_details": {
            "model_version": "2.0.0",
            "model_type": "hybrid_rule_ml",
            "trained_on_releases": None,
            "last_updated": None
        },
        "text_summary": "Low risk detected"
    }
    
    contract = RiskContract.from_dict(data)
    
    assert contract.id == "test-456"
    assert contract.risk_summary.risk_level == "LOW"
    assert len(contract.factors) == 1
    assert contract.factors[0].category == "code"


def test_risk_level_thresholds():
    """Test that risk levels follow the new threshold definitions."""
    # LOW: < 0.33
    low_summary = RiskSummary(
        risk_score=0.30,
        risk_level="LOW",
        confidence=0.85,
        overall_assessment="Low risk"
    )
    assert low_summary.risk_score < 0.33
    assert low_summary.risk_level == "LOW"
    
    # MEDIUM: 0.33 - 0.66
    medium_summary = RiskSummary(
        risk_score=0.50,
        risk_level="MEDIUM",
        confidence=0.85,
        overall_assessment="Medium risk"
    )
    assert 0.33 <= medium_summary.risk_score < 0.66
    assert medium_summary.risk_level == "MEDIUM"
    
    # HIGH: > 0.66
    high_summary = RiskSummary(
        risk_score=0.75,
        risk_level="HIGH",
        confidence=0.85,
        overall_assessment="High risk"
    )
    assert high_summary.risk_score >= 0.66
    assert high_summary.risk_level == "HIGH"


def test_contract_required_fields():
    """Test that all required contract fields are present."""
    contract = RiskContract(
        id="test",
        timestamp=datetime.now().isoformat(),
        repository="repo",
        branch="main",
        deployment_region="region",
        risk_summary=RiskSummary(
            risk_score=0.5,
            risk_level="MEDIUM",
            confidence=0.8,
            overall_assessment="Test"
        ),
        factors=[],
        recommendations=[],
        historical_context=HistoricalContext(
            previous_similar_changes=0,
            previous_incidents_in_region=0,
            last_incident_cause=None,
            time_since_last_outage_days=None
        ),
        model_details=ModelDetails(
            model_version="2.0.0",
            model_type="hybrid_rule_ml"
        ),
        text_summary="Test"
    )
    
    contract_dict = contract.to_dict()
    
    # Verify all top-level required fields are present
    required_fields = [
        'id', 'timestamp', 'repository', 'branch', 'deployment_region',
        'risk_summary', 'factors', 'recommendations', 
        'historical_context', 'model_details', 'text_summary'
    ]
    
    for field in required_fields:
        assert field in contract_dict, f"Missing required field: {field}"
