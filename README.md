# Cloud Optimizer Platform

A comprehensive platform for optimizing cloud resources and costs across multiple cloud providers (AWS, Azure, GCP).

## Features

- **Multi-cloud Support**: Integrate with AWS, Azure, and Google Cloud
- **Resource Management**: View and manage resources across different cloud providers
- **Cost Analysis**: Analyze and compare costs across cloud providers
- **Dashboard**: Visualize cloud usage and cost data
- **Simulation Mode**: Test the platform without actual cloud credentials

## Architecture

The Cloud Optimizer Platform consists of the following components:

- **API Gateway**: Central entry point for all API requests
- **Cloud Cost Normalization**: Service for normalizing cost data across providers
- **Frontend**: React-based web interface for interacting with the platform

## Prerequisites

- Docker and Docker Compose
- Node.js and npm (for local frontend development)
- Python 3.9+ (for local backend development)

## Getting Started

### Using Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cloud-optimizer-platform.git
   cd cloud-optimizer-platform
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Access the platform:
   - Frontend: http://localhost
   - API Gateway: http://localhost:8000
   - Cloud Cost Normalization: http://localhost:8001

### Local Development

#### Backend Services

1. Create a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # On Windows
   source venv/bin/activate     # On macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the API Gateway:
   ```bash
   cd scripts
   python run_api_gateway.py
   ```

4. Run the Cloud Cost Normalization service:
   ```bash
   cd scripts
   python run_cost_normalization.py
   ```

#### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

## API Documentation

- API Gateway Swagger UI: http://localhost:8000/docs
- Cloud Cost Normalization Swagger UI: http://localhost:8001/docs

## Cloud Provider Configuration

By default, the platform runs in simulation mode, which doesn't require actual cloud credentials. To use real cloud provider credentials:

### AWS
- Set environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`

### Azure
- Set environment variables: `AZURE_SUBSCRIPTION_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`

### GCP
- Set environment variables: `GCP_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`

## License

[MIT License](LICENSE)
