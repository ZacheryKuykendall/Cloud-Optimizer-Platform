# GCP Cloud Billing Client API Reference

This document provides detailed API reference for the GCP Cloud Billing client.

## Table of Contents

- [Client](#client)
- [Models](#models)
- [Exceptions](#exceptions)
- [Enums](#enums)

## Client

### GCPBillingClient

```python
class GCPBillingClient:
    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials: Optional[Any] = None,
        cache_ttl: int = 300,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None
```

Main client for interacting with GCP Cloud Billing API.

#### Parameters

- `project_id` (Optional[str]): GCP project ID
- `credentials` (Optional[Any]): GCP credentials object
- `cache_ttl` (int): Cache TTL in seconds (default: 300)
- `max_retries` (int): Maximum number of retries (default: 3)
- `timeout` (int): Request timeout in seconds (default: 30)

#### Methods

##### get_billing_data

```python
@retry(
    retry=retry_if_exception_type((APIError, RateLimitError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
async def get_billing_data(
    self,
    request: Union[GetBillingDataRequest, Dict[str, Any]]
) -> BillingQueryResult
```

Get billing data.

###### Parameters

- `request` (Union[GetBillingDataRequest, Dict[str, Any]]): Billing query request parameters

###### Returns

- `BillingQueryResult`: The billing query result

###### Raises

- `ValidationError`: If the request parameters are invalid
- `APIError`: If the API request fails
- `DataNotFoundError`: If no data is found

##### get_pricing_info

```python
@cached(cache=TTLCache(maxsize=100, ttl=300))
async def get_pricing_info(
    self,
    request: Union[GetPricingRequest, Dict[str, Any]]
) -> List[PricingInfo]
```

Get pricing information.

###### Parameters

- `request` (Union[GetPricingRequest, Dict[str, Any]]): Pricing request parameters

###### Returns

- `List[PricingInfo]`: List of pricing information

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

#### GetBillingDataRequest

```python
class GetBillingDataRequest(BaseModel):
    billing_account: str
    query: BillingQueryDefinition
```

Request parameters for getting billing data.

#### GetPricingRequest

```python
class GetPricingRequest(BaseModel):
    service: Optional[str] = None
    sku: Optional[str] = None
    region: Optional[str] = None
    effective_time: Optional[datetime] = None
```

Request parameters for getting pricing information.

#### CreateBudgetRequest

```python
class CreateBudgetRequest(BaseModel):
    billing_account: str
    budget: BudgetDefinition
```

Request parameters for creating a budget.

### Data Models

#### BillingQueryDefinition

```python
class BillingQueryDefinition(BaseModel):
    time_period: QueryTimeframe
    dataset: QueryDataset
```

Billing query definition.

#### QueryDataset

```python
class QueryDataset(BaseModel):
    granularity: GranularityType
    metrics: List[MetricConfiguration]
    grouping: Optional[List[QueryGrouping]] = None
    filter: Optional[QueryFilter] = None
```

Dataset configuration for billing queries.

#### BudgetDefinition

```python
class BudgetDefinition(BaseModel):
    display_name: str
    amount: BudgetAmount
    time_period: QueryTimeframe
    thresholds: Optional[Dict[str, BudgetAlertThreshold]] = None
```

Budget definition.

## Exceptions

### Base Exception

#### GCPBillingError

```python
class GCPBillingError(Exception):
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None
```

Base exception for GCP Cloud Billing client.

### API Exceptions

#### APIError

```python
class APIError(GCPBillingError):
    def __init__(
        self,
        message: str = "GCP Cloud Billing API error",
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ) -> None
```

Raised when GCP Cloud Billing API returns an error.

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

Raised when GCP Cloud Billing API rate limit is exceeded.

## Enums

### TimeframeType

```python
class TimeframeType(str, Enum):
    CUSTOM = "CUSTOM"
    MONTH_TO_DATE = "MONTH_TO_DATE"
    LAST_MONTH = "LAST_MONTH"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"
```

Time frame types for billing queries.

### GranularityType

```python
class GranularityType(str, Enum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
```

Granularity for billing data.

### CostMetricType

```python
class CostMetricType(str, Enum):
    COST = "cost"
    USAGE = "usage"
    CREDITS = "credits"
    ADJUSTMENTS = "adjustments"
```

Available cost metrics.

## Type Hints

The client uses the following type hints for improved type safety:

```python
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal

# Common type hints
BillingAccount = str
ProjectId = str
ServiceName = str
SkuId = str
Region = str
MetricName = str
GroupName = str
FilterValue = Union[str, int, float]
DateInterval = tuple[datetime, datetime]
```

For more examples and usage information, see the [Usage Guide](usage.md).
