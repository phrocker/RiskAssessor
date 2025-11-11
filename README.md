# RiskAssessor

A Python-based tool for assessing deployment risk by analyzing code changes, historical issues, and using LLM-based analysis to evaluate the risk of deployment or production failures.

## Features

- 🔍 **Issue Integration**: Fetch and catalog issues from GitHub and Jira
- 📊 **Complexity Analysis**: Analyze code changes for complexity metrics
- 🤖 **LLM-Powered Risk Assessment**: Use AI to evaluate deployment risks
- 📚 **Historical Analysis**: Learn from past issues to predict future risks
- 📈 **Comprehensive Metrics**: Track additions, deletions, file types, and critical files
- 🎯 **Risk Scoring**: Get actionable risk scores and recommendations
- 📋 **Risk Contracts**: Structured JSON contracts for standardized risk reporting (v2.0)
- 🌍 **Regional Validation**: Cloud-agnostic regional feature availability checking (v2.0)
- 💻 **CLI Interface**: Easy-to-use command-line interface
- ☁️ **Cloud-Agnostic Deployment**: Deploy to Kubernetes, AWS Lambda, Google Cloud Functions, or Azure Functions
- 🐳 **Docker Support**: Containerized for consistent environments

## What's New in v2.0

### Risk Contracts

RiskAssessor now supports **Risk Contracts** - a structured JSON format that provides comprehensive risk analysis with:

- **Standardized Output**: Consistent format for all risk assessments
- **Factor Breakdown**: Detailed categorization of risk factors (code, configuration, operational, testing, ownership)
- **Actionable Recommendations**: Clear next steps based on analysis
- **Historical Context**: Information about past incidents and similar changes
- **CI/CD Integration**: Easy to parse and integrate into automated pipelines

See the [examples/README.md](examples/README.md) for detailed documentation and usage examples.

### Regional Validation (NEW in v2.0)

RiskAssessor now includes **cloud-agnostic regional validation** to identify deployment risks based on regional feature availability:

- **Cloud-Agnostic**: Supports AWS, Azure, GCP, and custom/bare-metal infrastructure
- **Feature Availability**: Automatically checks if required services are available in target regions
- **Risk Scoring**: Factors missing regional features into overall risk assessment
- **Flexible Configuration**: Define your own regions and features for any infrastructure

Example configuration:

```yaml
regional:
  cloud_provider: aws
  regions:
    us-gov-west-1:
      features: [ec2, s3, rds]  # Limited features in GovCloud
      region_type: govcloud
```

See [examples/regional_config_examples.md](examples/regional_config_examples.md) for detailed examples.

#### New Risk Level Thresholds

- **LOW**: Risk score < 0.33 (safe for standard deployment)
- **MEDIUM**: Risk score 0.33 - 0.66 (requires careful review)  
- **HIGH**: Risk score > 0.66 (needs staged rollout)

## Installation

### From Source

```bash
git clone https://github.com/phrocker/RiskAssessor.git
cd RiskAssessor
pip install -e .
```

### Using pip (once published)

```bash
pip install risk-assessor
```

### Using Docker

```bash
# Pull the image (once published)
docker pull ghcr.io/phrocker/risk-assessor:latest

# Or build locally
docker build -t risk-assessor:latest .

# Run
docker run --rm \
  -e GITHUB_TOKEN="your-token" \
  -e GITHUB_REPO="owner/repo" \
  -e OPENAI_API_KEY="your-key" \
  risk-assessor:latest \
  risk-assessor assess-pr --pr 123
```

## Quick Start

### 1. Initialize Configuration

Create a configuration file with your API keys and settings:

```bash
risk-assessor init-config
```

This creates a `risk_assessor_config.yaml` file. Edit it with your credentials:

```yaml
github:
  token: ${GITHUB_TOKEN}
  repo: owner/repository

jira:
  server: https://your-company.atlassian.net
  username: ${JIRA_USERNAME}
  token: ${JIRA_TOKEN}
  project: PROJECT_KEY

llm:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4
  temperature: 0.7
```

You can use environment variables or set values directly in the config file.

### 2. Sync Historical Issues

Sync issues from GitHub:

```bash
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPO="owner/repo"

risk-assessor sync --source github --state all
```

Sync issues from Jira:

