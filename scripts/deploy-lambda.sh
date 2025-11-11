#!/bin/bash
# Deploy RiskAssessor to AWS Lambda using Serverless Framework
# Usage: ./scripts/deploy-lambda.sh [stage]

set -e

STAGE=${1:-dev}
LAMBDA_DIR="deployments/serverless/aws-lambda"

echo "========================================="
echo "RiskAssessor AWS Lambda Deployment"
echo "========================================="
echo "Stage: $STAGE"
echo ""

# Check if serverless is installed
if ! command -v serverless &> /dev/null; then
    echo "Installing Serverless Framework..."
    npm install -g serverless
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured"
    echo "Please run: aws configure"
    exit 1
fi

echo "AWS Account: $(aws sts get-caller-identity --query Account --output text)"
echo ""

# Check required environment variables
MISSING_VARS=()
[ -z "$GITHUB_TOKEN" ] && MISSING_VARS+=("GITHUB_TOKEN")
[ -z "$GITHUB_REPO" ] && MISSING_VARS+=("GITHUB_REPO")
[ -z "$OPENAI_API_KEY" ] && MISSING_VARS+=("OPENAI_API_KEY")

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "Error: Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please set these variables before deploying:"
    echo '  export GITHUB_TOKEN="your-token"'
    echo '  export GITHUB_REPO="owner/repo"'
    echo '  export OPENAI_API_KEY="your-key"'
    exit 1
fi

# Navigate to Lambda directory
cd $LAMBDA_DIR

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm init -y 2>/dev/null || true
    npm install --save-dev serverless-python-requirements
fi

# Copy requirements
if [ ! -f "requirements.txt" ]; then
    echo "Copying requirements.txt..."
    cp ../../../requirements.txt .
fi

# Confirm deployment
echo ""
read -p "Deploy to AWS Lambda in stage '$STAGE'? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Deploy
echo ""
echo "Deploying to AWS Lambda..."
serverless deploy --stage $STAGE

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Get deployment info:"
echo "  serverless info --stage $STAGE"
echo ""
echo "Invoke function:"
echo "  serverless invoke -f assessor --stage $STAGE -d '{\"operation\": \"catalog-stats\"}'"
echo ""
echo "View logs:"
echo "  serverless logs -f assessor --stage $STAGE -t"
echo ""
echo "Remove deployment:"
echo "  serverless remove --stage $STAGE"
echo ""
