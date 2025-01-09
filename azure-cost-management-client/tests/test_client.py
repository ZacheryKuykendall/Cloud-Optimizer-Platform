"""Tests for Azure Cost Management client."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Generator

import pytest
from azure.core.exceptions import HttpResponseError
from azure.mgmt.costmanagement.models import QueryResult

from azure_cost_management.client import AzureCostManagementClient
from azure_cost_management.exceptions import (
    APIError,
    AuthenticationError,
    BudgetError,
    ConfigurationError,
    DataNotFoundError,
    InvalidFilterError,
    InvalidScopeError,
    RateLimitError,
)
from azure_cost_management.models import (
    BudgetDefinition,
    BudgetTimeGrain,
    CostQueryDefinition,
    CreateBudgetRequest,
    GetCostRequest,
    GetForecastRequest,
    GranularityType,
    MetricConfiguration,
    MetricType,
    QueryDataset,
    QueryTimeframe,
    TimeframeType,
)


@pytest.fixture
def mock_credentials(mocker):
    """Mock Azure credentials."""
    return mocker.Mock()


@pytest.fixture
def mock_cost_management_client(mocker):
    """Mock Azure Cost Management client."""
    return mocker.Mock()


@pytest.fixture
def client(mock_credentials, mock_cost_management_client, mocker):
    """Create a test client with mocked dependencies."""
    mocker.patch(
        "azure_cost_management.client.DefaultAzureCredential",
        return_value=mock_credentials,
    )
    mocker.patch(
        "azure_cost_management.client.CostManagementClient",
        return_value=mock_cost_management_client,
    )
    return AzureCostManagementClient(subscription_id="test-subscription")


@pytest.fixture
def sample_cost_data() -> Dict[str, Any]:
    """Provide sample cost data."""
    return {
        "id": "test-id",
        "name": "test-query",
        "type": "Usage",
        "properties": {
            "columns": [
                {"name": "PreTaxCost", "type": "Number"},
                {"name": "UsageDate", "type": "DateTime"},
            ],
            "rows": [
                [10.0, "2024-01-01T00:00:00Z"],
                [15.0, "2024-01-02T00:00:00Z"],
            ],
        },
    }


@pytest.mark.asyncio
async def test_client_initialization(mock_credentials, mock_cost_management_client):
    """Test client initialization."""
    client = AzureCostManagementClient(subscription_id="test-subscription")
    assert client.credential == mock_credentials
    assert client.client == mock_cost_management_client


@pytest.mark.asyncio
async def test_client_initialization_invalid_credentials(mocker):
    """Test client initialization with invalid credentials."""
    mocker.patch(
        "azure_cost_management.client.DefaultAzureCredential",
        side_effect=Exception("AuthenticationFailed"),
    )
    with pytest.raises(AuthenticationError):
        AzureCostManagementClient(subscription_id="test-subscription")


@pytest.mark.asyncio
async def test_get_cost_and_usage(client, sample_cost_data):
    """Test getting cost and usage data."""
    client.client.query.usage.return_value = QueryResult(**sample_cost_data)

    request = GetCostRequest(
        scope="/subscriptions/test-subscription",
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
    assert response.id == "test-id"
    assert response.name == "test-query"
    assert response.type == "Usage"


@pytest.mark.asyncio
async def test_get_cost_and_usage_invalid_scope(client):
    """Test getting cost data with invalid scope."""
    client.client.query.usage.side_effect = HttpResponseError(
        message="InvalidScope",
        response=mocker.Mock(status_code=400),
    )

    request = GetCostRequest(
        scope="invalid-scope",
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

    with pytest.raises(InvalidScopeError):
        await client.get_cost_and_usage(request)


@pytest.mark.asyncio
async def test_get_cost_and_usage_rate_limit(client):
    """Test handling rate limiting."""
    client.client.query.usage.side_effect = HttpResponseError(
        message="TooManyRequests",
        response=mocker.Mock(status_code=429, headers={"Retry-After": "5"}),
    )

    request = GetCostRequest(
        scope="/subscriptions/test-subscription",
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

    with pytest.raises(RateLimitError) as exc_info:
        await client.get_cost_and_usage(request)
    assert exc_info.value.retry_after == 5


@pytest.mark.asyncio
async def test_create_budget(client):
    """Test creating a budget."""
    client.client.budgets.create_or_update.return_value = mocker.Mock(
        as_dict=lambda: {
            "id": "test-budget",
            "name": "test-budget",
            "type": "Budget",
            "amount": {"amount": 1000.0, "currency": "USD"},
            "timeGrain": "Monthly",
        }
    )

    request = CreateBudgetRequest(
        scope="/subscriptions/test-subscription",
        budget_name="test-budget",
        budget=BudgetDefinition(
            name="test-budget",
            amount=Decimal("1000.0"),
            time_grain=BudgetTimeGrain.MONTHLY,
            time_period=QueryTimeframe(
                from_date=datetime.now(),
                to_date=datetime.now() + timedelta(days=30),
            ),
        ),
    )

    response = await client.create_budget(request)
    assert response.name == "test-budget"
    assert response.amount.amount == Decimal("1000.0")


@pytest.mark.asyncio
async def test_create_budget_invalid_scope(client):
    """Test creating a budget with invalid scope."""
    client.client.budgets.create_or_update.side_effect = HttpResponseError(
        message="InvalidScope",
        response=mocker.Mock(status_code=400),
    )

    request = CreateBudgetRequest(
        scope="invalid-scope",
        budget_name="test-budget",
        budget=BudgetDefinition(
            name="test-budget",
            amount=Decimal("1000.0"),
            time_grain=BudgetTimeGrain.MONTHLY,
            time_period=QueryTimeframe(
                from_date=datetime.now(),
                to_date=datetime.now() + timedelta(days=30),
            ),
        ),
    )

    with pytest.raises(InvalidScopeError):
        await client.create_budget(request)


@pytest.mark.asyncio
async def test_client_context_manager(client):
    """Test client context manager."""
    async with client as c:
        assert c.client is not None

    # Client should be closed after context
    assert not hasattr(client, "client")


@pytest.mark.asyncio
async def test_client_caching(client, sample_cost_data):
    """Test response caching."""
    client.client.query.usage.return_value = QueryResult(**sample_cost_data)

    request = GetCostRequest(
        scope="/subscriptions/test-subscription",
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

    # First call should hit the API
    await client.get_cost_and_usage(request)
    assert client.client.query.usage.call_count == 1

    # Second call should use cache
    await client.get_cost_and_usage(request)
    assert client.client.query.usage.call_count == 1  # Count shouldn't increase


@pytest.mark.asyncio
async def test_client_retry_mechanism(client, sample_cost_data):
    """Test retry mechanism."""
    call_count = 0

    def mock_with_retries(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:  # Fail twice, succeed on third try
            raise HttpResponseError(
                message="TooManyRequests",
                response=mocker.Mock(status_code=429, headers={"Retry-After": "1"}),
            )
        return QueryResult(**sample_cost_data)

    client.client.query.usage.side_effect = mock_with_retries

    request = GetCostRequest(
        scope="/subscriptions/test-subscription",
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
    assert response.id == "test-id"
    assert call_count == 3  # Should have retried twice
