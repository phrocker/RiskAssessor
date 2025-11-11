#!/usr/bin/env python3
"""
Example demonstrating risk contract generation.

This script shows how to generate a risk assessment contract programmatically.
"""

from datetime import datetime
from risk_assessor.core.contracts import (
    RiskContract,
    RiskSummary,
    RiskFactor,
    HistoricalContext,
    ModelDetails
)
import json


def create_example_contract():
    """Create an example risk contract matching the issue specification."""
    
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
            overall_assessment="High risk of outage due to multiple concurrent config and dependency changes."
        ),
        
        factors=[
            RiskFactor(
                category="configuration",
                factor_name="Config Drift",
                impact_weight=0.30,
                observed_value="12 new environment variables introduced",
                assessment="Large config drift compared to baseline in us-east-1"
            ),
            RiskFactor(
                category="code",
                factor_name="Change Volume",
                impact_weight=0.25,
                observed_value="1,200 lines changed across 18 files",
                assessment="Above 95th percentile of normal changes for this repo"
            ),
            RiskFactor(
                category="operational",
                factor_name="Region Stability",
                impact_weight=0.20,
                observed_value="Previous rollback within 24 hours",
                assessment="Recent rollback detected for same region and service"
            ),
            RiskFactor(
                category="testing",
                factor_name="Test Coverage Delta",
                impact_weight=0.10,
                observed_value="-6% coverage drop",
                assessment="Lower test coverage compared to baseline"
            ),
            RiskFactor(
                category="ownership",
                factor_name="Code Churn",
                impact_weight=0.15,
                observed_value="7 different committers in last 10 commits",
                assessment="High churn area; may indicate unclear ownership"
            )
        ],
        
        recommendations=[
            "Perform a canary deployment in us-east-1 before global rollout.",
            "Enable feature flag rollback hooks.",
            "Run extended smoke tests on configuration initialization paths.",
            "Ensure config validation tests include new environment variables."
        ],
        
        historical_context=HistoricalContext(
            previous_similar_changes=14,
            previous_incidents_in_region=3,
            last_incident_cause="Config misalignment in env vars",
            time_since_last_outage_days=7
        ),
        
        model_details=ModelDetails(
            model_version="2.0.0",
            model_type="hybrid_rule_ml",
            trained_on_releases=1542,
            last_updated="2025-11-01"
        ),
        
        text_summary=(
            "Risk Assessor v2 detected a HIGH likelihood (78%) that this deployment could "
            "cause service instability in us-east-1. The primary drivers are significant "
            "configuration drift, large code volume, and recent rollback activity in the "
            "same region. Canary rollout and configuration validation are strongly recommended."
        )
    )
    
    return contract


def main():
    """Generate and display example contract."""
    print("=" * 80)
    print("Risk Assessment Contract Example")
    print("=" * 80)
    print()
    
    # Create example contract
    contract = create_example_contract()
    
    # Convert to dictionary and display as JSON
    contract_dict = contract.to_dict()
    json_output = json.dumps(contract_dict, indent=2)
    
    print(json_output)
    print()
    print("=" * 80)
    print("Contract Details:")
    print("=" * 80)
    print(f"Risk Level: {contract.risk_summary.risk_level}")
    print(f"Risk Score: {contract.risk_summary.risk_score}")
    print(f"Confidence: {contract.risk_summary.confidence}")
    print(f"Number of Factors: {len(contract.factors)}")
    print(f"Number of Recommendations: {len(contract.recommendations)}")
    print()
    
    # Save to file
    with open('examples/example_risk_contract.json', 'w') as f:
        f.write(json_output)
    
    print(f"✓ Example contract saved to examples/example_risk_contract.json")


if __name__ == '__main__':
    main()
