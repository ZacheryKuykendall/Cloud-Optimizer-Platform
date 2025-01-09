# Azure Cost Management Client API Reference

This document provides detailed API reference for the Azure Cost Management client.

## Table of Contents

- [Client](#client)
- [Models](#models)
- [Exceptions](#exceptions)
- [Enums](#enums)

## Client

### AzureCostManagementClient

```python
class AzureCostManagementClient:
    def __init__(
        self,
        subscription_id: Optional[str] = None,
        credential: Optional[DefaultAzureCredential] = None,
        cache_ttl: int = 300,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None
```

Main client for interacting with Azure Cost Management API.

#### Parameters

- `subscription_id` (Optional[str]): Azure subscription ID
- `credential` (Optional[DefaultAzureCredential]): Azure credential object
- `cache_ttl` (int): Cache TTL in seconds (default: 300)
- `max_retries` (int): Maximum number of retries (default: 3)
- `timeout` (int): Request timeout in seconds (default: 30)

#### Methods

##### get_cost_and_usage

```python
async def get_cost_and_usage(
    self,
    request: Union[GetCostRequest, Dict[str, Any]]
) -> CostQueryResult
```

Get cost and usage data.

###### Parameters

- `request` (Union[GetCostRequest, Dict[str, Any]]): Cost query request parameters

###### Returns

- `CostQueryResult`: The cost query result

###### Raises

- `ValidationError`: If the request parameters are invalid
- `APIError`: If the API request fails
- `DataNotFoundError`: If no data is found

##### get_cost_forecast

```python
@cached(cache=TTLCache(maxsize=100, ttl=300))
async def get_cost_forecast(
    self,
    request: Union[GetForecastRequest, Dict[str, Any]]
) -> ForecastResult
```

Get cost forecast.

###### Parameters

- `request` (Union[GetForecastRequest, Dict[str, Any]]): Forecast request parameters

###### Returns

- `ForecastResult`: The forecast result

###### Raises

- `ValidationError`: If the request parameters are invalid
- `APIError`: If the API request fails

##### create_budget

```python
async def create_budget(
    self,
    request: Union[CreateBudgetRequest, Dict[str, Any]]
) -> BudgetStatus
```

Create a budget.

###### Parameters

- `request` (Union[CreateBudgetRequest, Dict[str, Any]]): Budget creation request parameters

###### Returns

- `BudgetStatus`: The created budget status

###### Raises

- `ValidationError`: If the request parameters are invalid
- `APIError`: If the API request fails

##### update_budget

```python
async def update_budget(
    self,
    request: Union[UpdateBudgetRequest, Dict[str, Any]]
) -> BudgetStatus
```

Update a budget.

###### Parameters

- `request` (Union[UpdateBudgetRequest, Dict[str, Any]]): Budget update request parameters

###### Returns

- `BudgetStatus`: The updated budget status

###### Raises

- `ValidationError`: If the request parameters are invalid
- `APIError`: If the API request fails

##### delete_budget

```python
async def delete_budget(
    self,
    request: Union[DeleteBudgetRequest, Dict[str, Any]]
) -> None
```

Delete a budget.

###### Parameters

- `request` (Union[DeleteBudgetRequest, Dict[str, Any]]): Budget deletion request parameters

###### Raises

- `ValidationError`: If the request parameters are invalid
- `APIError`: If the API request fails

##### list_budgets

```python
async def list_budgets(
    self,
    request: Union[ListBudgetsRequest, Dict[str, Any]]
) -> List[BudgetStatus]
```

List budgets.

###### Parameters

- `request` (Union[ListBudgetsRequest, Dict[str, Any]]): Budget listing request parameters

###### Returns

- `List[BudgetStatus]`: List of budget statuses

###### Raises

- `ValidationError`: If the request parameters are invalid
- `APIError`: If the API request fails

## Models

### Request Models

#### GetCostRequest

```python
class GetCostRequest(BaseModel):
    scope: str
    query: CostQueryDefinition
```

Request parameters for getting cost data.

#### GetForecastRequest

```python
class GetForecastRequest(BaseModel):
    scope: str
    query: ForecastDefinition
```

Request parameters for getting cost forecast.

#### CreateBudgetRequest

```python
class CreateBudgetRequest(BaseModel):
    scope: str
    budget_name: str
    budget: BudgetDefinition
```

Request parameters for creating a budget.

### Data Models

#### CostQueryDefinition

```python
class CostQueryDefinition(BaseModel):
    type: str = "Usage"
    timeframe: Optional[TimeframeType] = None
    time_period: Optional[QueryTimeframe] = None
    dataset: QueryDataset
```

Cost query definition.

#### QueryDataset

```python
class QueryDataset(BaseModel):
    granularity: GranularityType
    aggregation: Dict[str, MetricConfiguration]
    grouping: Optional[List[QueryGrouping]] = None
    filter: Optional[QueryFilter] = None
```

Dataset configuration for cost queries.

#### BudgetDefinition

```python
class BudgetDefinition(BaseModel):
    name: str
    amount: Decimal
    time_grain: BudgetTimeGrain
    time_period: QueryTimeframe
    filter: Optional[BudgetFilter] = None
    notifications: Optional[Dict[str, NotificationThreshold]] = None
```

Budget definition.

## Exceptions

### Base Exception

#### AzureCostManagementError

```python
class AzureCostManagementError(Exception):
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None
```

Base exception for Azure Cost Management client.

### API Exceptions

#### APIError

```python
class APIError(AzureCostManagementError):
    def __init__(
        self,
        message: str = "Azure Cost Management API error",
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ) -> None
```

Raised when Azure Cost Management API returns an error.

#### RateLimitError

```python
class RateLimitError(APIError):
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ) -> None
```

Raised when Azure Cost Management API rate limit is exceeded.

### Validation Exceptions

#### ValidationError

```python
class ValidationError(AzureCostManagementError):
    def __init__(
        self,
        message: str = "Invalid request parameters",
        details: Optional[Dict[str, Any]] = None,
    ) -> None
```

Raised when request parameters are invalid.

## Enums

### TimeframeType

```python
class TimeframeType(str, Enum):
    CUSTOM = "Custom"
    MONTH_TO_DATE = "MonthToDate"
    BILLING_MONTH_TO_DATE = "BillingMonthToDate"
    THE_LAST_BILLING_MONTH = "TheLastBillingMonth"
    THE_LAST_MONTH = "TheLastMonth"
    WEEK_TO_DATE = "WeekToDate"
    BILLING_WEEK_TO_DATE = "BillingWeekToDate"
```

Time frame types for cost queries.

### GranularityType

```python
class GranularityType(str, Enum):
    DAILY = "Daily"
    MONTHLY = "Monthly"
    YEARLY = "Yearly"
```

Granularity for cost data.

### MetricType

```python
class MetricType(str, Enum):
    ACTUAL_COST = "ActualCost"
    AMORTIZED_COST = "AmortizedCost"
    USAGE_QUANTITY = "UsageQuantity"
    NORMALIZED_USAGE_AMOUNT = "NormalizedUsageAmount"
```

Available cost metrics.

### BudgetTimeGrain

```python
class BudgetTimeGrain(str, Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUALLY = "Annually"
```

Time grain for budgets.

## Type Hints

The client uses the following type hints for improved type safety:

```python
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal

# Common type hints
Scope = str
MetricName = str
GroupName = str
FilterValue = Union[str, int, float]
DateInterval = tuple[datetime, datetime]
```

For more examples and usage information, see the [Usage Guide](usage.md).
