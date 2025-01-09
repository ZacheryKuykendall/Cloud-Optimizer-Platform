"""Tests for AWS Cost Explorer client."""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Generator

import boto3
import pytest
from moto import mock_ce, mock_sts

from aws_cost_explorer.client import AWSCostExplorerClient
from aws_cost_explorer.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    DataNotFoundError,
    InvalidDateRangeError,
    RateLimitError,
)
from aws_cost_explorer.models import (
    CostReport,
    DateInterval,
    GetCostAndUsageRequest,
    GetCostForecastRequest,
    Granularity,
    MetricName,
)


@pytest.fixture
def aws_credentials() -> Dict[str, str]:
    """Provide mock AWS credentials."""
    return {
        "aws_access_key_id": "testing",
        "aws_secret_access_key": "testing",
        "aws_session_token": "testing",
        "region_name": "us-east-1",
    }


@pytest.fixture
def mock_aws() -> Generator[None, None, None]:
    """Mock AWS services."""
    with mock_ce(), mock_sts():
        yield


@pytest.fixture
def client(aws_credentials: Dict[str, str], mock_aws: None) -> AWSCostExplorerClient:
    """Create a test client."""
    return AWSCostExplorerClient(**aws_credentials)


@pytest.fixture
def sample_cost_data() -> Dict[str, Any]:
    """Provide sample cost data."""
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {
                    "Start": "2024-01-01",
                    "End": "2024-01-02",
                },
                "Total": {
                    "UnblendedCost": {"Amount": "10.0", "Unit": "USD"},
                    "UsageQuantity": {"Amount": "24.0", "Unit": "Hours"},
                },
                "Groups": [],
                "Estimated": False,
            }
        ],
        "DimensionValueAttributes": [],
        "NextPageToken": None,
    }


@pytest.mark.asyncio
async def test_client_initialization(aws_credentials: Dict[str, str], mock_aws: None) -> None:
    """Test client initialization."""
    client = AWSCostExplorerClient(**aws_credentials)
    assert client.session is not None
    assert client.client is not None


@pytest.mark.asyncio
async def test_client_initialization_invalid_credentials(mock_aws: None) -> None:
    """Test client initialization with invalid credentials."""
    with pytest.raises(ConfigurationError):
        AWSCostExplorerClient(
            aws_access_key_id="invalid",
            aws_secret_access_key="invalid",
            region_name="us-east-1",
        )


@pytest.mark.asyncio
async def test_client_initialization_invalid_region(aws_credentials: Dict[str, str], mock_aws: None) -> None:
    """Test client initialization with invalid region."""
    aws_credentials["region_name"] = "invalid-region"
    with pytest.raises(ConfigurationError):
        AWSCostExplorerClient(**aws_credentials)


@pytest.mark.asyncio
async def test_get_cost_and_usage(
    client: AWSCostExplorerClient, sample_cost_data: Dict[str, Any]
) -> None:
    """Test getting cost and usage data."""
    # Mock the AWS response
    client.client.get_cost_and_usage = lambda **kwargs: sample_cost_data

    request = GetCostAndUsageRequest(
        time_period=DateInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 2),
        ),
        granularity=Granularity.DAILY,
        metrics=[MetricName.UNBLENDED_COST, MetricName.USAGE_QUANTITY],
    )

    response = await client.get_cost_and_usage(request)
    assert isinstance(response, CostReport)
    assert len(response.results_by_time) == 1
    assert response.next_page_token is None


@pytest.mark.asyncio
async def test_get_cost_and_usage_invalid_dates(client: AWSCostExplorerClient) -> None:
    """Test getting cost data with invalid dates."""
    request = GetCostAndUsageRequest(
        time_period=DateInterval(
            start=datetime(2024, 1, 2),  # End before start
            end=datetime(2024, 1, 1),
        ),
        granularity=Granularity.DAILY,
        metrics=[MetricName.UNBLENDED_COST],
    )

    with pytest.raises(InvalidDateRangeError):
        await client.get_cost_and_usage(request)


