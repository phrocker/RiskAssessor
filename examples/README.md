# Risk Assessment Contract Examples

This directory contains examples demonstrating the Risk Assessment Contract format introduced in v2.0.

## Overview

The Risk Assessment Contract is a structured JSON format that provides comprehensive risk analysis for deployments. It includes:

- **Risk Summary**: Overall risk score, level, and confidence
- **Risk Factors**: Detailed breakdown of contributing factors by category
- **Recommendations**: Actionable steps to mitigate risks
- **Historical Context**: Information about past similar changes and incidents
- **Model Details**: Information about the risk assessment model used
- **Text Summary**: Natural language summary for human consumption

## Risk Level Thresholds

The contract uses the following risk level thresholds:

- **LOW**: Risk score < 0.33 (safe for standard deployment)
- **MEDIUM**: Risk score 0.33 - 0.66 (requires careful review)
- **HIGH**: Risk score > 0.66 (needs staged rollout and extensive validation)

## Factor Categories

Risk factors are categorized into:

1. **configuration**: Changes to configuration files, environment variables, deployment settings
2. **code**: Code complexity, change volume, file modifications
3. **operational**: Region stability, deployment history, rollback frequency
4. **testing**: Test coverage, test quality, test execution results
5. **ownership**: Code churn, contributor distribution, ownership clarity

## Using the Contract Format

### Command Line

Use the new contract-specific commands:

```bash
# Assess a pull request with contract format
risk-assessor assess-pr-contract --pr 123 --deployment-region us-east-1 --output risk.json

# Assess commits with contract format
risk-assessor assess-commits-contract --base main --head feature-branch --deployment-region eu-west-1 --output risk.json
```

### Python API

```python
from risk_assessor import RiskEngine
from risk_assessor.utils.config import Config

# Initialize
config = Config.from_env()
engine = RiskEngine(config)

# Generate contract for a PR
contract = engine.assess_pull_request_contract(
    pr_number=123,
    deployment_region="us-east-1",
    branch="main"
)

# Access contract data
print(f"Risk Level: {contract.risk_summary.risk_level}")
print(f"Risk Score: {contract.risk_summary.risk_score}")

# Export to JSON
import json
with open('risk_contract.json', 'w') as f:
    json.dump(contract.to_dict(), f, indent=2)

# Load from JSON
from risk_assessor.core.contracts import RiskContract
with open('risk_contract.json', 'r') as f:
    data = json.load(f)
    loaded_contract = RiskContract.from_dict(data)
```

## Example Contract

See `example_risk_contract.json` for a complete example contract that matches the specification.

You can generate this example by running:

```bash
python examples/example_contract.py
```

## Integration with CI/CD

The contract format is designed to be easily consumed by CI/CD pipelines:

### GitHub Actions Example

```yaml
- name: Assess Deployment Risk
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    pip install risk-assessor
    risk-assessor assess-pr-contract \
      --pr ${{ github.event.pull_request.number }} \
      --deployment-region us-east-1 \
      --output risk_contract.json
    
    # Check risk level
    RISK_LEVEL=$(jq -r '.risk_summary.risk_level' risk_contract.json)
    if [ "$RISK_LEVEL" = "HIGH" ]; then
      echo "::warning::High risk deployment detected"
      # Add PR comment with recommendations
      jq -r '.recommendations[]' risk_contract.json | while read rec; do
        echo "  - $rec"
      done
    fi
```

### Using Recommendations as PR Comments

```python
import json
from github import Github

# Load contract
with open('risk_contract.json') as f:
    contract = json.load(f)

# Create PR comment with recommendations
if contract['risk_summary']['risk_level'] in ['MEDIUM', 'HIGH']:
    comment = f"""## ⚠️ Risk Assessment: {contract['risk_summary']['risk_level']}
    
**Risk Score:** {contract['risk_summary']['risk_score']} (Confidence: {contract['risk_summary']['confidence']})

**Assessment:** {contract['risk_summary']['overall_assessment']}

### Recommendations:
"""
    for i, rec in enumerate(contract['recommendations'], 1):
        comment += f"\n{i}. {rec}"
    
    # Post to PR
    gh = Github(os.environ['GITHUB_TOKEN'])
    repo = gh.get_repo(os.environ['GITHUB_REPOSITORY'])
    pr = repo.get_pull(int(os.environ['PR_NUMBER']))
    pr.create_issue_comment(comment)
```

## Contract Schema

All contracts follow this schema:

```json
{
  "id": "string (unique identifier)",
  "timestamp": "ISO 8601 timestamp",
  "repository": "string (repo name)",
  "branch": "string (target branch)",
  "deployment_region": "string (deployment region)",
  "risk_summary": {
    "risk_score": "float (0.0-1.0)",
    "risk_level": "string (LOW|MEDIUM|HIGH)",
    "confidence": "float (0.0-1.0)",
    "overall_assessment": "string (summary)"
  },
  "factors": [
    {
      "category": "string (configuration|code|operational|testing|ownership)",
      "factor_name": "string",
      "impact_weight": "float (0.0-1.0)",
      "observed_value": "string",
      "assessment": "string"
    }
  ],
  "recommendations": ["string"],
  "historical_context": {
    "previous_similar_changes": "integer",
    "previous_incidents_in_region": "integer",
    "last_incident_cause": "string|null",
    "time_since_last_outage_days": "integer|null"
  },
  "model_details": {
    "model_version": "string",
    "model_type": "string",
    "trained_on_releases": "integer|null",
    "last_updated": "string|null"
  },
  "text_summary": "string (natural language summary)"
}
```

## Backward Compatibility

The original `assess-pr` and `assess-commits` commands continue to work with the legacy format. The new contract format is available through:

- `assess-pr-contract`
- `assess-commits-contract`

Both formats can coexist, allowing gradual migration to the new contract-based approach.
