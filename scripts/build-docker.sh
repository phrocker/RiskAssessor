#!/bin/bash
# Build and push RiskAssessor Docker image
# Usage: ./scripts/build-docker.sh [registry/image:tag]

set -e

IMAGE=${1:-risk-assessor:latest}

echo "========================================="
echo "RiskAssessor Docker Build"
echo "========================================="
echo "Image: $IMAGE"
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed or not in PATH"
    exit 1
fi

# Build the image
echo "Building Docker image..."
docker build -t $IMAGE .

echo ""
echo "Build complete!"
echo "Image: $IMAGE"
echo ""

# Ask if user wants to push
if [[ $IMAGE == *"/"* ]]; then
    read -p "Push image to registry? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Pushing image to registry..."
        docker push $IMAGE
        echo "Push complete!"
    fi
fi

echo ""
echo "Test the image locally:"
echo "  docker run --rm $IMAGE risk-assessor --help"
echo ""
echo "Run with environment variables:"
echo '  docker run --rm \'
echo '    -e GITHUB_TOKEN="your-token" \'
echo '    -e GITHUB_REPO="owner/repo" \'
echo '    -e OPENAI_API_KEY="your-key" \'
echo "    $IMAGE \\"
echo "    risk-assessor assess-pr --pr 123"
echo ""
