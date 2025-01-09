# Azure Cost Management Client

A Python client for Azure Cost Management API with async support, robust error handling, and built-in caching.

## Features

- ✨ Async/await support
- 🔒 Secure authentication handling
- 📊 Comprehensive cost data retrieval
- 💾 Built-in response caching
- 🔄 Automatic retries with exponential backoff
- 🛡️ Type safety with Pydantic models
- 📝 Detailed logging
- 🧪 Extensive test coverage

## Installation

```bash
pip install azure-cost-management-client
```

## Quick Start

```python
from datetime import datetime, timedelta
from azure_cost_management import (
    AzureCostManagementClient,
    GetCostRequest,
    CostQueryDefinition,
    TimeframeType,
    QueryDataset,
    GranularityType,
    MetricConfiguration,
    MetricType,
)

async def get_monthly_costs():
    async with AzureCostManagementClient(subscription_id="your-subscription-id") as client:
        request = GetCostRequest(
            scope="/subscriptions/your-subscription-id",
            query=CostQueryDefinition(
                timeframe=TimeframeType.MONTH_TO_DATE,
                dataset=QueryDataset(
                    granularity=GranularityType.DAILY,
                    aggregation={
                        "totalCost": MetricConfiguration(
                            name=MetricType.ACTUAL_COST,
                        )
                    },
                ),
            ),
        )
        
        response = await client.get_cost_and_usage(request)
        return response
```

## Requirements

- Python 3.9+
- Azure credentials configured
- Required Azure permissions for Cost Management API

## Authentication

The client supports multiple authentication methods:

1. Environment variables
2. Azure credentials file
3. Direct credential injection
4. Managed identities

See the [usage documentation](docs/usage.md) for detailed authentication examples.

## Key Features

### Async Support

All API operations are async, allowing for efficient concurrent operations:

```python
async with AzureCostManagementClient() as client:
    cost_future = client.get_cost_and_usage(cost_request)
    forecast_future = client.get_cost_forecast(forecast_request)
    
    cost_data, forecast_data = await asyncio.gather(
        cost_future,
        forecast_future
    )
```

### Built-in Caching

Automatic caching of responses to improve performance:

```python
client = AzureCostManagementClient(
    cache_ttl=300  # Cache responses for 5 minutes
)
```

### Retry Mechanism

Automatic retry with exponential backoff for transient failures:

```python
client = AzureCostManagementClient(
    max_retries=3,
    timeout=30
)
```

### Type Safety

All requests and responses are validated using Pydantic models:

```python
from azure_cost_management import (
    CostQueryDefinition,
    TimeframeType,
    QueryDataset,
    GranularityType,
    MetricConfiguration,
    MetricType,
)

request = GetCostRequest(
    scope="/subscriptions/your-subscription-id",
    query=CostQueryDefinition(
        timeframe=TimeframeType.MONTH_TO_DATE,
        dataset=QueryDataset(
            granularity=GranularityType.DAILY,
            aggregation={
                "totalCost": MetricConfiguration(
                    name=MetricType.ACTUAL_COST,
                )
            },
        ),
    ),
)
```

## Available Operations

- Get cost and usage data
- Get cost forecasts
- Create and manage budgets
- Filter costs by various dimensions
- Group results by resource, service, or other attributes

## Error Handling

The client provides detailed error handling with specific exception types:

```python
from azure_cost_management import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    DataNotFoundError,
    InvalidScopeError,
    RateLimitError,
)

try:
    async with AzureCostManagementClient() as client:
        response = await client.get_cost_and_usage(request)
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
   git clone https://github.com/yourusername/azure-cost-management-client.git
   cd azure-cost-management-client
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

- Azure Cost Management API Documentation
- Azure SDK for Python Documentation
- Python Async/Await Documentation

## Support

For support, please:

1. Check the [documentation](docs/usage.md)
2. Search existing [issues](https://github.com/yourusername/azure-cost-management-client/issues)
3. Create a new issue if needed

## Project Status

This project is actively maintained and follows [Semantic Versioning](https://semver.org/).

## Security

Please report security issues directly to the maintainers. See our [Security Policy](SECURITY.md) for details.
