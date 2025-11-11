# RiskAssessor Azure Functions Deployment

Deploy RiskAssessor as Azure Functions.

## Prerequisites

- Azure account with active subscription
- Azure CLI installed (`az`)
- Azure Functions Core Tools installed
- Python 3.11 installed

## Setup

### 1. Install Azure CLI and Functions Core Tools

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

### 2. Login to Azure

```bash
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

### 3. Create Resources

```bash
# Set variables
RESOURCE_GROUP="risk-assessor-rg"
LOCATION="eastus"
STORAGE_ACCOUNT="riskassessorsa"
FUNCTION_APP="risk-assessor-func"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create Function App (Linux, Python 3.11)
az functionapp create \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --storage-account $STORAGE_ACCOUNT \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux
```

### 4. Configure Application Settings

```bash
# Set environment variables
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    GITHUB_TOKEN="your-github-token" \
    GITHUB_REPO="owner/repo" \
    OPENAI_API_KEY="your-openai-key" \
    LLM_MODEL="gpt-4" \
    RISK_CATALOG_PATH="/tmp/.risk_assessor/catalog.json"
```

## Deployment

### Deploy Function App

```bash
cd deployments/serverless/azure-functions

# Deploy
func azure functionapp publish $FUNCTION_APP
```

### Deploy with Azure CLI

```bash
# Zip the function app
cd deployments/serverless/azure-functions
zip -r function-app.zip .

# Deploy
az functionapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --src function-app.zip
```

## Usage

### Get Function URL and Key

```bash
# Get function URL
FUNCTION_URL=$(az functionapp function show \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --function-name RiskAssessorHttp \
  --query invokeUrlTemplate -o tsv)

# Get function key
FUNCTION_KEY=$(az functionapp keys list \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP \
  --query functionKeys.default -o tsv)

echo "Function URL: $FUNCTION_URL"
echo "Function Key: $FUNCTION_KEY"
```

### Invoke via HTTP

```bash
# Assess a PR
curl -X POST "$FUNCTION_URL?code=$FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "assess-pr",
    "params": {
      "pr_number": 123
    }
  }'

# Assess commits
curl -X POST "$FUNCTION_URL?code=$FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "assess-commits",
    "params": {
      "base": "main",
      "head": "develop"
    }
  }'

# Get catalog stats
curl -X POST "$FUNCTION_URL?code=$FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "catalog-stats",
    "params": {}
  }'
```

### Local Testing

```bash
cd deployments/serverless/azure-functions

# Create local settings
cat > local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "GITHUB_TOKEN": "your-github-token",
    "GITHUB_REPO": "owner/repo",
    "OPENAI_API_KEY": "your-openai-key",
    "LLM_MODEL": "gpt-4"
  }
}
EOF

# Start local function
func start

# Test locally
curl -X POST http://localhost:7071/api/assess \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "catalog-stats",
    "params": {}
  }'
```

## Monitoring

### View Logs

```bash
# Stream logs
func azure functionapp logstream $FUNCTION_APP

# Or use Azure CLI
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP
```

### Application Insights

```bash
# Enable Application Insights
az monitor app-insights component create \
  --app risk-assessor-insights \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Link to Function App
INSIGHTS_KEY=$(az monitor app-insights component show \
  --app risk-assessor-insights \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey -o tsv)

az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSIGHTS_KEY
```

## Security

### Use Key Vault for Secrets

```bash
# Create Key Vault
az keyvault create \
  --name risk-assessor-kv \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Add secrets
az keyvault secret set \
  --vault-name risk-assessor-kv \
  --name github-token \
  --value "your-github-token"

az keyvault secret set \
  --vault-name risk-assessor-kv \
  --name openai-api-key \
  --value "your-openai-key"

# Enable managed identity for Function App
az functionapp identity assign \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP

# Grant access to Key Vault
PRINCIPAL_ID=$(az functionapp identity show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

az keyvault set-policy \
  --name risk-assessor-kv \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list

# Reference in app settings
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings \
    "GITHUB_TOKEN=@Microsoft.KeyVault(SecretUri=https://risk-assessor-kv.vault.azure.net/secrets/github-token/)" \
    "OPENAI_API_KEY=@Microsoft.KeyVault(SecretUri=https://risk-assessor-kv.vault.azure.net/secrets/openai-api-key/)"
```

## Queue Processing

### Setup Storage Queue

```bash
# Create queue
az storage queue create \
  --name risk-assessor-queue \
  --account-name $STORAGE_ACCOUNT

# Send message
az storage message put \
  --queue-name risk-assessor-queue \
  --account-name $STORAGE_ACCOUNT \
  --content '{"operation": "assess-pr", "params": {"pr_number": 123}}'
```

## Scaling

### Configure Auto-scaling

```bash
# Update to Premium plan for more control
az functionapp plan create \
  --name risk-assessor-plan \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku EP1 \
  --is-linux

# Move function to plan
az functionapp update \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --plan risk-assessor-plan
```

## Cost Optimization

### Consumption Plan Pricing

- First 1M executions/month: Free
- After: $0.20 per 1M executions
- Compute: $0.000016 per GB-second

### Monitor Costs

```bash
# View cost analysis
az consumption usage list \
  --start-date 2024-01-01 \
  --end-date 2024-01-31
```

## Troubleshooting

### Function Not Running

```bash
# Check function status
az functionapp show \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP

# Restart function
az functionapp restart \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP
```

### Dependency Issues

```bash
# SSH into function (Premium plan only)
az webapp create-remote-connection \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP
```

## Cleanup

```bash
# Delete resource group (removes all resources)
az group delete --name $RESOURCE_GROUP --yes
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Deploy to Azure Functions
  uses: Azure/functions-action@v1
  with:
    app-name: ${{ env.FUNCTION_APP }}
    package: deployments/serverless/azure-functions
    publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

### Azure DevOps

```yaml
- task: AzureFunctionApp@1
  inputs:
    azureSubscription: 'Azure-Service-Connection'
    appType: 'functionAppLinux'
    appName: '$(FUNCTION_APP)'
    package: '$(System.DefaultWorkingDirectory)/deployments/serverless/azure-functions'
```
