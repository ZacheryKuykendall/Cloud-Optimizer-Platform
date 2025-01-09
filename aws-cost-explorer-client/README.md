# AWS Cost Explorer Client

A Python client for AWS Cost Explorer API with async support, robust error handling, and built-in caching.

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
pip install aws-cost-explorer-client
```

## Quick Start

```python
from datetime import datetime, timedelta
from aws_cost_explorer import AWSCostExplorerClient
from aws_cost_explorer.models import (
    DateInterval,
    GetCostAndUsageRequest,
    Granularity,
    MetricName,
)

async def get_monthly_costs():
    async with AWSCostExplorerClient() as client:
        request = GetCostAndUsageRequest(
            time_period=DateInterval(
                start=datetime.now() - timedelta(days=30),
                end=datetime.now()
            ),
            granularity=Granularity.DAILY,
            metrics=[MetricName.UNBLENDED_COST]
        )
        
        response = await client.get_cost_and_usage(request)
        return response

```

## Requirements

- Python 3.9+
- AWS credentials configured
- Required AWS IAM permissions for Cost Explorer API

## Authentication

The client supports multiple authentication methods:

1. Environment variables
2. AWS credentials file
3. Direct credential injection
4. IAM roles

See the [usage documentation](docs/usage.md) for detailed authentication examples.

## Key Features

### Async Support

All API operations are async, allowing for efficient concurrent operations:

```python
async with AWSCostExplorerClient() as client:
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
client = AWSCostExplorerClient(
    cache_ttl=300  # Cache responses for 5 minutes
)
```

### Retry Mechanism

Automatic retry with exponential backoff for transient failures:

```python
client = AWSCostExplorerClient(
    max_retries=3,
    timeout=30
)
```

### Type Safety

All requests and responses are validated using Pydantic models:

```python
from aws_cost_explorer.models import (
    CostFilter,
    Expression,
    GroupDefinition,
    GroupDefinitionType,
)

request = GetCostAndUsageRequest(
    time_period=DateInterval(...),
    granularity=Granularity.DAILY,
    metrics=[MetricName.UNBLENDED_COST],
    group_by=[
        GroupDefinition(
            type=GroupDefinitionType.SERVICE
        )
    ],
    filter=CostFilter(
        expressions=[
            Expression(
                dimension="SERVICE",
                values=["Amazon EC2"]
            )
        ]
    )
)
```

## Available Operations

- Get cost and usage data
- Get cost forecasts
- Get reservation utilization
- Get Savings Plans utilization
- Filter costs by various dimensions
- Group results by service, tag, or other attributes

## Error Handling

The client provides detailed error handling with specific exception types:

```python
from aws_cost_explorer.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    DataNotFoundError,
    InvalidDateRangeError,
    RateLimitError,
)

try:
    async with AWSCostExplorerClient() as client:
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
   git clone https://github.com/yourusername/aws-cost-explorer-client.git
   cd aws-cost-explorer-client
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

- AWS Cost Explorer API Documentation
- Boto3 Documentation
- Python Async/Await Documentation

## Support

For support, please:

1. Check the [documentation](docs/usage.md)
2. Search existing [issues](https://github.com/yourusername/aws-cost-explorer-client/issues)
3. Create a new issue if needed

## Project Status

This project is actively maintained and follows [Semantic Versioning](https://semver.org/).

## Security

Please report security issues directly to the maintainers. See our [Security Policy](SECURITY.md) for details.
