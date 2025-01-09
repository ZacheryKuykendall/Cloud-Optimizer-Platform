# GCP Cloud Billing Client Usage Guide

This guide provides detailed examples and best practices for using the GCP Cloud Billing client.

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
pip install gcp-billing-client
```

Or using Poetry:

```bash
poetry add gcp-billing-client
```

## Authentication

### Service Account

The recommended way to authenticate is using a service account:

```python
from google.oauth2 import service_account
from gcp_billing import GCPBillingClient

credentials = service_account.Credentials.from_service_account_file(
    "path/to/service-account.json",
    scopes=["https://www.googleapis.com/auth/cloud-billing"]
)

async with GCPBillingClient(credentials=credentials) as client:
    response = await client.get_billing_data(request)
```

### Application Default Credentials

You can also use Application Default Credentials:

```python
from gcp_billing import GCPBillingClient

# Will use ADC from environment
async with GCPBillingClient() as client:
    response = await client.get_billing_data(request)
```

### Environment Variables

Set up environment variables:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

```python
from gcp_billing import GCPBillingClient

async with GCPBillingClient() as client:
    # Client will use environment variables automatically
    response = await client.get_billing_data(request)
```

### Direct Credential Injection

For more control, inject credentials directly:

```python
from google.oauth2.credentials import Credentials
from gcp_billing import GCPBillingClient

credentials = Credentials(
    token="your-oauth2-token",
    refresh_token="your-refresh-token",
    client_id="your-client-id",
    client_secret="your-client-secret",
    token_uri="https://oauth2.googleapis.com/token",
)

async with GCPBillingClient(credentials=credentials) as client:
    response = await client.get_billing_data(request)
```

## Basic Usage

### Get Billing Data

```python
from gcp_billing import (
    GetBillingDataRequest,
    BillingQueryDefinition,
    TimeframeType,
    QueryDataset,
    GranularityType,
    MetricConfiguration,
    CostMetricType,
)

async def get_monthly_costs():
    async with GCPBillingClient() as client:
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

### Get Pricing Information

```python
from gcp_billing import GetPricingRequest

async def get_compute_pricing():
    async with GCPBillingClient() as client:
        request = GetPricingRequest(
            service="Compute Engine",
            region="us-central1"
        )
        
        return await client.get_pricing_info(request)
```

### Create Budget

```python
from gcp_billing import (
    CreateBudgetRequest,
    BudgetDefinition,
    BudgetAmount,
    BudgetAlertThreshold,
)

async def create_monthly_budget():
    async with GCPBillingClient() as client:
        request = CreateBudgetRequest(
            billing_account="your-billing-account",
            budget=BudgetDefinition(
                display_name="Monthly Budget",
                amount=BudgetAmount(
                    amount=Decimal("1000.0"),
                    currency="USD",
                ),
                time_period=QueryTimeframe(
                    timeframe=TimeframeType.MONTH_TO_DATE,
                ),
                thresholds={
                    "80percent": BudgetAlertThreshold(
                        threshold_type="PERCENTAGE",
                        threshold=Decimal("80.0"),
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
from gcp_billing import GCPBillingClient

async def get_cost_data():
    async with GCPBillingClient() as client:
        billing_future = client.get_billing_data(billing_request)
        pricing_future = client.get_pricing_info(pricing_request)
        budget_future = client.list_budgets(budget_request)
        
        billing_data, pricing_data, budgets = await asyncio.gather(
            billing_future,
            pricing_future,
            budget_future
        )
        
        return billing_data, pricing_data, budgets
```

### Custom Caching

```python
from gcp_billing import GCPBillingClient

client = GCPBillingClient(
    cache_ttl=600,  # Cache for 10 minutes
)
```

### Retry Configuration

```python
from gcp_billing import GCPBillingClient

client = GCPBillingClient(
    max_retries=5,
    timeout=60,
)
```

## Error Handling

```python
from gcp_billing import (
    APIError,
    AuthenticationError,
    RateLimitError,
    DataNotFoundError,
    InvalidBillingAccountError,
)

async def handle_billing_data():
    try:
        async with GCPBillingClient() as client:
            response = await client.get_billing_data(request)
            
    except RateLimitError as e:
        print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
        # Implement backoff logic
        
    except DataNotFoundError:
        print("No billing data available for the specified period")
        
    except InvalidBillingAccountError:
        print("Invalid billing account. Check your credentials")
        
    except APIError as e:
        print(f"API error: {e.message}")
        if e.details:
            print(f"Details: {e.details}")
```

## Best Practices

1. Always use async context managers:
   ```python
   async with GCPBillingClient() as client:
       # Work with client
   ```

2. Implement proper error handling:
   ```python
   try:
       async with GCPBillingClient() as client:
           response = await client.get_billing_data(request)
   except Exception as e:
       logger.error(f"Error getting billing data: {e}")
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
   client = GCPBillingClient(cache_ttl=300)
   ```

## Common Scenarios

### Monthly Cost Analysis

```python
async def analyze_monthly_costs():
    async with GCPBillingClient() as client:
        # Get current month costs
        current_costs = await client.get_billing_data(
            GetBillingDataRequest(
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
        )
        
        return current_costs
```

### Project Cost Tracking

```python
async def track_project_costs(project_id: str):
    async with GCPBillingClient() as client:
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
                    filter=QueryFilter(
                        type=FilterType.PROJECT,
                        name="project_id",
                        values=[project_id],
                    ),
                ),
            ),
        )
        
        return await client.get_billing_data(request)
```

### Budget Management

```python
async def manage_budgets():
    async with GCPBillingClient() as client:
        # List existing budgets
        budgets = await client.list_budgets(
            ListBudgetsRequest(
                billing_account="your-billing-account"
            )
        )
        
        # Create new budget if none exists
        if not budgets:
            await client.create_budget(
                CreateBudgetRequest(
                    billing_account="your-billing-account",
                    budget=BudgetDefinition(
                        display_name="Default Budget",
                        amount=BudgetAmount(
                            amount=Decimal("1000.0"),
                            currency="USD",
                        ),
                        time_period=QueryTimeframe(
                            timeframe=TimeframeType.MONTH_TO_DATE,
                        ),
                    ),
                )
            )
```

For more examples and detailed API documentation, see the [API Reference](api.md).
