# AWS Cost Explorer Client Usage Guide

This guide demonstrates how to use the AWS Cost Explorer client to retrieve and analyze AWS cost data.

## Installation

Install the package using pip:

```bash
pip install aws-cost-explorer-client
```

## Authentication

The client supports multiple authentication methods:

### 1. Environment Variables

```python
import os

os.environ["AWS_ACCESS_KEY_ID"] = "your-access-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret-key"
os.environ["AWS_REGION"] = "us-east-1"

from aws_cost_explorer import AWSCostExplorerClient

client = AWSCostExplorerClient()
```

### 2. Direct Credentials

```python
from aws_cost_explorer import AWSCostExplorerClient

client = AWSCostExplorerClient(
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    region_name="us-east-1"
)
```

### 3. AWS Profile

```python
from aws_cost_explorer import AWSCostExplorerClient

client = AWSCostExplorerClient(profile_name="default")
```

## Basic Usage

### Get Cost and Usage Data

```python
from datetime import datetime, timedelta
from aws_cost_explorer.models import (
    DateInterval,
    GetCostAndUsageRequest,
    Granularity,
    MetricName,
)

async def get_monthly_costs():
    # Create a client
    async with AWSCostExplorerClient() as client:
        # Define time period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Create request
        request = GetCostAndUsageRequest(
            time_period=DateInterval(
                start=start_date,
                end=end_date
            ),
            granularity=Granularity.DAILY,
            metrics=[
                MetricName.UNBLENDED_COST,
                MetricName.USAGE_QUANTITY
            ]
        )
        
        # Get cost data
        response = await client.get_cost_and_usage(request)
        
        # Process results
        for result in response.results_by_time:
            print(f"Date: {result.timestamp}")
            for group in result.groups:
                print(f"  Cost: {group.metrics.unblended_cost.amount} {group.metrics.unblended_cost.unit}")
```

### Get Cost Forecast

```python
from aws_cost_explorer.models import GetCostForecastRequest

async def get_cost_forecast():
    async with AWSCostExplorerClient() as client:
        # Define forecast period
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        request = GetCostForecastRequest(
            time_period=DateInterval(
                start=start_date,
                end=end_date
            ),
            granularity=Granularity.MONTHLY,
            metric=MetricName.UNBLENDED_COST,
            prediction_interval_level=95
        )
        
        forecast = await client.get_cost_forecast(request)
        print(f"Forecasted cost: {forecast['Total']['Amount']} {forecast['Total']['Unit']}")
```

### Get Reservation Utilization

```python
from aws_cost_explorer.models import GetReservationUtilizationRequest

async def get_reservation_usage():
    async with AWSCostExplorerClient() as client:
        request = GetReservationUtilizationRequest(
            time_period=DateInterval(
                start=datetime.now() - timedelta(days=30),
                end=datetime.now()
            ),
            granularity=Granularity.MONTHLY
        )
        
        utilization = await client.get_reservation_utilization(request)
        print(f"Reservation utilization: {utilization}")
```

### Get Savings Plans Utilization

```python
from aws_cost_explorer.models import GetSavingsPlansUtilizationRequest

async def get_savings_plans_usage():
    async with AWSCostExplorerClient() as client:
        request = GetSavingsPlansUtilizationRequest(
            time_period=DateInterval(
                start=datetime.now() - timedelta(days=30),
                end=datetime.now()
            ),
            granularity=Granularity.MONTHLY
        )
        
        utilization = await client.get_savings_plans_utilization(request)
        print(f"Savings Plans utilization: {utilization}")
```

## Advanced Usage

### Filtering Costs

```python
from aws_cost_explorer.models import CostFilter, Expression

async def get_filtered_costs():
    async with AWSCostExplorerClient() as client:
        request = GetCostAndUsageRequest(
            time_period=DateInterval(
                start=datetime.now() - timedelta(days=30),
                end=datetime.now()
            ),
            granularity=Granularity.DAILY,
            metrics=[MetricName.UNBLENDED_COST],
            filter=CostFilter(
                expressions=[
                    Expression(
                        dimension="SERVICE",
                        values=["Amazon EC2", "Amazon RDS"]
                    ),
                    Expression(
                        dimension="TAG",
                        key="Environment",
                        values=["Production"]
                    )
                ]
            )
        )
        
        response = await client.get_cost_and_usage(request)
```

### Grouping Results

```python
from aws_cost_explorer.models import GroupDefinition, GroupDefinitionType

async def get_grouped_costs():
    async with AWSCostExplorerClient() as client:
        request = GetCostAndUsageRequest(
            time_period=DateInterval(
                start=datetime.now() - timedelta(days=30),
                end=datetime.now()
            ),
            granularity=Granularity.MONTHLY,
            metrics=[MetricName.UNBLENDED_COST],
            group_by=[
                GroupDefinition(
                    type=GroupDefinitionType.SERVICE
                ),
                GroupDefinition(
                    type=GroupDefinitionType.TAGS,
                    key="Environment"
                )
            ]
        )
        
        response = await client.get_cost_and_usage(request)
```

## Error Handling

```python
from aws_cost_explorer.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    DataNotFoundError,
    InvalidDateRangeError,
    RateLimitError,
)

async def handle_errors():
    try:
        async with AWSCostExplorerClient() as client:
            request = GetCostAndUsageRequest(...)
            response = await client.get_cost_and_usage(request)
            
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
        
    except RateLimitError as e:
        print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
        
    except DataNotFoundError as e:
        print(f"No data found: {e}")
        
    except InvalidDateRangeError as e:
        print(f"Invalid date range: {e}")
        
    except APIError as e:
        print(f"API error: {e}")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
```

## Performance Optimization

### Caching

The client includes built-in caching to improve performance:

```python
from aws_cost_explorer import AWSCostExplorerClient

client = AWSCostExplorerClient(
    cache_ttl=300  # Cache responses for 5 minutes
)
```

### Retry Mechanism

The client automatically retries failed requests:

```python
client = AWSCostExplorerClient(
    max_retries=3,  # Maximum number of retry attempts
    timeout=30      # Request timeout in seconds
)
```

## Best Practices

1. Always use the client as an async context manager to ensure proper cleanup:
   ```python
   async with AWSCostExplorerClient() as client:
       # Your code here
   ```

2. Use appropriate granularity for your needs:
   - HOURLY: For detailed analysis of specific days
   - DAILY: For month-to-date analysis
   - MONTHLY: For year-over-year comparisons

3. Include specific metrics to reduce response size:
   ```python
   metrics=[MetricName.UNBLENDED_COST]  # Instead of all metrics
   ```

4. Use filters to narrow down results:
   ```python
   filter=CostFilter(
       expressions=[
           Expression(
               dimension="SERVICE",
               values=["Amazon EC2"]
           )
       ]
   )
   ```

5. Handle rate limits appropriately:
   ```python
   except RateLimitError as e:
       await asyncio.sleep(e.retry_after)
       # Retry request
   ```

## Common Issues and Solutions

1. **Authentication Failures**
   - Verify credentials are correct
   - Check IAM permissions
   - Ensure region is properly set

2. **Rate Limiting**
   - Implement exponential backoff
   - Use caching when possible
   - Batch requests when feasible

3. **Missing Data**
   - Verify date ranges are correct
   - Check if data exists in the account
   - Ensure proper IAM permissions

4. **Performance Issues**
   - Use appropriate granularity
   - Limit date ranges when possible
   - Implement caching
   - Use specific metrics instead of all

## Support

For issues and feature requests, please visit our [GitHub repository](https://github.com/yourusername/aws-cost-explorer-client).
