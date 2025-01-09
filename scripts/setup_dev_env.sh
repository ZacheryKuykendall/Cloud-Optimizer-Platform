#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[-]${NC} $1"
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed"
        return 1
    else
        print_status "$1 is installed ($(command -v $1))"
        return 0
    fi
}

# Check system requirements
print_status "Checking system requirements..."

REQUIREMENTS=(python3 pip node npm docker docker-compose)
MISSING_REQUIREMENTS=0

for cmd in "${REQUIREMENTS[@]}"; do
    if ! check_command $cmd; then
        MISSING_REQUIREMENTS=1
    fi
done

if [ $MISSING_REQUIREMENTS -eq 1 ]; then
    print_error "Please install missing requirements and run this script again"
    exit 1
fi

# Create Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
pip install -r scripts/requirements.txt

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
cd ../cost-dashboard
npm install
cd ../scripts

# Check if .env file exists
if [ ! -f ../.env ]; then
    print_status "Creating .env file from template..."
    cp ../.env.example ../.env
    print_warning "Please update ../.env with your credentials"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ../logs
mkdir -p ../data/prometheus
mkdir -p ../data/grafana

# Set correct permissions
print_status "Setting file permissions..."
chmod +x health_check.py
chmod 600 ../.env

# Verify Docker configuration
print_status "Verifying Docker configuration..."
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running"
    exit 1
fi

# Pull required Docker images
print_status "Pulling Docker images..."
docker-compose -f ../docker-compose.yml pull

# Build local images
print_status "Building local images..."
docker-compose -f ../docker-compose.yml build

# Run health check
print_status "Running initial health check..."
./health_check.py --verbose

# Final instructions
echo
print_status "Development environment setup complete!"
echo
echo "Next steps:"
echo "1. Update the .env file with your cloud provider credentials"
echo "2. Start the services with: docker-compose up -d"
echo "3. Access the dashboard at: http://localhost:3000"
echo "4. Monitor the system at: http://localhost:9090 (Prometheus)"
echo "                         http://localhost:3001 (Grafana)"
echo
print_warning "Remember to never commit the .env file to version control"

# Activate virtual environment if script is sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    print_status "Activating Python virtual environment..."
    source venv/bin/activate
fi