```bash
export JIRA_SERVER="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email@company.com"
export JIRA_TOKEN="your-jira-token"

risk-assessor sync --source jira --project PROJECT_KEY
```

### 3. Assess Risk

#### Using Risk Contracts (Recommended - v2.0)

Assess a pull request with structured contract output:

```bash
risk-assessor assess-pr-contract --pr 123 --deployment-region us-east-1 --output risk.json
```

Assess commits between branches with contract output:

```bash
risk-assessor assess-commits-contract --base main --head feature-branch --deployment-region us-east-1 --output risk.json
```

#### Legacy Format

Assess a pull request (legacy format):

```bash
risk-assessor assess-pr --pr 123
```

Assess commits between two branches:

```bash
risk-assessor assess-commits --base main --head feature-branch
```

View catalog statistics:

```bash
risk-assessor catalog-stats
```

## Usage

### Environment Variables

The tool can be configured using environment variables:

- `GITHUB_TOKEN`: GitHub personal access token
- `GITHUB_REPO`: Repository in format `owner/repo`
- `JIRA_SERVER`: Jira server URL
- `JIRA_USERNAME`: Jira username/email
- `JIRA_TOKEN`: Jira API token
- `JIRA_PROJECT`: Jira project key
- `OPENAI_API_KEY` or `LLM_API_KEY`: OpenAI or compatible LLM API key
- `LLM_MODEL`: Model to use (default: `gpt-4`)
- `LLM_API_BASE`: Custom API endpoint (optional)
- `RISK_CATALOG_PATH`: Path to catalog file (default: `.risk_assessor/catalog.json`)

### CLI Commands

#### `sync`

Sync issues from GitHub or Jira to the local catalog:

```bash
# Sync GitHub issues
risk-assessor sync --source github --state all

# Sync with label filter
risk-assessor sync --source github --labels bug --labels critical

# Sync Jira issues
risk-assessor sync --source jira --project PROJ
```

#### `assess-pr`

Assess risk for a GitHub pull request:

```bash
# Basic assessment
risk-assessor assess-pr --pr 123

# Save to JSON file
risk-assessor assess-pr --pr 123 --output risk-report.json

# Use custom config
risk-assessor assess-pr --pr 123 --config my-config.yaml
```

#### `assess-commits`

Assess risk for commits between two references:

```bash
# Assess between branches
risk-assessor assess-commits --base main --head develop

# Assess between tags
risk-assessor assess-commits --base v1.0.0 --head v2.0.0

# Save to JSON
risk-assessor assess-commits --base main --head develop --output assessment.json
```

#### `assess-pr-contract` (NEW in v2.0)

Assess a pull request with contract format:

```bash
# Basic assessment with contract
risk-assessor assess-pr-contract --pr 123 --deployment-region us-east-1

# Save contract to JSON file
risk-assessor assess-pr-contract --pr 123 --deployment-region us-east-1 --output risk.json
```

#### `assess-commits-contract` (NEW in v2.0)

Assess commits with contract format:

```bash
# Assess between branches
risk-assessor assess-commits-contract --base main --head develop --deployment-region us-west-2

# Save to JSON
risk-assessor assess-commits-contract --base main --head develop --deployment-region us-west-2 --output risk.json
```

#### `assess-pr` (Legacy)

Assess a pull request with legacy format:

```bash
# Basic assessment
risk-assessor assess-pr --pr 123

# Save to JSON file
risk-assessor assess-pr --pr 123 --output risk-report.json

# Use custom config
risk-assessor assess-pr --pr 123 --config my-config.yaml
```

#### `assess-commits` (Legacy)

Assess risk for commits between two references:

```bash
# Assess between branches
risk-assessor assess-commits --base main --head develop

# Assess between tags
risk-assessor assess-commits --base v1.0.0 --head v2.0.0

# Save to JSON
risk-assessor assess-commits --base main --head develop --output assessment.json
```

#### `catalog-stats`

View statistics about the issue catalog:

```bash
risk-assessor catalog-stats
```

## Risk Contract Format (v2.0)

### Contract Structure

Risk contracts provide a standardized format for risk assessments:

