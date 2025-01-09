# Currency Conversion Service

A Python service for handling currency conversions and exchange rates, specifically designed for cloud cost data. This service provides a robust platform for converting costs between different currencies, managing exchange rates, and handling batch operations.

## Features

- Multiple Rate Providers:
  - Forex Python
  - European Central Bank
  - Open Exchange Rates
  - Custom providers
  - Fallback strategies

- Exchange Rate Management:
  - Real-time rate fetching
  - Historical rates
  - Rate caching
  - Rate validation
  - Stale rate detection

- Conversion Operations:
  - Single currency conversions
  - Batch conversions
  - Historical conversions
  - Forward rate conversions
  - Custom rate types

- Caching Strategies:
  - In-memory cache
  - Redis cache
  - Database cache
  - Custom cache implementations

- Monitoring & Alerts:
  - Rate change alerts
  - Conversion metrics
  - Provider health checks
  - Performance monitoring
  - Error tracking

## Installation

```bash
pip install currency-conversion-service
```

## Prerequisites

- Python 3.8 or higher
- Redis (optional, for Redis caching)
- PostgreSQL (optional, for persistent storage)
- API keys for rate providers:
  - Open Exchange Rates API key
  - Other provider credentials as needed

## Quick Start

### Basic Usage

```python
from currency_conversion import (
    Money,
    ConversionRequest,
    RateSource,
    RateType
)

# Create a conversion request
request = ConversionRequest(
    amount=Money(amount=100, currency="USD"),
    target_currency="EUR",
    rate_source=RateSource.FOREX
)

# Perform conversion
result = converter.convert(request)
print(f"Converted amount: {result.result.amount} {result.result.currency}")
```

### Batch Conversions

```python
from currency_conversion import ConversionBatch

# Create batch request
batch = ConversionBatch(
    requests=[
        ConversionRequest(amount=Money(100, "USD"), target_currency="EUR"),
        ConversionRequest(amount=Money(200, "GBP"), target_currency="EUR"),
        ConversionRequest(amount=Money(300, "JPY"), target_currency="EUR")
    ],
    target_currency="EUR"
)

# Process batch
result = converter.convert_batch(batch)

# Process results
for conversion in result.results:
    print(f"{conversion.request.amount} -> {conversion.result}")
```

### Rate Provider Configuration

```python
from currency_conversion import (
    RateProviderConfig,
    UpdateFrequency,
    CacheStrategy
)

# Configure rate provider
config = RateProviderConfig(
    provider=RateSource.OPEN_EXCHANGE,
    api_key="your-api-key",
    update_frequency=UpdateFrequency.HOURLY,
    cache_strategy=CacheStrategy.REDIS,
    timeout_seconds=30,
    retry_attempts=3
)

# Initialize provider
converter.configure_provider(config)
```

### Rate Alerts

```python
from currency_conversion import RateAlert

# Create rate alert
alert = RateAlert(
    source_currency="USD",
    target_currency="EUR",
    threshold=0.05,  # 5% change
    condition="change_percent",
    notification_channels=["email", "slack"]
)

# Register alert
converter.register_alert(alert)
```

## Advanced Usage

### Custom Rate Provider

```python
from currency_conversion import RateSource, ExchangeRate

class CustomProvider:
    def get_rate(self, source: str, target: str) -> ExchangeRate:
        # Implement custom rate fetching logic
        pass

# Register custom provider
converter.register_provider(
    RateSource.CUSTOM,
    CustomProvider()
)
```

### Caching Configuration

```python
from currency_conversion import CacheStrategy

# Configure Redis caching
converter.configure_cache(
    strategy=CacheStrategy.REDIS,
    host="localhost",
    port=6379,
    ttl_seconds=3600
)
```

### Metrics Collection

```python
# Get conversion metrics
metrics = converter.get_metrics(
    period_start="2024-01-01",
    period_end="2024-01-31"
)

print(f"Total conversions: {metrics.total_conversions}")
print(f"Average response time: {metrics.average_response_time}ms")
```

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/currency-conversion-service.git
cd currency-conversion-service
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
pytest tests/test_conversion.py
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

## Acknowledgments

- Forex Python library
- European Central Bank exchange rates
- Open Exchange Rates API
