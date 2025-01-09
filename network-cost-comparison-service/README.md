# Network Cost Comparison Service

A Python service for comparing network costs across different cloud providers, providing detailed cost analysis, performance metrics, and optimization recommendations.

## Features

- Multi-Cloud Network Cost Analysis:
  - AWS Network Services:
    - VPC and Networking
    - Load Balancers (ALB, NLB)
    - VPN Connections
    - Direct Connect
    - Transit Gateway
    - CloudFront (CDN)
    - Route 53 (DNS)
    - WAF & Shield
  - Azure Network Services:
    - Virtual Network
    - Load Balancer
    - Application Gateway
    - ExpressRoute
    - Virtual WAN
    - Front Door & CDN
    - DNS
    - DDoS Protection
  - Google Cloud Network Services:
    - VPC Network
    - Load Balancing
    - Cloud Interconnect
    - Cloud VPN
    - Network Intelligence
    - Cloud CDN
    - Cloud DNS
    - Cloud Armor

- Network Service Types:
  - Virtual Private Clouds (VPC)
  - Load Balancers
  - VPN Connections
  - Direct Connect/ExpressRoute
  - Transit/Virtual WAN
  - Content Delivery Networks
  - DNS Services
  - Web Application Firewalls
  - Network Firewalls
  - NAT Gateways
  - VPC Endpoints

- Comprehensive Analysis:
  - Cost breakdown
  - Performance metrics
  - Feature comparison
  - Compliance requirements
  - Availability analysis
  - Network topology

- Advanced Features:
  - Real-time pricing updates
  - Network performance testing
  - Cost optimization recommendations
  - Compliance requirements checking
  - Regional availability analysis

## Installation

```bash
pip install network-cost-comparison-service
```

## Prerequisites

- Python 3.8 or higher
- Cloud provider credentials:
  - AWS credentials
  - Azure credentials
  - GCP credentials
- Optional dependencies:
  - Redis (for caching)
  - PostgreSQL (for historical data)

## Quick Start

### Basic Network Comparison

```python
from network_comparison import (
    ComparisonRequest,
    ComparisonCriteria,
    NetworkRequirements,
    NetworkServiceType,
    CloudProvider
)

# Configure network requirements
requirements = NetworkRequirements(
    service_type=NetworkServiceType.VPC,
    min_bandwidth_gbps=10.0,
    ipv6_required=True,
    max_latency_ms=50.0
)

# Create comparison criteria
criteria = ComparisonCriteria(
    requirements=requirements,
    regions=["us-east-1", "us-east", "us-central1"],
    time_period=timedelta(days=30),
    estimated_data_transfer_gb=5000.0
)

# Create comparison request
request = ComparisonRequest(
    criteria=criteria,
    include_performance_metrics=True
)

# Get comparison results
comparator = NetworkComparator()
response = comparator.compare(request)

# Process results
print(f"Recommended Option: {response.results.recommended_option.service.service_name}")
print(f"Monthly Cost: ${response.results.recommended_option.monthly_cost}")

# Show alternatives
for alt in response.results.alternatives[:3]:
    print(f"\nAlternative: {alt.service.service_name}")
    print(f"Provider: {alt.service.provider}")
    print(f"Monthly Cost: ${alt.monthly_cost}")
```

### Detailed Cost Analysis

```python
from network_comparison import NetworkTier, AvailabilityLevel

# Configure detailed comparison
criteria = ComparisonCriteria(
    requirements=NetworkRequirements(
        service_type=NetworkServiceType.LOAD_BALANCER,
        min_bandwidth_gbps=20.0,
        network_tier=NetworkTier.PREMIUM,
        availability_level=AvailabilityLevel.MULTI_REGION
    ),
    preferred_providers=[CloudProvider.AWS, CloudProvider.AZURE],
    regions=["us-east-1", "us-east"],
    time_period=timedelta(days=365),
    estimated_data_transfer_gb=10000.0,
    estimated_request_count=1000000,
    expected_growth_rate=0.2  # 20% growth per year
)

# Get detailed comparison
response = comparator.compare_detailed(
    criteria,
    include_performance_metrics=True,
    include_cost_breakdown=True,
    include_savings_analysis=True
)

# Process cost breakdown
for estimate in response.results.estimates:
    print(f"\nService: {estimate.service.service_name}")
    print(f"Provider: {estimate.service.provider}")
    print(f"Base Cost: ${estimate.cost_breakdown.base_cost}")
    print(f"Data Transfer Cost: ${estimate.cost_breakdown.data_transfer_cost}")
    print(f"Request Cost: ${estimate.cost_breakdown.request_cost}")
    
    # Show savings opportunities
    for opportunity, amount in estimate.savings_opportunities.items():
        print(f"Potential Saving ({opportunity}): ${amount}")
```

### Performance Analysis

```python
from network_comparison import PerformanceMetrics

# Get performance metrics
metrics = response.performance_metrics

for service_id, metric in metrics.items():
    service = next(e for e in response.results.estimates 
                  if e.service.id == service_id)
    
    print(f"\nService: {service.service.service_name}")
    print(f"Bandwidth Score: {metric.bandwidth_score}")
    print(f"Latency Score: {metric.latency_score}")
    print(f"Reliability Score: {metric.reliability_score}")
    print(f"Availability Score: {metric.availability_score}")
    print(f"Overall Score: {metric.overall_score}")
```

## Advanced Usage

### Custom Network Requirements

```python
# Configure custom requirements
requirements = NetworkRequirements(
    service_type=NetworkServiceType.VPN,
    min_bandwidth_gbps=5.0,
    network_tier=NetworkTier.ENTERPRISE,
    availability_level=AvailabilityLevel.REGIONAL,
    min_availability=99.99,  # SLA percentage
    required_features={
        "ddos_protection",
        "flow_logs",
        "packet_capture"
    },
    max_latency_ms=10.0,
    max_packet_loss=0.01,
    compliance_requirements={
        "hipaa",
        "pci_dss",
        "gdpr"
    }
)

# Create comparison criteria
criteria = ComparisonCriteria(
    requirements=requirements,
    regions=["us-east-1", "us-east"],
    time_period=timedelta(days=365),
    estimated_data_transfer_gb=50000.0,
    performance_requirements={
        "min_throughput": 4.5,  # Gbps
        "max_jitter": 2.0       # ms
    },
    compliance_requirements={
        "data_residency": "US",
        "encryption_standard": "AES-256"
    }
)
```

### Caching and Performance

```python
# Configure caching
comparator = NetworkComparator(
    cache_config={
        "pricing_ttl": 3600,  # 1 hour
        "service_ttl": 86400,  # 24 hours
        "redis_url": "redis://localhost:6379"
    }
)

# Batch comparison
results = comparator.compare_batch(
    requests=[request1, request2, request3],
    parallel=True,
    max_workers=4
)
```

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/network-cost-comparison-service.git
cd network-cost-comparison-service
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_comparator.py
```

### Code Style

The project uses several tools to maintain code quality:

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy src tests

# Linting
pylint src tests
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [AWS Cost Explorer Client](https://github.com/yourusername/aws-cost-explorer-client)
- [Azure Cost Management Client](https://github.com/yourusername/azure-cost-management-client)
- [GCP Billing Client](https://github.com/yourusername/gcp-billing-client)
- [Cloud Cost Normalization](https://github.com/yourusername/cloud-cost-normalization)
- [Cost Estimation Engine](https://github.com/yourusername/cost-estimation-engine)

## Acknowledgments

- Cloud provider pricing APIs
- Network performance tools
- Cost analysis libraries
- Data visualization packages
