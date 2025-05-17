# Cloud Optimizer Platform Scripts

This directory contains utility scripts for running and managing the Cloud Optimizer Platform services.

## Setup

Before running any scripts, install the required dependencies:

```powershell
# Create and activate a virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r ..\requirements.txt
```

## Available Scripts

### run_api_gateway.py

Runs the API Gateway service with simulation mode enabled by default.

```powershell
# Run with default settings (simulation mode enabled)
python run_api_gateway.py

# Run with specific port
python run_api_gateway.py --port 8080

# Run with real cloud credentials (disable simulation)
python run_api_gateway.py --no-simulation
```

### restart_api_gateway.py

Stops any running API Gateway processes and then starts a new API Gateway service.

```powershell
# Restart with default settings (simulation mode enabled)
python restart_api_gateway.py

# Restart with specific port
python restart_api_gateway.py --port 8080

# Restart with real cloud credentials (disable simulation)
python restart_api_gateway.py --no-simulation
```

### run_cost_normalization.py

Runs the Cloud Cost Normalization service with simulation mode enabled by default.

```powershell
# Run with default settings (simulation mode enabled)
python run_cost_normalization.py

# Run with specific port
python run_cost_normalization.py --port 8081

# Run with real cloud credentials (disable simulation)
python run_cost_normalization.py --no-simulation
```

## Using Simulation Mode

Simulation mode provides realistic-looking but entirely simulated data for development and testing. This allows you to:

1. Develop and test without actual cloud credentials
2. Generate consistent data for UI development
3. Demonstrate the application's capabilities without connecting to real cloud resources

To force simulation mode globally, set the environment variable:

```powershell
$env:CLOUD_OPTIMIZER_SIMULATION = "true"
```

## Adding New Scripts

When adding new scripts, please follow these conventions:

1. Include a docstring explaining the purpose of the script
2. Add command-line arguments with sensible defaults
3. Handle errors gracefully
4. Update this README with usage instructions 