```json
{
  "id": "changeset-abc123",
  "timestamp": "2025-11-11T14:32:00Z",
  "repository": "sentrius-core",
  "branch": "feature/abac-risk-eval",
  "deployment_region": "us-east-1",
  "risk_summary": {
    "risk_score": 0.78,
    "risk_level": "HIGH",
    "confidence": 0.87,
    "overall_assessment": "High risk of outage..."
  },
  "factors": [...],
  "recommendations": [...],
  "historical_context": {...},
  "model_details": {...},
  "text_summary": "Risk Assessor v2 detected..."
}
```

See [examples/example_risk_contract.json](examples/example_risk_contract.json) for a complete example.

### Risk Factor Categories

- **configuration**: Config files, environment variables, deployment settings
- **code**: Change volume, complexity, file types
- **operational**: Region stability, deployment history
- **testing**: Test coverage, quality metrics
- **ownership**: Code churn, contributor patterns

## How It Works

RiskAssessor uses a multi-factor approach to assess deployment risk:

### 1. Complexity Analysis (30% default weight)

- Analyzes the number of files changed
- Calculates total lines added/deleted
- Identifies critical files (config, deployment, security, etc.)
- Evaluates file types and their risk profiles
- Considers commit fragmentation

### 2. Historical Analysis (30% default weight)

- Searches for related issues in the catalog
- Considers issue severity and status
- Identifies patterns in file changes
- Learns from past failures

### 3. LLM Analysis (40% default weight)

- Uses AI to evaluate deployment risk
- Considers deployment context
- Provides actionable recommendations
- Identifies key concerns
- Offers confidence ratings

### Risk Scores and Levels (v2.0)

The tool provides risk scores from 0.0 to 1.0 with updated thresholds:

- **LOW** (< 0.33): Safe to deploy with standard procedures
- **MEDIUM** (0.33 - 0.66): Review carefully, consider additional testing
- **HIGH** (> 0.66): Requires thorough review and staged rollout

### Legacy Risk Levels

The legacy format uses these thresholds:

- **Low Risk** (< 0.3): Safe to deploy with standard procedures
- **Medium Risk** (0.3 - 0.6): Review carefully, consider additional testing
- **High Risk** (0.6 - 0.8): Requires thorough review and staged rollout
- **Critical Risk** (> 0.8): High probability of issues, requires extensive validation

## Configuration

### Configuration File

Create a `risk_assessor_config.yaml`:

```yaml
github:
  token: your-token
  repo: owner/repository

jira:
  server: https://company.atlassian.net
  username: user@company.com
  token: jira-token
  project: PROJ

llm:
  api_key: your-openai-key
  model: gpt-4
  temperature: 0.7

thresholds:
  low: 0.3
  medium: 0.6
  high: 0.8
  complexity_weight: 0.3
  history_weight: 0.3
  llm_weight: 0.4

regional:
  cloud_provider: aws  # aws, azure, gcp, custom, or bare_metal
  regions:
    us-east-1:
      features: [ec2, s3, lambda, rds, dynamodb]
      region_type: standard
      availability_zones: 3

catalog_path: .risk_assessor/catalog.json
```

### Customizing Weights

Adjust the risk factor weights in your configuration:

```yaml
thresholds:
  complexity_weight: 0.4  # Increase complexity importance
  history_weight: 0.4     # Increase history importance
  llm_weight: 0.2         # Decrease LLM importance
```

### Regional Configuration

Configure cloud-agnostic regional validation to assess deployment risks based on feature availability:

**AWS Example:**
```yaml
regional:
  cloud_provider: aws
  regions:
    us-east-1:
      features: [ec2, s3, lambda, rds, dynamodb, eks, ecs]
      region_type: standard
      availability_zones: 3
    us-gov-west-1:
      features: [ec2, s3, rds]  # Limited features in GovCloud
      region_type: govcloud
```

**Azure Example:**
```yaml
regional:
  cloud_provider: azure
  regions:
    eastus:
      features: [virtual_machines, app_service, sql_database, storage, functions, aks]
      paired_region: westus
```

**Custom/Bare-Metal Example:**
```yaml
regional:
  cloud_provider: custom
  regions:
    datacenter-1:
      features: [kubernetes, postgresql, redis, rabbitmq]
      metadata:
        location: on-premises
        capacity: high
```

For detailed regional configuration examples, see [examples/regional_config_examples.md](examples/regional_config_examples.md).

