#!/bin/bash
# Deploy RiskAssessor to Kubernetes
# Usage: ./scripts/deploy-k8s.sh [namespace] [image-name]

set -e

NAMESPACE=${1:-risk-assessor}
IMAGE=${2:-risk-assessor:latest}
K8S_DIR="deployments/kubernetes"

echo "========================================="
echo "RiskAssessor Kubernetes Deployment"
echo "========================================="
echo "Namespace: $NAMESPACE"
echo "Image: $IMAGE"
echo ""

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Check if connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "Error: Not connected to a Kubernetes cluster"
    echo "Please configure kubectl to connect to your cluster"
    exit 1
fi

# Confirm deployment
read -p "Deploy to current kubectl context? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "Step 1: Creating namespace..."
kubectl apply -f $K8S_DIR/namespace.yaml

echo ""
echo "Step 2: Creating secrets..."
echo "NOTE: Edit $K8S_DIR/secret.yaml with your credentials before deploying!"
read -p "Have you updated the secrets? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please edit $K8S_DIR/secret.yaml and run this script again"
    exit 1
fi
kubectl apply -f $K8S_DIR/secret.yaml

echo ""
echo "Step 3: Creating ConfigMap..."
kubectl apply -f $K8S_DIR/configmap.yaml

echo ""
echo "Step 4: Creating PersistentVolumeClaim..."
kubectl apply -f $K8S_DIR/pvc.yaml

echo ""
echo "Step 5: Creating Deployment..."
# Update image in deployment if custom image is specified
if [ "$IMAGE" != "risk-assessor:latest" ]; then
    echo "Updating deployment to use image: $IMAGE"
    cat $K8S_DIR/deployment.yaml | sed "s|image: risk-assessor:latest|image: $IMAGE|g" | kubectl apply -f -
else
    kubectl apply -f $K8S_DIR/deployment.yaml
fi

echo ""
echo "Step 6: Creating Service..."
kubectl apply -f $K8S_DIR/service.yaml

echo ""
echo "Optional: Deploy CronJob for scheduled syncing? (y/N)"
read -p "" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f $K8S_DIR/cronjob.yaml
    echo "CronJob deployed"
fi

echo ""
echo "Optional: Enable HorizontalPodAutoscaler? (y/N)"
read -p "" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f $K8S_DIR/hpa.yaml
    echo "HPA deployed"
fi

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Check deployment status:"
echo "  kubectl get all -n $NAMESPACE"
echo ""
echo "View logs:"
echo "  kubectl logs -n $NAMESPACE -l app=risk-assessor"
echo ""
echo "Run a command:"
echo "  kubectl exec -n $NAMESPACE -it \$(kubectl get pods -n $NAMESPACE -l app=risk-assessor -o jsonpath='{.items[0].metadata.name}') -- risk-assessor --help"
echo ""