@pytest.mark.asyncio
async def test_get_cost_and_usage_rate_limit(
    client: AWSCostExplorerClient, mock_aws: None
) -> None:
    """Test handling rate limiting."""
    def mock_rate_limit(**kwargs):
        raise client.client.exceptions.RateExceededException({
            "Error": {
                "Code": "RateExceededException",
                "Message": "Rate limit exceeded",
            },
            "ResponseMetadata": {"RetryAfter": 5},
        }, "GetCostAndUsage")

    client.client.get_cost_and_usage = mock_rate_limit

    request = GetCostAndUsageRequest(
        time_period=DateInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 2),
        ),
        granularity=Granularity.DAILY,
        metrics=[MetricName.UNBLENDED_COST],
    )

    with pytest.raises(RateLimitError) as exc_info:
        await client.get_cost_and_usage(request)
    assert exc_info.value.retry_after == 5


@pytest.mark.asyncio
async def test_get_cost_and_usage_no_data(
    client: AWSCostExplorerClient, mock_aws: None
) -> None:
    """Test handling no data found."""
    def mock_no_data(**kwargs):
        raise client.client.exceptions.DataUnavailableException({
            "Error": {
                "Code": "DataUnavailableException",
                "Message": "No data available",
            },
            "ResponseMetadata": {},
        }, "GetCostAndUsage")

    client.client.get_cost_and_usage = mock_no_data

    request = GetCostAndUsageRequest(
        time_period=DateInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 2),
        ),
        granularity=Granularity.DAILY,
        metrics=[MetricName.UNBLENDED_COST],
    )

    with pytest.raises(DataNotFoundError):
        await client.get_cost_and_usage(request)


@pytest.mark.asyncio
async def test_get_cost_forecast(client: AWSCostExplorerClient) -> None:
    """Test getting cost forecast."""
    forecast_data = {
        "Total": {
            "Amount": "100.0",
            "Unit": "USD",
        },
        "ForecastResultsByTime": [
            {
                "TimePeriod": {
                    "Start": "2024-01-01",
                    "End": "2024-02-01",
                },
                "MeanValue": "100.0",
                "PredictionIntervalLowerBound": "90.0",
                "PredictionIntervalUpperBound": "110.0",
            }
        ],
    }

    client.client.get_cost_forecast = lambda **kwargs: forecast_data

    request = GetCostForecastRequest(
        time_period=DateInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 2, 1),
        ),
        granularity=Granularity.MONTHLY,
        metric=MetricName.UNBLENDED_COST,
        prediction_interval_level=95,
    )

    response = await client.get_cost_forecast(request)
    assert isinstance(response, dict)
    assert "Total" in response
    assert "ForecastResultsByTime" in response


@pytest.mark.asyncio
async def test_client_context_manager(aws_credentials: Dict[str, str], mock_aws: None) -> None:
    """Test client context manager."""
    async with AWSCostExplorerClient(**aws_credentials) as client:
        assert client.session is not None
        assert client.client is not None

    # Client should be closed after context
    assert not hasattr(client, "client")


@pytest.mark.asyncio
async def test_client_caching(
    client: AWSCostExplorerClient, sample_cost_data: Dict[str, Any]
) -> None:
    """Test response caching."""
    call_count = 0

    def mock_get_cost_and_usage(**kwargs):
        nonlocal call_count
        call_count += 1
        return sample_cost_data

    client.client.get_cost_and_usage = mock_get_cost_and_usage

    request = GetCostAndUsageRequest(
        time_period=DateInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 2),
        ),
        granularity=Granularity.DAILY,
        metrics=[MetricName.UNBLENDED_COST],
    )

    # First call should hit the API
    await client.get_cost_and_usage(request)
    assert call_count == 1

    # Second call should use cache
    await client.get_cost_and_usage(request)
    assert call_count == 1  # Count shouldn't increase


@pytest.mark.asyncio
async def test_client_retry_mechanism(
    client: AWSCostExplorerClient, sample_cost_data: Dict[str, Any]
) -> None:
    """Test retry mechanism."""
    call_count = 0

    def mock_with_retries(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:  # Fail twice, succeed on third try
            raise client.client.exceptions.ThrottlingException({
                "Error": {
                    "Code": "ThrottlingException",
                    "Message": "Rate limit exceeded",
                },
                "ResponseMetadata": {},
            }, "GetCostAndUsage")
        return sample_cost_data

    client.client.get_cost_and_usage = mock_with_retries

    request = GetCostAndUsageRequest(
        time_period=DateInterval(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 2),
        ),
        granularity=Granularity.DAILY,
        metrics=[MetricName.UNBLENDED_COST],
    )

    response = await client.get_cost_and_usage(request)
    assert isinstance(response, CostReport)
    assert call_count == 3  # Should have retried twice
