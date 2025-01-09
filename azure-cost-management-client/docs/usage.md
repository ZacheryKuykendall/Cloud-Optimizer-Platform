# Azure Cost Management Client Usage Guide

This guide provides detailed examples and best practices for using the Azure Cost Management client.

## Table of Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Common Scenarios](#common-scenarios)

## Installation

Install the package using pip:

```bash
pip install azure-cost-management-client
```

Or using Poetry:

```bash
poetry add azure-cost-management-client
```

## Authentication

### Environment Variables

The simplest way to authenticate is using environment variables:

```bash
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

```python
from azure_cost_management import AzureCostManagementClient

async with AzureCostManagementClient() as client:
    # Client will use environment variables automatically
    response = await client.get_cost_and_usage(request)
```

### Azure Credentials File

You can also use an Azure credentials file:

```ini
# ~/.azure/credentials
[default]
subscription_id=your-subscription-id
tenant_id=your-tenant-id
client_id=your-client-id
client_secret=your-client-secret
```

```python
from azure.identity import AzureCliCredential
from azure_cost_management import AzureCostManagementClient

credential = AzureCliCredential()
async with AzureCostManagementClient(credential=credential) as client:
    response = await client.get_cost_and_usage(request)
```

### Direct Credential Injection

For more control, inject credentials directly:

```python
from azure.identity import ClientSecretCredential
from azure_cost_management import AzureCostManagementClient

credential = ClientSecretCredential(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

async with AzureCostManagementClient(
    subscription_id="your-subscription-id",
    credential=credential
) as client:
    response = await client.get_cost_and_usage(request)
```

### Managed Identity

When running in Azure, use managed identity:

```python
from azure.identity import ManagedIdentityCredential
from azure_cost_management import AzureCostManagementClient

credential = ManagedIdentityCredential()
async with AzureCostManagementClient(credential=credential) as client:
    response = await client.get_cost_and_usage(request)
```

## Basic Usage

### Get Cost and Usage Data

```python
from azure_cost_management import (
    GetCostRequest,
    CostQueryDefinition,
    TimeframeType,
    QueryDataset,
    GranularityType,
    MetricConfiguration,
    MetricType,
)

async def get_monthly_costs():
    async with AzureCostManagementClient() as client:
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
        
        return await client.get_cost_and_usage(request)
```

### Get Cost Forecast

```python
from azure_cost_management import (
    GetForecastRequest,
    ForecastDefinition,
)

async def get_cost_forecast():
    async with AzureCostManagementClient() as client:
        request = GetForecastRequest(
            scope="/subscriptions/your-subscription-id",
            query=ForecastDefinition(
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
        
        return await client.get_cost_forecast(request)
```

### Create Budget

```python
from azure_cost_management import (
    CreateBudgetRequest,
    BudgetDefinition,
    BudgetTimeGrain,
)

async def create_monthly_budget():
    async with AzureCostManagementClient() as client:
        request = CreateBudgetRequest(
            scope="/subscriptions/your-subscription-id",
            budget_name="monthly-budget",
            budget=BudgetDefinition(
                name="monthly-budget",
                amount=Decimal("1000.0"),
                time_grain=BudgetTimeGrain.MONTHLY,
                time_period=QueryTimeframe(
                    from_date=datetime.now(),
                    to_date=datetime.now() + timedelta(days=30),
                ),
                notifications={
                    "80percent": NotificationThreshold(
                        threshold_type="Actual",
                        threshold=Decimal("80.0"),
                        operator="GreaterThan",
                        notification_enabled=True,
                        emails=["admin@example.com"],
                    )
                },
            ),
        )
        
        return await client.create_budget(request)
```

## Advanced Features

### Concurrent Operations

```python
import asyncio
from azure_cost_management import AzureCostManagementClient

async def get_cost_data():
    async with AzureCostManagementClient() as client:
        cost_future = client.get_cost_and_usage(cost_request)
        forecast_future = client.get_cost_forecast(forecast_request)
        budget_future = client.list_budgets(budget_request)
        
        cost_data, forecast_data, budgets = await asyncio.gather(
            cost_future,
            forecast_future,
            budget_future
        )
        
        return cost_data, forecast_data, budgets
```

### Custom Caching

```python
from azure_cost_management import AzureCostManagementClient

client = AzureCostManagementClient(
    cache_ttl=600,  # Cache for 10 minutes
)
```

### Retry Configuration

```python
from azure_cost_management import AzureCostManagementClient

client = AzureCostManagementClient(
    max_retries=5,
    timeout=60,
)
```

## Error Handling

```python
from azure_cost_management import (
    APIError,
    AuthenticationError,
    RateLimitError,
    DataNotFoundError,
)

async def handle_cost_data():
    try:
        async with AzureCostManagementClient() as client:
            response = await client.get_cost_and_usage(request)
            
    except RateLimitError as e:
        print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
        # Implement backoff logic
        
    except DataNotFoundError:
        print("No cost data available for the specified period")
        
    except AuthenticationError:
        print("Authentication failed. Check your credentials")
        
    except APIError as e:
        print(f"API error: {e.message}")
        if e.details:
            print(f"Details: {e.details}")
```

## Best Practices

1. Always use async context managers:
   ```python
   async with AzureCostManagementClient() as client:
       # Work with client
   ```

2. Implement proper error handling:
   ```python
   try:
       async with AzureCostManagementClient() as client:
           response = await client.get_cost_and_usage(request)
   except Exception as e:
       logger.error(f"Error getting cost data: {e}")
       raise
   ```

3. Use appropriate timeframes:
   ```python
   # For recent data
   timeframe=TimeframeType.MONTH_TO_DATE
   
   # For historical analysis
   timeframe=TimeframeType.CUSTOM
   time_period=QueryTimeframe(
       from_date=datetime(2024, 1, 1),
       to_date=datetime(2024, 1, 31),
   )
   ```

4. Implement caching for frequently accessed data:
   ```python
   client = AzureCostManagementClient(cache_ttl=300)
   ```

## Common Scenarios

### Monthly Cost Analysis

```python
async def analyze_monthly_costs():
    async with AzureCostManagementClient() as client:
        # Get current month costs
        current_costs = await client.get_cost_and_usage(
            GetCostRequest(
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
        )
        
        # Get forecast
        forecast = await client.get_cost_forecast(
            GetForecastRequest(
                scope="/subscriptions/your-subscription-id",
                query=ForecastDefinition(
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
        )
        
        return current_costs, forecast
```

### Resource Group Cost Tracking

```python
async def track_resource_group_costs(resource_group: str):
    async with AzureCostManagementClient() as client:
        request = GetCostRequest(
            scope=f"/subscriptions/your-subscription-id/resourceGroups/{resource_group}",
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
        
        return await client.get_cost_and_usage(request)
```

### Budget Management

```python
async def manage_budgets():
    async with AzureCostManagementClient() as client:
        # List existing budgets
        budgets = await client.list_budgets(
            ListBudgetsRequest(
                scope="/subscriptions/your-subscription-id"
            )
        )
        
        # Create new budget if none exists
        if not budgets:
            await client.create_budget(
                CreateBudgetRequest(
                    scope="/subscriptions/your-subscription-id",
                    budget_name="default-budget",
                    budget=BudgetDefinition(
                        name="default-budget",
                        amount=Decimal("1000.0"),
                        time_grain=BudgetTimeGrain.MONTHLY,
                        time_period=QueryTimeframe(
                            from_date=datetime.now(),
                            to_date=datetime.now() + timedelta(days=365),
                        ),
                    ),
                )
            )
```

For more examples and detailed API documentation, see the [API Reference](api.md).
