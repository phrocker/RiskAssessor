# RiskAssessor Google Cloud Functions Deployment

Deploy RiskAssessor as Google Cloud Functions.

## Prerequisites

- Google Cloud Platform account
- `gcloud` CLI installed and authenticated
- Project created in GCP
- Billing enabled

## Setup

### 1. Install Google Cloud SDK

```bash
# Install gcloud
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize
gcloud init

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs

```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 3. Create Secrets

```bash
# GitHub token
echo -n "your-github-token" | gcloud secrets create github-token --data-file=-

# OpenAI API key
echo -n "your-openai-key" | gcloud secrets create openai-api-key --data-file=-

# Jira token (optional)
echo -n "your-jira-token" | gcloud secrets create jira-token --data-file=-
```

## Deployment

### Deploy HTTP Function

```bash
cd deployments/serverless/google-cloud-functions

# Deploy the function
gcloud functions deploy risk-assessor \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point risk_assessor \
  --region us-central1 \
  --memory 512MB \
  --timeout 300s \
  --set-env-vars GITHUB_REPO=owner/repo,LLM_MODEL=gpt-4 \
  --set-secrets GITHUB_TOKEN=github-token:latest,OPENAI_API_KEY=openai-api-key:latest
```

### Deploy Scheduled Function

```bash
# Deploy function for scheduler
gcloud functions deploy risk-assessor-scheduler \
  --runtime python311 \
  --trigger-topic risk-assessor-sync \
  --entry-point risk_assessor_scheduler \
  --region us-central1 \
  --memory 512MB \
  --timeout 300s \
  --set-env-vars GITHUB_REPO=owner/repo,LLM_MODEL=gpt-4 \
  --set-secrets GITHUB_TOKEN=github-token:latest,OPENAI_API_KEY=openai-api-key:latest

# Create Pub/Sub topic
gcloud pubsub topics create risk-assessor-sync

# Create Cloud Scheduler job (daily at 2 AM)
gcloud scheduler jobs create pubsub daily-sync \
  --location us-central1 \
  --schedule "0 2 * * *" \
  --topic risk-assessor-sync \
  --message-body '{"sync": true}'
```

## Usage

### Get Function URL

```bash
gcloud functions describe risk-assessor --region us-central1 --format='value(httpsTrigger.url)'
```

### Invoke via HTTP

```bash
# Set the URL
FUNCTION_URL=$(gcloud functions describe risk-assessor --region us-central1 --format='value(httpsTrigger.url)')

# Assess a PR
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "assess-pr",
    "params": {
      "pr_number": 123
    }
  }'

# Assess commits
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "assess-commits",
    "params": {
      "base": "main",
      "head": "develop"
    }
  }'

# Get catalog stats
curl -X POST $FUNCTION_URL \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "catalog-stats",
    "params": {}
  }'
```

### Local Testing

```bash
# Install Functions Framework
pip install functions-framework

# Run locally
functions-framework --target risk_assessor --debug

# Test
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "catalog-stats",
    "params": {}
  }'
```

## Monitoring

### View Logs

```bash
# Real-time logs
gcloud functions logs read risk-assessor --region us-central1 --limit 50

# Follow logs
gcloud functions logs read risk-assessor --region us-central1 --limit 50 --format=json | jq
```

### Metrics

```bash
# View in Cloud Console
gcloud monitoring dashboards list

# Or use Cloud Console UI
https://console.cloud.google.com/functions/list
```

## Configuration

### Environment Variables

Update environment variables:

```bash
gcloud functions deploy risk-assessor \
  --update-env-vars GITHUB_REPO=new-owner/new-repo,LLM_MODEL=gpt-3.5-turbo \
  --region us-central1
```

### Update Secrets

```bash
# Update secret
echo -n "new-token" | gcloud secrets versions add github-token --data-file=-

# Function will use latest version automatically
```

## Security

### Use Service Account

```bash
# Create service account
gcloud iam service-accounts create risk-assessor

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:risk-assessor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy with service account
gcloud functions deploy risk-assessor \
  --service-account risk-assessor@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Enable Authentication

```bash
# Deploy with authentication required
gcloud functions deploy risk-assessor \
  --no-allow-unauthenticated

# Invoke with auth
curl -H "Authorization: bearer $(gcloud auth print-identity-token)" \
  $FUNCTION_URL \
  -d '{"operation": "catalog-stats"}'
```

## Cost Optimization

### Pricing

- First 2M invocations/month: Free
- After: $0.40 per 1M invocations
- Compute: $0.0000025 per GB-second

### Optimize

```bash
# Use smaller memory
gcloud functions deploy risk-assessor \
  --memory 256MB \
  --timeout 120s
```

## Troubleshooting

### Build Failures

```bash
# View build logs
gcloud builds list --limit 5
gcloud builds log BUILD_ID
```

### Cold Starts

Pre-warm with Cloud Scheduler:

```bash
gcloud scheduler jobs create http warm-function \
  --schedule "*/5 * * * *" \
  --uri $FUNCTION_URL \
  --http-method POST \
  --message-body '{"operation": "catalog-stats"}'
```

## Cleanup

```bash
# Delete function
gcloud functions delete risk-assessor --region us-central1

# Delete scheduler job
gcloud scheduler jobs delete daily-sync --location us-central1

# Delete secrets
gcloud secrets delete github-token
gcloud secrets delete openai-api-key
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Deploy to Cloud Functions
  uses: google-github-actions/deploy-cloud-functions@v1
  with:
    name: risk-assessor
    runtime: python311
    entry_point: risk_assessor
    region: us-central1
    env_vars: GITHUB_REPO=${{ github.repository }}
    secret_environment_variables: |
      GITHUB_TOKEN=github-token
      OPENAI_API_KEY=openai-api-key
```
