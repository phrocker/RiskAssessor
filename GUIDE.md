# RiskAssessor User Guide

## Overview

RiskAssessor is a comprehensive tool for assessing deployment risk by analyzing code changes, historical issues, and using AI to evaluate potential problems before they happen.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (optional, for repository analysis)

### Install from Source

```bash
git clone https://github.com/phrocker/RiskAssessor.git
cd RiskAssessor
pip install -e .
```

## Configuration

### Step 1: Create Configuration File

```bash
python -m risk_assessor.cli init-config
```

This creates a `risk_assessor_config.yaml` file.

### Step 2: Set API Keys

You can configure RiskAssessor in two ways:

#### Option 1: Environment Variables (Recommended)

Create a `.env` file or export variables:

```bash
export GITHUB_TOKEN="ghp_your_token"
export GITHUB_REPO="owner/repository"
export OPENAI_API_KEY="sk-your_key"
```

#### Option 2: Configuration File

Edit `risk_assessor_config.yaml`:

```yaml
github:
  token: your-github-token
  repo: owner/repository

llm:
  api_key: your-openai-key
  model: gpt-4
```

## Getting Started

### 1. Sync Historical Issues

First, build up your issue catalog by syncing from GitHub:

```bash
python -m risk_assessor.cli sync --source github --state all
```

Or from Jira:

```bash
python -m risk_assessor.cli sync --source jira --project MYPROJ
```

### 2. Assess a Pull Request

```bash
python -m risk_assessor.cli assess-pr --pr 123
```

This will:
- Analyze the complexity of changes
- Search for related historical issues
- Use AI to evaluate deployment risk
- Provide recommendations

### 3. Assess Commits Between Branches

```bash
python -m risk_assessor.cli assess-commits --base main --head develop
```

This is useful for release planning.

## Understanding Risk Scores

RiskAssessor provides a risk score from 0.0 to 1.0:

| Score Range | Risk Level | Meaning |
|-------------|------------|---------|
| 0.0 - 0.3   | Low        | Safe to deploy with standard procedures |
| 0.3 - 0.6   | Medium     | Review carefully, consider additional testing |
| 0.6 - 0.8   | High       | Requires thorough review and staged rollout |
| 0.8 - 1.0   | Critical   | High probability of issues, extensive validation needed |

## Risk Factors

### Complexity Analysis (Default Weight: 30%)

Evaluates:
- Number of files changed
- Lines added/deleted
- File types (e.g., SQL, shell scripts are higher risk)
- Critical files (config, deployment, security files)
- Commit patterns

### Historical Analysis (Default Weight: 30%)

Evaluates:
- Past issues related to changed files
- Issue severity and frequency
- Patterns in past failures

### LLM Analysis (Default Weight: 40%)

Uses AI to:
- Understand deployment context
- Identify potential failure modes
- Provide actionable recommendations
- Estimate risk based on change patterns

## Advanced Usage

### Custom Configuration

Adjust risk weights in your config file:

```yaml
thresholds:
  complexity_weight: 0.4  # More emphasis on complexity
  history_weight: 0.3
  llm_weight: 0.3         # Less emphasis on AI
```

### Save Assessment to File

```bash
python -m risk_assessor.cli assess-pr --pr 123 --output report.json
```

### Filter Issues by Labels

```bash
python -m risk_assessor.cli sync --source github --labels bug --labels security
```

## Python API

Use RiskAssessor in your Python code:

```python
from risk_assessor import RiskEngine
from risk_assessor.utils.config import Config

# Initialize
config = Config.from_env()
engine = RiskEngine(config)

# Sync issues
engine.sync_github_issues(state="all")

# Assess a PR
result = engine.assess_pull_request(pr_number=123)

print(f"Risk: {result['risk_level']}")
print(f"Score: {result['overall_risk_score']:.2f}")

# Get recommendations
for rec in result['llm_analysis']['recommendations']:
    print(f"- {rec}")
```

## CI/CD Integration

### GitHub Actions

Add to `.github/workflows/risk-assessment.yml`:

```yaml
name: Risk Assessment

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  assess-risk:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install RiskAssessor
        run: pip install risk-assessor
      
      - name: Assess PR Risk
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -m risk_assessor.cli assess-pr \
            --pr ${{ github.event.pull_request.number }} \
            --output risk-report.json
          
          # Comment on PR (requires additional script)
          cat risk-report.json
      
      - name: Check Risk Level
        run: |
          RISK=$(jq -r '.risk_level' risk-report.json)
          echo "Risk Level: $RISK"
          
          if [ "$RISK" = "critical" ]; then
            echo "::warning::Critical risk detected - manual review required"
            exit 1
          fi
```

### GitLab CI

Add to `.gitlab-ci.yml`:

```yaml
risk-assessment:
  stage: test
  script:
    - pip install risk-assessor
    - |
      python -m risk_assessor.cli assess-commits \
        --base $CI_MERGE_REQUEST_TARGET_BRANCH_NAME \
        --head $CI_MERGE_REQUEST_SOURCE_BRANCH_NAME \
        --output risk.json
    - cat risk.json
  only:
    - merge_requests
```

## Troubleshooting

### "GitHub client not configured"

Make sure you've set:
```bash
export GITHUB_TOKEN="your_token"
export GITHUB_REPO="owner/repo"
```

### "LLM analysis failed"

Check:
- Your OpenAI API key is valid
- You have credits/quota available
- Network connectivity

LLM is optional - you'll still get complexity and history analysis.

### "No issues found"

Run sync first:
```bash
python -m risk_assessor.cli sync --source github
```

## Best Practices

1. **Regular Syncing**: Sync issues weekly to keep the catalog up-to-date
2. **Pre-Release Checks**: Always assess before major releases
3. **Team Review**: Share risk reports with your team for high-risk changes
4. **Iterative Development**: Check risk early and often during development
5. **Custom Weights**: Tune weights based on your team's experience

## Support

- Documentation: [README.md](README.md)
- Issues: [GitHub Issues](https://github.com/phrocker/RiskAssessor/issues)
- Examples: See `examples/` directory

## License

MIT License - See LICENSE file for details.
