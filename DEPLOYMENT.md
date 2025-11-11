# RiskAssessor Deployment Guide

This guide provides comprehensive instructions for deploying RiskAssessor in various cloud environments using cloud-agnostic approaches.

## Table of Contents

- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Serverless Deployment](#serverless-deployment)
  - [AWS Lambda](#aws-lambda)
  - [Google Cloud Functions](#google-cloud-functions)
  - [Azure Functions](#azure-functions)
- [Configuration](#configuration)
- [Best Practices](#best-practices)

## Deployment Options

RiskAssessor can be deployed in multiple ways to suit your infrastructure:

| Deployment Type | Best For | Pros | Cons |
|----------------|----------|------|------|
| **Docker** | Local development, simple deployments | Easy to set up, consistent environment | Requires container orchestration for scale |
| **Kubernetes** | Production, multi-cloud, high availability | Scalable, portable, self-healing | More complex setup |
| **AWS Lambda** | AWS-native, event-driven, serverless | No server management, auto-scaling | AWS-specific, cold starts |
| **Google Cloud Functions** | GCP-native, event-driven | Simple deployment, auto-scaling | GCP-specific |
| **Azure Functions** | Azure-native, event-driven | Integrated with Azure services | Azure-specific |

## Docker Deployment

Docker provides the foundation for all cloud deployments and can be used standalone.

### Quick Start

```bash
# Build the image
docker build -t risk-assessor:latest .

# Run with environment variables
docker run --rm \
  -e GITHUB_TOKEN="your-token" \
  -e GITHUB_REPO="owner/repo" \
  -e OPENAI_API_KEY="your-key" \
  risk-assessor:latest \
  risk-assessor assess-pr --pr 123
```

### Using Docker Compose

```bash
# Create .env file with your configuration
cat > .env << EOF
GITHUB_TOKEN=your-github-token
GITHUB_REPO=owner/repo
OPENAI_API_KEY=your-openai-key
LLM_MODEL=gpt-4
EOF

# Start the service
docker-compose up -d

# Run commands
docker-compose run risk-assessor risk-assessor assess-pr --pr 123

# Stop the service
docker-compose down
```

### Building for Multi-Architecture

```bash
# Build for multiple platforms
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-registry/risk-assessor:latest \
  --push .
```

## Kubernetes Deployment

Kubernetes provides cloud-agnostic orchestration for containerized applications.

### Prerequisites

- Kubernetes cluster (any provider: GKE, EKS, AKS, on-prem)
- kubectl configured
- Docker image in accessible registry

### Quick Deploy

```bash
cd deployments/kubernetes

# 1. Update configurations
# Edit secret.yaml with your credentials
# Edit configmap.yaml with your settings
# Edit deployment.yaml with your image

# 2. Deploy
kubectl apply -f namespace.yaml
kubectl apply -f secret.yaml
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 3. Verify
kubectl get pods -n risk-assessor
```

### Common Kubernetes Patterns

#### Pattern 1: One-time Assessment Job

```bash
# Edit job.yaml with your parameters
kubectl apply -f job.yaml
kubectl logs -n risk-assessor job/risk-assessor-job
```

#### Pattern 2: Scheduled Syncing

```bash
# Deploy CronJob for daily syncing
kubectl apply -f cronjob.yaml
```

#### Pattern 3: Auto-scaling

```bash
# Enable horizontal pod autoscaling
kubectl apply -f hpa.yaml
```

### Cloud Provider Examples

#### Google Kubernetes Engine (GKE)

```bash
# Create cluster
gcloud container clusters create risk-assessor \
  --region us-central1 \
  --num-nodes 3

# Get credentials
gcloud container clusters get-credentials risk-assessor --region us-central1

# Deploy
kubectl apply -f deployments/kubernetes/
```

#### Amazon Elastic Kubernetes Service (EKS)

```bash
# Create cluster
eksctl create cluster \
  --name risk-assessor \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --nodes 3

# Deploy
kubectl apply -f deployments/kubernetes/
```

#### Azure Kubernetes Service (AKS)

```bash
# Create cluster
az aks create \
  --resource-group risk-assessor-rg \
  --name risk-assessor-cluster \
  --node-count 3

# Get credentials
az aks get-credentials \
  --resource-group risk-assessor-rg \
  --name risk-assessor-cluster

# Deploy
kubectl apply -f deployments/kubernetes/
```

## Serverless Deployment

Serverless deployments are ideal for event-driven, low-maintenance operations.

### AWS Lambda

See [deployments/serverless/aws-lambda/README.md](serverless/aws-lambda/README.md) for detailed instructions.

**Quick Start:**

```bash
cd deployments/serverless/aws-lambda

# Install Serverless Framework
npm install -g serverless
npm install

# Set environment variables
export GITHUB_TOKEN="your-token"
export GITHUB_REPO="owner/repo"
export OPENAI_API_KEY="your-key"

# Deploy
serverless deploy
```

**Features:**
- HTTP API via API Gateway
- Scheduled syncing via EventBridge
- S3 catalog storage
- CloudWatch logging

### Google Cloud Functions

See [deployments/serverless/google-cloud-functions/README.md](serverless/google-cloud-functions/README.md) for detailed instructions.

**Quick Start:**

```bash
cd deployments/serverless/google-cloud-functions

# Create secrets
echo -n "your-token" | gcloud secrets create github-token --data-file=-
echo -n "your-key" | gcloud secrets create openai-api-key --data-file=-

# Deploy
gcloud functions deploy risk-assessor \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point risk_assessor \
  --set-env-vars GITHUB_REPO=owner/repo \
  --set-secrets GITHUB_TOKEN=github-token:latest,OPENAI_API_KEY=openai-api-key:latest
```

**Features:**
- HTTP triggers
- Cloud Scheduler for cron jobs
- Secret Manager integration
- Cloud Logging

### Azure Functions

See [deployments/serverless/azure-functions/README.md](serverless/azure-functions/README.md) for detailed instructions.

**Quick Start:**

```bash
cd deployments/serverless/azure-functions

# Create Function App
az functionapp create \
  --name risk-assessor-func \
  --resource-group risk-assessor-rg \
  --storage-account riskassessorsa \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4

# Deploy
func azure functionapp publish risk-assessor-func
```

**Features:**
- HTTP triggers
- Timer triggers
- Queue triggers
- Application Insights
- Key Vault integration

## Configuration

### Environment Variables

All deployment methods support these environment variables:

```bash
# Required
GITHUB_TOKEN="your-github-token"
GITHUB_REPO="owner/repository"
OPENAI_API_KEY="your-openai-api-key"

# Optional
JIRA_SERVER="https://company.atlassian.net"
JIRA_USERNAME="user@company.com"
JIRA_TOKEN="jira-api-token"
JIRA_PROJECT="PROJECT_KEY"

LLM_MODEL="gpt-4"
LLM_API_BASE="https://custom-endpoint.com"
RISK_CATALOG_PATH="/path/to/catalog.json"
```

### Configuration Files

You can also use YAML configuration files:

```yaml
# risk_assessor_config.yaml
github:
  token: ${GITHUB_TOKEN}
  repo: owner/repository

jira:
  server: https://company.atlassian.net
  username: ${JIRA_USERNAME}
  token: ${JIRA_TOKEN}
  project: PROJECT_KEY

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

## Best Practices

### Security

1. **Never commit secrets** - Use secret management systems:
   - Kubernetes: Secrets or External Secrets Operator
   - AWS: Secrets Manager or Parameter Store
   - GCP: Secret Manager
   - Azure: Key Vault

2. **Use least privilege** - Grant minimal required permissions:
   - GitHub: Read access to repositories
   - Jira: Read access to projects
   - LLM: API access only

3. **Enable authentication** - Protect endpoints:
   - Kubernetes: Network Policies, Ingress auth
   - AWS: API Gateway authorizers
   - GCP: IAM authentication
   - Azure: Function keys or managed identity

### Reliability

1. **Implement retries** - Handle transient failures
2. **Set appropriate timeouts** - Prevent hanging operations
3. **Monitor health** - Use health checks and readiness probes
4. **Log appropriately** - Balance verbosity with cost

### Performance

1. **Optimize cold starts** (Serverless):
   - Keep dependencies minimal
   - Use provisioned concurrency
   - Pre-warm functions

2. **Cache catalog data** - Reduce redundant API calls

3. **Batch operations** - Sync issues in batches

### Cost Optimization

1. **Right-size resources**:
   - Kubernetes: Adjust resource requests/limits
   - Serverless: Optimize memory allocation

2. **Use spot/preemptible instances** (where appropriate)

3. **Implement data retention policies** - Clean old catalog data

4. **Monitor usage** - Track API calls and compute time

### High Availability

1. **Multiple replicas** (Kubernetes):
   ```yaml
   spec:
     replicas: 3
   ```

2. **Multi-region deployment** (Serverless):
   - Deploy to multiple regions
   - Use global load balancing

3. **Persistent storage**:
   - Kubernetes: Use PersistentVolumes
   - Serverless: Use cloud storage (S3, GCS, Blob)

### Monitoring

1. **Logging**:
   - Centralize logs (CloudWatch, Stackdriver, App Insights)
   - Structure logs as JSON
   - Include correlation IDs

2. **Metrics**:
   - Track assessment duration
   - Monitor API rate limits
   - Alert on errors

3. **Tracing**:
   - Use distributed tracing (optional)
   - Track request flow

## Migration Between Environments

### From Local to Docker

```bash
# Test locally first
risk-assessor assess-pr --pr 123

# Then in Docker
docker run -e GITHUB_TOKEN=$GITHUB_TOKEN \
  -e GITHUB_REPO=$GITHUB_REPO \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  risk-assessor:latest \
  risk-assessor assess-pr --pr 123
```

### From Docker to Kubernetes

```bash
# Push image to registry
docker tag risk-assessor:latest your-registry/risk-assessor:latest
docker push your-registry/risk-assessor:latest

# Update deployment.yaml
# Deploy to Kubernetes
kubectl apply -f deployments/kubernetes/
```

### From Kubernetes to Serverless

```bash
# Extract configuration
kubectl get configmap risk-assessor-config -n risk-assessor -o yaml

# Convert to serverless configuration
# Deploy using serverless-specific tools
```

## Troubleshooting

### Common Issues

1. **Authentication failures**
   - Verify tokens are valid and not expired
   - Check token permissions

2. **API rate limiting**
   - Implement exponential backoff
   - Use conditional requests
   - Cache responses

3. **Timeout errors**
   - Increase timeout settings
   - Optimize queries
   - Reduce batch sizes

4. **Storage issues**
   - Verify volume mounts (Kubernetes)
   - Check storage permissions
   - Monitor disk space

### Debug Commands

```bash
# Kubernetes
kubectl logs -n risk-assessor -l app=risk-assessor --tail=100
kubectl describe pod -n risk-assessor POD_NAME
kubectl exec -n risk-assessor POD_NAME -- env

# Docker
docker logs CONTAINER_ID
docker exec -it CONTAINER_ID sh

# Serverless (AWS)
serverless logs -f assessor -t
aws lambda invoke --function-name risk-assessor output.json

# Serverless (GCP)
gcloud functions logs read risk-assessor --limit 50

# Serverless (Azure)
func azure functionapp logstream risk-assessor-func
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/phrocker/RiskAssessor/issues
- Documentation: See deployment-specific READMEs

## Next Steps

- Configure monitoring and alerting
- Set up CI/CD pipelines
- Implement backup and disaster recovery
- Scale based on usage patterns
