"""Tests for GCP Cloud Billing client."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Generator

import pytest
from google.api_core import exceptions as google_exceptions
from google.cloud.billing import CloudBillingClient
from google.cloud.billing_budgets import BudgetServiceClient

from gcp_billing.client import GCPBillingClient
from gcp_billing.exceptions import (
    APIError,
    AuthenticationError,
    BudgetError,
    ConfigurationError,
    DataNotFoundError,
    InvalidBillingAccountError,
    InvalidFilterError,
    RateLimitError,
)
from gcp_billing.models import (
    BillingQueryDefinition,
    BudgetAmount,
    BudgetDefinition,
    CreateBudgetRequest,
    GetBillingDataRequest,
    GetPricingRequest,
    GranularityType,
    MetricConfiguration,
    CostMetricType,
    QueryDataset,
    QueryTimeframe,
    TimeframeType,
)


@pytest.fixture
def mock_credentials(mocker):
    """Mock GCP credentials."""
    return mocker.Mock()


@pytest.fixture
def mock_billing_client(mocker):
    """Mock GCP Cloud Billing client."""
    return mocker.Mock(spec=CloudBillingClient)


@pytest.fixture
def mock_budgets_client(mocker):
    """Mock GCP Cloud Billing Budgets client."""
    return mocker.Mock(spec=BudgetServiceClient)


@pytest.fixture
def client(mock_credentials, mock_billing_client, mock_budgets_client, mocker):
    """Create a test client with mocked dependencies."""
    mocker.patch(
        "gcp_billing.client.CloudBillingClient",
        return_value=mock_billing_client,
    )
    mocker.patch(
        "gcp_billing.client.BudgetServiceClient",
        return_value=mock_budgets_client,
    )
    return GCPBillingClient(project_id="test-project", credentials=mock_credentials)


@pytest.fixture
def sample_billing_data() -> Dict[str, Any]:
    """Provide sample billing data."""
    return {
        "billing_account_id": "test-account",
        "cost_amount": {"currency_code": "USD", "units": "10", "nanos": 500000000},
        "usage_start_time": "2024-01-01T00:00:00Z",
        "usage_end_time": "2024-01-02T00:00:00Z",
        "project": {"id": "test-project", "name": "Test Project"},
        "service": {"id": "compute-engine", "name": "Compute Engine"},
    }


@pytest.mark.asyncio
async def test_client_initialization(mock_credentials, mock_billing_client, mock_budgets_client):
    """Test client initialization."""
    client = GCPBillingClient(project_id="test-project", credentials=mock_credentials)
    assert client.billing_client == mock_billing_client
    assert client.budgets_client == mock_budgets_client
    assert client.project_id == "test-project"


@pytest.mark.asyncio
async def test_client_initialization_invalid_credentials(mocker):
    """Test client initialization with invalid credentials."""
    mocker.patch(
        "gcp_billing.client.CloudBillingClient",
        side_effect=Exception("unauthorized"),
    )
    with pytest.raises(AuthenticationError):
        GCPBillingClient(project_id="test-project")


@pytest.mark.asyncio
async def test_get_billing_data(client, sample_billing_data):
    """Test getting billing data."""
    client.billing_client.get_billing_account_usage.return_value = sample_billing_data

    request = GetBillingDataRequest(
        billing_account="test-account",
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

    response = await client.get_billing_data(request)
    assert response.billing_account_id == "test-account"
    assert response.cost_amount["currency_code"] == "USD"


@pytest.mark.asyncio
async def test_get_billing_data_invalid_account(client):
    """Test getting billing data with invalid account."""
    client.billing_client.get_billing_account_usage.side_effect = google_exceptions.NotFound(
        "Billing account not found"
    )

    request = GetBillingDataRequest(
        billing_account="invalid-account",
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

    with pytest.raises(DataNotFoundError):
        await client.get_billing_data(request)


@pytest.mark.asyncio
async def test_get_billing_data_rate_limit(client):
    """Test handling rate limiting."""
    client.billing_client.get_billing_account_usage.side_effect = google_exceptions.ResourceExhausted(
        "Resource has been exhausted"
    )

    request = GetBillingDataRequest(
        billing_account="test-account",
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

    with pytest.raises(RateLimitError):
        await client.get_billing_data(request)


@pytest.mark.asyncio
async def test_create_budget(client):
    """Test creating a budget."""
    client.budgets_client.create_budget.return_value = {
        "name": "test-budget",
        "display_name": "Test Budget",
        "amount": {"currency_code": "USD", "units": "1000"},
        "threshold_rules": [{"threshold_percent": 0.8}],
    }

    request = CreateBudgetRequest(
        billing_account="test-account",
        budget=BudgetDefinition(
            display_name="Test Budget",
            amount=BudgetAmount(
                amount=Decimal("1000.0"),
                currency="USD",
            ),
            time_period=QueryTimeframe(
                timeframe=TimeframeType.MONTH_TO_DATE,
            ),
        ),
    )

    response = await client.create_budget(request)
    assert response.name == "test-budget"
    assert response.display_name == "Test Budget"


@pytest.mark.asyncio
async def test_create_budget_invalid_account(client):
    """Test creating a budget with invalid account."""
    client.budgets_client.create_budget.side_effect = google_exceptions.InvalidArgument(
        "Invalid billing account"
    )

    request = CreateBudgetRequest(
        billing_account="invalid-account",
        budget=BudgetDefinition(
            display_name="Test Budget",
            amount=BudgetAmount(
                amount=Decimal("1000.0"),
                currency="USD",
            ),
            time_period=QueryTimeframe(
                timeframe=TimeframeType.MONTH_TO_DATE,
            ),
        ),
    )

    with pytest.raises(InvalidBillingAccountError):
        await client.create_budget(request)


@pytest.mark.asyncio
async def test_client_context_manager(client):
    """Test client context manager."""
    async with client as c:
        assert c.billing_client is not None
        assert c.budgets_client is not None

    # Client should be closed after context
    assert not hasattr(client, "billing_client")
    assert not hasattr(client, "budgets_client")


@pytest.mark.asyncio
async def test_client_caching(client, sample_billing_data):
    """Test response caching."""
    client.billing_client.get_billing_account_usage.return_value = sample_billing_data

    request = GetBillingDataRequest(
        billing_account="test-account",
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

    # First call should hit the API
    await client.get_billing_data(request)
    assert client.billing_client.get_billing_account_usage.call_count == 1

    # Second call should use cache
    await client.get_billing_data(request)
    assert client.billing_client.get_billing_account_usage.call_count == 1  # Count shouldn't increase


@pytest.mark.asyncio
async def test_client_retry_mechanism(client, sample_billing_data):
    """Test retry mechanism."""
    call_count = 0

    def mock_with_retries(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:  # Fail twice, succeed on third try
            raise google_exceptions.ResourceExhausted("Resource has been exhausted")
        return sample_billing_data

    client.billing_client.get_billing_account_usage.side_effect = mock_with_retries

    request = GetBillingDataRequest(
        billing_account="test-account",
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

    response = await client.get_billing_data(request)
    assert response.billing_account_id == "test-account"
    assert call_count == 3  # Should have retried twice
