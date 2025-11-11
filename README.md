# RiskAssessor

A Python-based tool for assessing deployment risk by analyzing code changes, historical issues, and using LLM-based analysis to evaluate the risk of deployment or production failures.

## Features

- 🔍 **Issue Integration**: Fetch and catalog issues from GitHub and Jira
- 📊 **Complexity Analysis**: Analyze code changes for complexity metrics
- 🤖 **LLM-Powered Risk Assessment**: Use AI to evaluate deployment risks
- 📚 **Historical Analysis**: Learn from past issues to predict future risks
- 📈 **Comprehensive Metrics**: Track additions, deletions, file types, and critical files
- 🎯 **Risk Scoring**: Get actionable risk scores and recommendations
- 💻 **CLI Interface**: Easy-to-use command-line interface
- ☁️ **Cloud-Agnostic Deployment**: Deploy to Kubernetes, AWS Lambda, Google Cloud Functions, or Azure Functions
- 🐳 **Docker Support**: Containerized for consistent environments

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

Assess a pull request:

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

#### `catalog-stats`

View statistics about the issue catalog:

```bash
risk-assessor catalog-stats
```

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

### Risk Scores

The tool provides risk scores from 0.0 to 1.0:

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

## Python API

Use RiskAssessor programmatically:

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

Before deploying a release:

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