## Python API

### Using Risk Contracts (v2.0)

```python
from risk_assessor import RiskEngine
from risk_assessor.utils.config import Config
import json

# Load configuration
config = Config.from_env()

# Initialize engine
engine = RiskEngine(config)

# Sync issues (optional)
engine.sync_github_issues(state="all")

# Assess a PR with contract format
contract = engine.assess_pull_request_contract(
    pr_number=123,
    deployment_region="us-east-1",
    branch="main"
)

# Access contract data
print(f"Risk Level: {contract.risk_summary.risk_level}")
print(f"Risk Score: {contract.risk_summary.risk_score:.2f}")
print(f"Confidence: {contract.risk_summary.confidence:.2f}")

# Access factors
for factor in contract.factors:
    print(f"  {factor.factor_name}: {factor.observed_value}")

# Access recommendations
for rec in contract.recommendations:
    print(f"  - {rec}")

# Export to JSON
with open('risk_contract.json', 'w') as f:
    json.dump(contract.to_dict(), f, indent=2)

# Load from JSON
from risk_assessor.core.contracts import RiskContract
with open('risk_contract.json') as f:
    loaded_contract = RiskContract.from_dict(json.load(f))
```

### Legacy Format

Use RiskAssessor with the legacy format:

```python
from risk_assessor import RiskEngine
from risk_assessor.utils.config import Config

# Load configuration
config = Config.from_env()

# Initialize engine
engine = RiskEngine(config)

# Sync issues
engine.sync_github_issues(state="all")

# Assess a PR
assessment = engine.assess_pull_request(pr_number=123)

print(f"Risk Level: {assessment['risk_level']}")
print(f"Risk Score: {assessment['overall_risk_score']:.2f}")

# Get recommendations from LLM
if assessment.get('llm_analysis'):
    for rec in assessment['llm_analysis']['recommendations']:
        print(f"  - {rec}")
```

## Examples

### CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Assess Deployment Risk
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    pip install risk-assessor
    risk-assessor assess-commits --base main --head ${{ github.sha }} --output risk.json
    
    # Parse risk level and fail if critical
    RISK_LEVEL=$(jq -r '.risk_level' risk.json)
    if [ "$RISK_LEVEL" = "critical" ]; then
      echo "Critical risk detected - manual approval required"
      exit 1
    fi
```

### Pre-deployment Check

Before deploying a release with contract format:

```bash
# Assess changes in the release with contract
risk-assessor assess-commits-contract \
  --base v1.0.0 \
  --head v1.1.0 \
  --deployment-region production \
  --output release-risk.json

# Review the contract
cat release-risk.json | jq '.risk_summary'
cat release-risk.json | jq '.recommendations'

# Check risk level and fail if HIGH
RISK_LEVEL=$(jq -r '.risk_summary.risk_level' release-risk.json)
if [ "$RISK_LEVEL" = "HIGH" ]; then
  echo "High risk deployment detected - manual review required"
  exit 1
fi
```

Legacy format:

```bash
# Assess changes in the release
risk-assessor assess-commits --base v1.0.0 --head v1.1.0 --output release-risk.json

# Review the report
cat release-risk.json | jq '.llm_analysis.recommendations'
```

## Deployment

RiskAssessor supports multiple deployment options for cloud-agnostic infrastructure:

### Docker

```bash
# Using Docker Compose
docker-compose up -d
docker-compose run risk-assessor risk-assessor assess-pr --pr 123
```

### Kubernetes

```bash
# Deploy to any Kubernetes cluster (GKE, EKS, AKS, on-prem)
kubectl apply -f deployments/kubernetes/
```

### Serverless

**AWS Lambda:**
```bash
cd deployments/serverless/aws-lambda
serverless deploy
```

**Google Cloud Functions:**
```bash
cd deployments/serverless/google-cloud-functions
gcloud functions deploy risk-assessor --runtime python311 --trigger-http
```

**Azure Functions:**
```bash
cd deployments/serverless/azure-functions
func azure functionapp publish risk-assessor-func
```

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
# Format code
black risk_assessor/

# Type checking
mypy risk_assessor/

# Linting
flake8 risk_assessor/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/phrocker/RiskAssessor/issues) page.
