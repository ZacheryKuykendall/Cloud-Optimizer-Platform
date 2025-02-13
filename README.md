# Cloud Optimizer Platform

A project to optimize cloud resources.

- src/ contains the source code (an Express-based API server).
- config/ contains configuration files.
- cloud-cost-normalization/ houses a microservice with its own Dockerfile.
- package.json contains project metadata.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [CLI Tool](#cli-tool)
- [Dashboard](#dashboard)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Cloud Optimizer Platform integrates multiple microservices including a cost normalization service and a core API server built with Node.js/Express. It provides cost analysis, resource optimization, and cross-cloud networking capabilities.

### Key Features

- Multi-cloud cost analysis and normalization
- Resource optimization recommendations
- Cross-cloud network management
- Cost forecasting and budgeting
- Resource inventory management
- Interactive dashboard
- Command-line interface

## Architecture

The platform consists of several microservices:

```
cloud-optimizer/
├── api-gateway-service/        # API Gateway
├── aws-cost-explorer-client/   # AWS Cost API Client
├── azure-cost-management-client/ # Azure Cost API Client
├── gcp-billing-client/         # GCP Billing API Client
├── cloud-cost-normalization/   # Cost Data Normalization
├── cloud-network-manager/      # Cross-Cloud Networking
├── cloud-cost-optimizer/       # Cost Optimization Engine
├── cost-dashboard/            # Web Dashboard
└── cloud-optimizer-cli/       # Command Line Interface
```

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- Docker and Docker Compose
- Cloud Provider Accounts:
  - AWS Account with Cost Explorer API access
  - Azure Subscription with Cost Management API access
  - GCP Project with Cloud Billing API enabled

## Installation

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Start the API server:
```bash
npm start
```

3. Visit http://localhost:3000 to verify the service is running.

### Dockerized Services

- To build & run the cloud-cost-normalization service:
```bash
cd cloud-cost-normalization
docker build -t cloud-cost-normalization .
docker run -p 8000:8000 cloud-cost-normalization
```

- Use docker-compose for orchestrated startups if provided.

## Configuration

### AWS Configuration

1. Create AWS credentials:
   - Go to AWS IAM Console
   - Create a new IAM user with programmatic access
   - Attach the following policies:
     - `AWSCostExplorerServiceFullAccess`
     - `AWSResourceGroupsReadOnlyAccess`

2. Configure credentials:
```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="your-region"

# Option 2: AWS credentials file
aws configure
```

### Azure Configuration

1. Create Azure service principal:
```bash
az ad sp create-for-rbac --name "CloudOptimizer" --role "Cost Management Reader"
```

2. Configure credentials:
```bash
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

### GCP Configuration

1. Create service account and key:
   - Go to GCP Console > IAM & Admin > Service Accounts
   - Create new service account with "Billing Account Viewer" role
   - Create and download JSON key file

2. Configure credentials:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

## Usage

### Starting the Platform

1. Start all services:
```bash
docker-compose up -d
```

2. Verify services are running:
```bash
docker-compose ps
```

3. Access the dashboard:
```bash
open http://localhost:3000
```

### Basic Operations

1. Resource Inventory:
```bash
# List all resources
cloud-optimizer resources list

# Get resource details
cloud-optimizer resources get <resource-id>
```

2. Cost Analysis:
```bash
# Get cost overview
cloud-optimizer costs analyze --last-30-days

# Compare costs across providers
cloud-optimizer costs compare --resource-type vm
```

3. Optimization:
```bash
# Get optimization recommendations
cloud-optimizer optimize analyze

# Apply optimization
cloud-optimizer optimize apply <recommendation-id>
```

## CLI Tool

The `cloud-optimizer` CLI provides comprehensive command-line access to all platform features.

### Global Commands

```bash
# Get help
cloud-optimizer --help

# Version info
cloud-optimizer version

# Configure CLI
cloud-optimizer configure
```

### Cost Management

```bash
# Get cost summary
cloud-optimizer costs summary --start-date 2023-01-01 --end-date 2023-12-31

# Export cost report
cloud-optimizer costs export --format csv --output costs.csv

# Set budget alert
cloud-optimizer budget set --amount 1000 --currency USD
```

### Resource Management

```bash
# List resources by type
cloud-optimizer resources list --type compute

# Get resource metrics
cloud-optimizer resources metrics <resource-id>

# Tag resources
cloud-optimizer resources tag <resource-id> --tags env=prod
```

### Network Management

```bash
# List VPN connections
cloud-optimizer network vpn list

# Create VPN connection
cloud-optimizer network vpn create --source aws-vpc-1 --target azure-vnet-1

# Monitor connection
cloud-optimizer network vpn monitor <connection-id>
```

## Dashboard

The web dashboard provides a visual interface for managing the platform.

### Dashboard Sections

1. **Overview**
   - Total costs across providers
   - Resource utilization
   - Active optimizations

2. **Cost Analysis**
   - Detailed cost breakdowns
   - Historical trends
   - Provider comparisons

3. **Resource Management**
   - Resource inventory
   - Performance metrics
   - Configuration management

4. **Optimization**
   - Recommendations
   - Implementation plans
   - Savings tracking

### Dashboard Features

1. **Interactive Visualizations**
   - Cost trends
   - Resource usage
   - Provider comparisons

2. **Real-time Monitoring**
   - Resource metrics
   - Cost tracking
   - Alert notifications

3. **Report Generation**
   - Cost reports
   - Resource inventories
   - Optimization summaries

## API Documentation

API documentation is available at:
- Development: http://localhost:8080/docs
- Production: https://api.cloudoptimizer.example.com/docs

## Troubleshooting

### Common Issues

1. **Service Connection Issues**
   ```bash
   # Check service status
   docker-compose ps
   
   # View service logs
   docker-compose logs <service-name>
   ```

2. **Authentication Issues**
   - Verify cloud provider credentials
   - Check API access permissions
   - Review service principal settings

3. **Performance Issues**
   - Check resource allocation
   - Review database indexes
   - Monitor API rate limits

### Debug Mode

Enable debug logging:
```bash
export CLOUD_OPTIMIZER_DEBUG=1
```

### Support

- GitHub Issues: [Report a bug](https://github.com/your-org/cloud-optimizer/issues)
- Documentation: [Wiki](https://github.com/your-org/cloud-optimizer/wiki)
- Community: [Discussions](https://github.com/your-org/cloud-optimizer/discussions)

## System Verification

To verify that all components are working correctly and properly integrated:

1. Install health check dependencies:
```bash
cd scripts
python -m pip install -r requirements.txt
```

2. Run the health check:
```bash
# Basic check
python health_check.py

# Detailed output
python health_check.py --verbose

# Save results to file
python health_check.py --output health_check_results.json
```

The health check will verify:
- All service endpoints are responding
- Cloud provider integrations are working
- Cross-cloud networking is operational
- Data normalization is functioning
- Monitoring system is active

## Troubleshooting

If you encounter issues:

1. Check service logs:
```bash
docker-compose logs <service-name>
```

2. Verify environment variables:
```bash
# Copy example env file
cp .env.example .env

# Edit with your credentials
nano .env
```

3. Common issues:
- Cloud provider credentials not set or expired
- Required ports already in use
- Insufficient permissions for cross-cloud operations
- Database connection issues

4. Monitor metrics:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (default password in .env.example)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Cloud Optimizer Platform

## Building and Running

### Prerequisites
- Docker
- Docker Compose

### Build and Run
```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check service health
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # Cost Analyzer
curl http://localhost:8002/health  # Resource Optimizer
curl http://localhost:8003/health  # Cloud Cost Normalization

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```
