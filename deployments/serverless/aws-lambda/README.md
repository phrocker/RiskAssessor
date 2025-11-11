# RiskAssessor AWS Lambda Deployment

Deploy RiskAssessor as AWS Lambda functions with API Gateway and scheduled execution.

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Node.js and npm installed
- Serverless Framework installed: `npm install -g serverless`
- Docker (for packaging Python dependencies)

## Setup

### 1. Install Serverless Framework Plugins

```bash
cd deployments/serverless/aws-lambda
npm init -y
npm install --save-dev serverless-python-requirements
```

### 2. Configure Environment Variables

Create a `.env` file or export variables:

```bash
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPO="owner/repo"
export OPENAI_API_KEY="your-openai-key"
export LLM_MODEL="gpt-4"

# Optional: Jira
export JIRA_SERVER="https://your-company.atlassian.net"
export JIRA_USERNAME="your-email"
export JIRA_TOKEN="your-jira-token"
export JIRA_PROJECT="PROJECT_KEY"
```

### 3. Package Dependencies

Copy the requirements file:

```bash
cp ../../../requirements.txt .
```

## Deployment

### Deploy to AWS

```bash
# Deploy to dev stage
serverless deploy

# Deploy to production
serverless deploy --stage prod --region us-west-2
```

### Deploy Specific Function

```bash
serverless deploy function -f assessor
```

## Usage

### Via API Gateway

After deployment, you'll get an API endpoint. Use it to trigger assessments:

```bash
# Get the endpoint
serverless info

# Assess a PR
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/assess \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "assess-pr",
    "params": {
      "pr_number": 123
    }
  }'

# Assess commits
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/assess \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "assess-commits",
    "params": {
      "base": "main",
      "head": "feature-branch"
    }
  }'

# Get catalog stats
curl -X POST https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev/assess \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "catalog-stats",
    "params": {}
  }'
```

### Direct Invocation

```bash
# Invoke function directly
serverless invoke -f assessor -d '{
  "operation": "assess-pr",
  "params": {
    "pr_number": 123
  }
}'

# View logs
serverless logs -f assessor -t
```

### Scheduled Sync

The function automatically syncs GitHub issues daily at 2 AM UTC. Check the logs:

```bash
serverless logs -f assessor --startTime 1h
```

## Event Formats

### Assess PR

```json
{
  "operation": "assess-pr",
  "params": {
    "pr_number": 123
  }
}
```

### Assess Commits

```json
{
  "operation": "assess-commits",
  "params": {
    "base": "main",
    "head": "develop"
  }
}
```

### Sync GitHub Issues

```json
{
  "operation": "sync-github",
  "params": {
    "state": "all",
    "labels": ["bug", "critical"]
  }
}
```

### Sync Jira Issues

```json
{
  "operation": "sync-jira",
  "params": {
    "project": "PROJ"
  }
}
```

## Monitoring

### CloudWatch Logs

```bash
# Tail logs
serverless logs -f assessor -t

# View specific time range
serverless logs -f assessor --startTime 1h --filter "ERROR"
```

### Metrics

```bash
# View metrics in CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=risk-assessor-dev-assessor \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Cost Optimization

### Adjust Memory and Timeout

In `serverless.yml`:

```yaml
provider:
  memorySize: 256  # Reduce for cost savings
  timeout: 120     # Reduce if faster execution
```

### Use Reserved Concurrency

Prevent runaway costs:

```yaml
functions:
  assessor:
    reservedConcurrency: 5
```

### Lambda Pricing

- First 1M requests/month: Free
- After: $0.20 per 1M requests
- Compute: $0.0000166667 per GB-second

## Security

### Use AWS Secrets Manager

Store sensitive data in Secrets Manager:

```bash
# Create secret
aws secretsmanager create-secret \
  --name risk-assessor/github-token \
  --secret-string "your-token"

# Update serverless.yml
provider:
  environment:
    GITHUB_TOKEN: ${ssm:/aws/reference/secretsmanager/risk-assessor/github-token}
```

### Enable VPC

For accessing private resources:

```yaml
provider:
  vpc:
    securityGroupIds:
      - sg-xxxxxxxxx
    subnetIds:
      - subnet-xxxxxxxxx
      - subnet-yyyyyyyyy
```

## Troubleshooting

### Cold Start Issues

Pre-warm the function:

```bash
# Use a CloudWatch Events rule
aws events put-rule \
  --name warm-risk-assessor \
  --schedule-expression "rate(5 minutes)"
```

### Package Too Large

Lambda has a 250MB limit. Optimize:

```yaml
custom:
  pythonRequirements:
    slim: true
    strip: true
    noDeploy:
      - boto3
      - botocore
```

### Timeout Errors

Increase timeout:

```yaml
provider:
  timeout: 900  # Max 15 minutes
```

## Cleanup

Remove all resources:

```bash
serverless remove
```

## Alternative: SAM Template

For pure AWS infrastructure, see `template.yaml` for AWS SAM deployment.

## CI/CD Integration

### GitHub Actions

```yaml
- name: Deploy to Lambda
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    cd deployments/serverless/aws-lambda
    npm install
    serverless deploy --stage prod
```
