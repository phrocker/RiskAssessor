# Regional Configuration Examples

This example shows how to configure cloud-agnostic regional validation in RiskAssessor.

## AWS Configuration

```yaml
# GitHub Configuration
github:
  token: ${GITHUB_TOKEN}
  repo: owner/repository

# LLM Configuration
llm:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4

# Regional Configuration for AWS
regional:
  cloud_provider: aws
  regions:
    us-east-1:
      features: [ec2, rds, s3, lambda, dynamodb, eks, ecs, elasticache, kinesis, sqs, sns]
      region_type: standard
      availability_zones: 3
    
    us-gov-west-1:
      # GovCloud has limited service availability
      features: [ec2, rds, s3]
      region_type: govcloud
      availability_zones: 2
    
    ap-southeast-1:
      features: [ec2, rds, s3, lambda, dynamodb, eks, ecs]
      region_type: standard
      availability_zones: 3
```

## Azure Configuration

```yaml
regional:
  cloud_provider: azure
  regions:
    eastus:
      features: [virtual_machines, app_service, sql_database, cosmos_db, storage, functions, aks, container_instances, redis_cache, service_bus]
      region_type: standard
      paired_region: westus
    
    westeurope:
      features: [virtual_machines, app_service, sql_database, storage, functions, aks]
      region_type: standard
      paired_region: northeurope
```

## GCP Configuration

```yaml
regional:
  cloud_provider: gcp
  regions:
    us-central1:
      features: [compute_engine, cloud_sql, cloud_storage, cloud_functions, cloud_run, gke, firestore, bigtable, memorystore, pub_sub]
      region_type: standard
      zones: 3
    
    asia-northeast1:
      features: [compute_engine, cloud_sql, cloud_storage, cloud_functions, gke]
      region_type: standard
      zones: 3
```

## Custom/Bare-Metal Configuration

For custom infrastructure or bare-metal deployments:

```yaml
regional:
  cloud_provider: custom
  regions:
    datacenter-nyc-1:
      # Simple list format
      features: [kubernetes, postgresql, redis, rabbitmq, nginx]
      metadata:
        location: New York, USA
        capacity: high
        network: 10Gbps
    
    datacenter-london-1:
      # Detailed format with availability status
      features:
        - name: kubernetes
          available: true
          metadata:
            version: "1.28"
        - name: postgresql
          available: true
          metadata:
            version: "15.3"
        - name: mongodb
          available: false
          metadata:
            reason: "Not yet deployed"
        - name: object_storage
          available: true
          metadata:
            type: MinIO
      metadata:
        location: London, UK
        capacity: medium
```

## Bare-Metal Infrastructure

```yaml
regional:
  cloud_provider: bare_metal
  regions:
    rack-a-zone-1:
      features:
        - name: load_balancer
          available: true
          metadata:
            type: HAProxy
            capacity: 10k req/s
        - name: container_runtime
          available: true
          metadata:
            type: containerd
        - name: storage_block
          available: true
          metadata:
            type: Ceph
            capacity_tb: 100
        - name: storage_object
          available: false
          metadata:
            reason: "Planned for Q2"
      metadata:
        datacenter: Primary DC
        power: redundant
        cooling: N+1
    
    rack-b-zone-1:
      features: [load_balancer, container_runtime]
      metadata:
        datacenter: Primary DC
        power: single
```

## How It Works

When you configure regional validation:

1. **Deployment Region**: Specify the target region when assessing risk
   ```bash
   risk-assessor assess-pr-contract --pr 123 --deployment-region us-gov-west-1
   ```

2. **Feature Availability Check**: RiskAssessor will:
   - Validate that the region exists in your configuration
   - Check which features are available in that region
   - Identify missing features that could increase deployment risk

3. **Risk Assessment**: Missing features are factored into the risk calculation:
   - Adds an "operational" risk factor for regional feature availability
   - Lists unavailable features in the risk contract
   - Provides recommendations based on missing capabilities

## Example Risk Contract Output

When deploying to a region with limited features:

```json
{
  "factors": [
    {
      "category": "operational",
      "factor_name": "Regional Feature Availability",
      "impact_weight": 0.15,
      "observed_value": "3 features unavailable in us-gov-west-1",
      "assessment": "Missing features: lambda, dynamodb, eks"
    }
  ],
  "recommendations": [
    "Verify that deployment does not require unavailable services in us-gov-west-1",
    "Consider alternative region if lambda, dynamodb, or eks are critical dependencies"
  ]
}
```

## Benefits

- **Cloud Agnostic**: Works with AWS, Azure, GCP, and custom infrastructure
- **Flexible**: Simple list or detailed feature configuration
- **Risk Aware**: Automatically factors regional limitations into risk scores
- **Customizable**: Define your own regions and features for any infrastructure
