# GCP Cloud Billing Client

A Python client for Google Cloud Platform's Cloud Billing API with async support, robust error handling, and built-in caching.

## Features

- ✨ Async/await support
- 🔒 Secure authentication handling
- 📊 Comprehensive billing data retrieval
- 💾 Built-in response caching
- 🔄 Automatic retries with exponential backoff
- 🛡️ Type safety with Pydantic models
- 📝 Detailed logging
- 🧪 Extensive test coverage

## Installation

```bash
pip install gcp-billing-client
```

## Quick Start

```python
from gcp_billing import (
    GCPBillingClient,
    GetBillingDataRequest,
    BillingQueryDefinition,
    TimeframeType,
    QueryDataset,
    GranularityType,
    MetricConfiguration,
    CostMetricType,
)

async def get_monthly_costs():
    async with GCPBillingClient(project_id="your-project-id") as client:
        request = GetBillingDataRequest(
            billing_account="your-billing-account",
            query=BillingQueryDefinition(
                time_period=QueryTimeframe(
                    timeframe=TimeframeType.MONTH_TO_DATE,
                ),
                dataset=QueryDataset(
                    granularity=GranularityType.DAILY,
                    metrics=[
                        MetricConfiguration(
                            name=CostMetricType.COST,
                        )
                    ],
                ),
            ),
        )
        
        return await client.get_billing_data(request)
```

## Requirements

- Python 3.9+
- GCP credentials configured
- Required GCP permissions for Cloud Billing API

## Authentication

The client supports multiple authentication methods:

1. Environment variables
2. Service account JSON file
3. Application Default Credentials
4. Direct credential injection

See the [usage documentation](docs/usage.md) for detailed authentication examples.

## Key Features

### Async Support

All API operations are async, allowing for efficient concurrent operations:

```python
async with GCPBillingClient() as client:
    billing_future = client.get_billing_data(billing_request)
    pricing_future = client.get_pricing_info(pricing_request)
    
    billing_data, pricing_data = await asyncio.gather(
        billing_future,
        pricing_future
    )
```

### Built-in Caching

Automatic caching of responses to improve performance:

```python
client = GCPBillingClient(
    cache_ttl=300  # Cache responses for 5 minutes
)
```

### Retry Mechanism

Automatic retry with exponential backoff for transient failures:

```python
client = GCPBillingClient(
    max_retries=3,
    timeout=30
)
```

### Type Safety

All requests and responses are validated using Pydantic models:

```python
from gcp_billing import (
    BillingQueryDefinition,
    TimeframeType,
    QueryDataset,
    GranularityType,
    MetricConfiguration,
    CostMetricType,
)

request = GetBillingDataRequest(
    billing_account="your-billing-account",
    query=BillingQueryDefinition(
        time_period=QueryTimeframe(
            timeframe=TimeframeType.MONTH_TO_DATE,
        ),
        dataset=QueryDataset(
            granularity=GranularityType.DAILY,
            metrics=[
                MetricConfiguration(
                    name=CostMetricType.COST,
                )
            ],
        ),
    ),
)
```

## Available Operations

- Get billing data and usage
- Get pricing information
- Create and manage budgets
- Export billing data to BigQuery or Cloud Storage
- Filter costs by various dimensions
- Group results by project, service, or other attributes

## Error Handling

The client provides detailed error handling with specific exception types:

```python
from gcp_billing import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    DataNotFoundError,
    InvalidBillingAccountError,
    RateLimitError,
)

try:
    async with GCPBillingClient() as client:
        response = await client.get_billing_data(request)
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except DataNotFoundError as e:
    print(f"No data found: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## Documentation

- [Usage Guide](docs/usage.md)
- [API Reference](docs/api.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gcp-billing-client.git
   cd gcp-billing-client
   ```

2. Install development dependencies:
   ```bash
   poetry install
   ```

3. Run tests:
   ```bash
   poetry run pytest
   ```

4. Run linting:
   ```bash
   poetry run black .
   poetry run isort .
   poetry run mypy .
   poetry run pylint src tests
   ```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google Cloud Billing API Documentation
- Google Cloud Python Client Libraries Documentation
- Python Async/Await Documentation

## Support

For support, please:

1. Check the [documentation](docs/usage.md)
2. Search existing [issues](https://github.com/yourusername/gcp-billing-client/issues)
3. Create a new issue if needed

## Project Status

This project is actively maintained and follows [Semantic Versioning](https://semver.org/).

## Security

Please report security issues directly to the maintainers. See our [Security Policy](SECURITY.md) for details.
