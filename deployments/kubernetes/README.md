# RiskAssessor Kubernetes Deployment

This directory contains Kubernetes manifests for deploying RiskAssessor in a cloud-agnostic way.

## Prerequisites

- Kubernetes cluster (any provider: GKE, EKS, AKS, on-prem, etc.)
- kubectl configured to access your cluster
- Docker image built and pushed to a registry accessible by your cluster

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t your-registry/risk-assessor:latest .

# Push to your registry
docker push your-registry/risk-assessor:latest
```

### 2. Update Configuration

Edit the following files with your specific values:

**secret.yaml** - Add your credentials:
```yaml
stringData:
  GITHUB_TOKEN: "your-actual-github-token"
  OPENAI_API_KEY: "your-actual-openai-key"
```

**configmap.yaml** - Update configuration:
```yaml
data:
  GITHUB_REPO: "your-org/your-repo"
```

**deployment.yaml** - Update image reference:
```yaml
image: your-registry/risk-assessor:latest
```

### 3. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Create secrets (edit first!)
kubectl apply -f secret.yaml

# Create configmap
kubectl apply -f configmap.yaml

# Create persistent volume claim
kubectl apply -f pvc.yaml

# Create deployment
kubectl apply -f deployment.yaml

# Create service
kubectl apply -f service.yaml

# Optional: Create cronjob for automated syncing
kubectl apply -f cronjob.yaml

# Optional: Enable autoscaling
kubectl apply -f hpa.yaml
```

### 4. Verify Deployment

```bash
# Check deployment status
kubectl get deployments -n risk-assessor

# Check pods
kubectl get pods -n risk-assessor

# View logs
kubectl logs -n risk-assessor -l app=risk-assessor
```

## Usage Patterns

### Pattern 1: One-time Assessment Job

Run a one-time assessment using the Job resource:

```bash
# Edit job.yaml to set your PR number or commit range
kubectl apply -f job.yaml

# Check job status
kubectl get jobs -n risk-assessor

# View results
kubectl logs -n risk-assessor job/risk-assessor-job
```

### Pattern 2: Scheduled Syncing

The CronJob automatically syncs issues daily at 2 AM. To modify:

```yaml
# In cronjob.yaml
spec:
  schedule: "0 2 * * *"  # Change this cron expression
```

### Pattern 3: Interactive Assessment

Run interactive commands in the pod:

```bash
# Get pod name
POD_NAME=$(kubectl get pods -n risk-assessor -l app=risk-assessor -o jsonpath='{.items[0].metadata.name}')

# Run assessment
kubectl exec -n risk-assessor $POD_NAME -- risk-assessor assess-pr --pr 123

# Sync issues
kubectl exec -n risk-assessor $POD_NAME -- risk-assessor sync --source github --state all

# View catalog stats
kubectl exec -n risk-assessor $POD_NAME -- risk-assessor catalog-stats
```

## Cloud Provider Specific Notes

### Google Kubernetes Engine (GKE)

```bash
# Authenticate to GKE
gcloud container clusters get-credentials CLUSTER_NAME --region REGION

# Use GCR for images
docker tag risk-assessor:latest gcr.io/PROJECT_ID/risk-assessor:latest
docker push gcr.io/PROJECT_ID/risk-assessor:latest
```

### Amazon Elastic Kubernetes Service (EKS)

```bash
# Authenticate to EKS
aws eks update-kubeconfig --name CLUSTER_NAME --region REGION

# Use ECR for images
aws ecr get-login-password --region REGION | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
docker tag risk-assessor:latest ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/risk-assessor:latest
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/risk-assessor:latest
```

### Azure Kubernetes Service (AKS)

```bash
# Authenticate to AKS
az aks get-credentials --resource-group RESOURCE_GROUP --name CLUSTER_NAME

# Use ACR for images
az acr login --name REGISTRY_NAME
docker tag risk-assessor:latest REGISTRY_NAME.azurecr.io/risk-assessor:latest
docker push REGISTRY_NAME.azurecr.io/risk-assessor:latest
```

## Security Best Practices

### 1. Use External Secrets Operator

Instead of storing secrets in Kubernetes, use External Secrets Operator:

```bash
# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

See commented example in `secret.yaml` for configuration.

### 2. Network Policies

Create network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: risk-assessor-netpol
  namespace: risk-assessor
spec:
  podSelector:
    matchLabels:
      app: risk-assessor
  policyTypes:
  - Ingress
  - Egress
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS for API calls
```

### 3. Pod Security Standards

Apply pod security standards:

```bash
kubectl label namespace risk-assessor pod-security.kubernetes.io/enforce=restricted
```

## Monitoring and Observability

### Prometheus Metrics

Add Prometheus annotations to deployment:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
```

### Logging

View aggregated logs:

```bash
# All pods in namespace
kubectl logs -n risk-assessor -l app=risk-assessor --all-containers=true

# Follow logs
kubectl logs -n risk-assessor -l app=risk-assessor -f

# Previous pod logs
kubectl logs -n risk-assessor POD_NAME --previous
```

## Scaling

### Manual Scaling

```bash
kubectl scale deployment risk-assessor -n risk-assessor --replicas=3
```

### Auto Scaling

The HPA is configured to scale based on CPU and memory. Adjust in `hpa.yaml`:

```yaml
spec:
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod -n risk-assessor POD_NAME

# Check events
kubectl get events -n risk-assessor --sort-by='.lastTimestamp'
```

### ConfigMap/Secret Issues

```bash
# Verify ConfigMap
kubectl get configmap risk-assessor-config -n risk-assessor -o yaml

# Verify Secret (base64 encoded)
kubectl get secret risk-assessor-secrets -n risk-assessor -o yaml
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n risk-assessor

# Describe PVC
kubectl describe pvc risk-assessor-data -n risk-assessor
```

## Cleanup

Remove all resources:

```bash
kubectl delete -f .
kubectl delete namespace risk-assessor
```

## Advanced Configuration

### Using Init Containers

Add an init container to pre-populate catalog:

```yaml
initContainers:
- name: init-catalog
  image: risk-assessor:latest
  command:
  - risk-assessor
  - sync
  - --source
  - github
  - --state
  - all
  volumeMounts:
  - name: catalog-data
    mountPath: /app/.risk_assessor
```

### Multi-Environment Setup

Use Kustomize for different environments:

```bash
# Create overlay directories
mkdir -p deployments/kubernetes/overlays/{dev,staging,prod}

# Use kustomize
kubectl apply -k deployments/kubernetes/overlays/prod
```
