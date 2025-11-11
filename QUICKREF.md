# RiskAssessor Quick Reference

## Installation

```bash
pip install -e .
```

## Environment Variables

```bash
export GITHUB_TOKEN="ghp_xxx"
export GITHUB_REPO="owner/repo"
export OPENAI_API_KEY="sk-xxx"
export JIRA_SERVER="https://company.atlassian.net"
export JIRA_USERNAME="user@company.com"
export JIRA_TOKEN="xxx"
export JIRA_PROJECT="PROJ"
```

## CLI Commands

### Initialize Config
```bash
python -m risk_assessor.cli init-config
```

### Sync Issues
```bash
# GitHub
python -m risk_assessor.cli sync --source github --state all

# Jira
python -m risk_assessor.cli sync --source jira --project PROJ

# With filters
python -m risk_assessor.cli sync --source github --labels bug --labels critical
```

### Assess Risk
```bash
# Pull Request
python -m risk_assessor.cli assess-pr --pr 123

# Commits between refs
python -m risk_assessor.cli assess-commits --base main --head develop

# Save to file
python -m risk_assessor.cli assess-pr --pr 123 --output report.json
```

### Catalog Stats
```bash
python -m risk_assessor.cli catalog-stats
```

## Python API

```python
from risk_assessor import RiskEngine
from risk_assessor.utils.config import Config

# Initialize
config = Config.from_env()
engine = RiskEngine(config)

# Sync issues
engine.sync_github_issues(state="all")
engine.sync_jira_issues(project="PROJ")

# Assess
result = engine.assess_pull_request(pr_number=123)
result = engine.assess_commits(base="main", head="develop")

# Access results
print(result['risk_level'])           # "low", "medium", "high", "critical"
print(result['overall_risk_score'])   # 0.0 - 1.0
print(result['complexity_analysis'])  # Complexity metrics
print(result['history_analysis'])     # Related issues
print(result['llm_analysis'])         # AI recommendations
```

## Risk Levels

| Score   | Level    | Action |
|---------|----------|--------|
| 0.0-0.3 | Low      | Standard deployment |
| 0.3-0.6 | Medium   | Extra review, testing |
| 0.6-0.8 | High     | Staged rollout |
| 0.8-1.0 | Critical | Extensive validation |

## Configuration Example

```yaml
# risk_assessor_config.yaml
github:
  token: ${GITHUB_TOKEN}
  repo: owner/repo

jira:
  server: https://company.atlassian.net
  username: ${JIRA_USERNAME}
  token: ${JIRA_TOKEN}
  project: PROJ

llm:
  api_key: ${OPENAI_API_KEY}
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

## Common Patterns

### Pre-Release Check
```bash
python -m risk_assessor.cli assess-commits \
  --base v1.0.0 \
  --head main \
  --output release-risk.json
```

### CI/CD Integration
```bash
# In your CI pipeline
python -m risk_assessor.cli assess-pr --pr $PR_NUMBER
if [ $? -ne 0 ]; then
  echo "Risk assessment failed"
  exit 1
fi
```

### Batch Processing
```python
from risk_assessor import RiskEngine
from risk_assessor.utils.config import Config

config = Config.from_env()
engine = RiskEngine(config)

# Assess multiple PRs
pr_numbers = [123, 124, 125]
for pr in pr_numbers:
    result = engine.assess_pull_request(pr)
    print(f"PR #{pr}: {result['risk_level']}")
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "GitHub client not configured" | Set GITHUB_TOKEN and GITHUB_REPO |
| "LLM analysis failed" | Check OPENAI_API_KEY, or skip LLM |
| "No issues found" | Run sync command first |
| "ModuleNotFoundError" | Run `pip install -r requirements.txt` |

## Links

- [Full Documentation](README.md)
- [User Guide](GUIDE.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
