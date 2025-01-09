"""AWS Cost Explorer API client implementation."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from cachetools import TTLCache, cached
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    CredentialsError,
    DataNotFoundError,
    InvalidDateRangeError,
    RateLimitError,
    RegionError,
    RetryError,
    ServiceQuotaExceededError,
    SessionError,
)
from .models import (
    CostFilter,
    CostReport,
    DateInterval,
    GetCostAndUsageRequest,
    GetCostForecastRequest,
    GetReservationUtilizationRequest,
    GetSavingsPlansUtilizationRequest,
    Granularity,
    GroupDefinition,
    MetricName,
)

logger = logging.getLogger(__name__)


class AWSCostExplorerClient:
    """Client for interacting with AWS Cost Explorer API."""

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        region_name: Optional[str] = None,
        profile_name: Optional[str] = None,
        session: Optional[boto3.Session] = None,
        cache_ttl: int = 300,  # 5 minutes
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        """Initialize the AWS Cost Explorer client.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_session_token: AWS session token
            region_name: AWS region name
            profile_name: AWS profile name
            session: Existing boto3 session
            cache_ttl: Cache TTL in seconds
            max_retries: Maximum number of retries
            timeout: Request timeout in seconds

        Raises:
            ConfigurationError: If the configuration is invalid
            AuthenticationError: If authentication fails
            RegionError: If the region is invalid
        """
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.timeout = timeout

        try:
            self.session = session or self._create_session(
                aws_access_key_id,
                aws_secret_access_key,
                aws_session_token,
                region_name,
                profile_name,
            )
            self.client = self.session.client("ce", timeout=timeout)
        except (BotoCoreError, ClientError) as e:
            raise ConfigurationError(f"Failed to initialize AWS Cost Explorer client: {str(e)}")

        # Initialize cache
        self._cache = TTLCache(maxsize=100, ttl=cache_ttl)

    def _create_session(
        self,
        aws_access_key_id: Optional[str],
        aws_secret_access_key: Optional[str],
        aws_session_token: Optional[str],
        region_name: Optional[str],
        profile_name: Optional[str],
    ) -> boto3.Session:
        """Create a new boto3 session.

        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_session_token: AWS session token
            region_name: AWS region name
            profile_name: AWS profile name

        Returns:
            boto3.Session: The created session

        Raises:
            AuthenticationError: If authentication fails
            RegionError: If the region is invalid
        """
        try:
            return boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name,
                profile_name=profile_name,
            )
        except (BotoCoreError, ClientError) as e:
            if "InvalidClientTokenId" in str(e):
                raise CredentialsError("Invalid AWS credentials")
            if "InvalidRegion" in str(e):
                raise RegionError(f"Invalid AWS region: {region_name}")
            raise AuthenticationError(f"Failed to create AWS session: {str(e)}")

    @retry(
        retry=retry_if_exception_type((ClientError, BotoCoreError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_cost_and_usage(
        self,
        request: Union[GetCostAndUsageRequest, Dict[str, Any]],
    ) -> CostReport:
        """Get cost and usage data.

        Args:
            request: Cost and usage request parameters

        Returns:
            CostReport: The cost and usage report

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
            DataNotFoundError: If no data is found
        """
        if isinstance(request, dict):
            request = GetCostAndUsageRequest(**request)

        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    "Start": request.time_period.start.strftime("%Y-%m-%d"),
                    "End": request.time_period.end.strftime("%Y-%m-%d"),
                },
                Granularity=request.granularity.value,
                Metrics=[metric.value for metric in request.metrics],
                GroupBy=[
                    {"Type": group.type.value, "Key": group.key}
                    for group in (request.group_by or [])
                ],
                Filter=request.filter.dict() if request.filter else None,
                NextPageToken=request.next_page_token,
            )

            return CostReport(**response)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ValidationException":
                raise InvalidDateRangeError(str(e))
            if error_code == "ThrottlingException":
                raise RateLimitError(
                    str(e),
                    retry_after=int(e.response.get("ResponseMetadata", {}).get("RetryAfter", 0)),
                )
            if error_code == "LimitExceededException":
                raise ServiceQuotaExceededError(str(e))
            if error_code == "NoDataFoundException":
                raise DataNotFoundError(str(e))
            raise APIError(f"AWS Cost Explorer API error: {str(e)}")

        except BotoCoreError as e:
            raise APIError(f"AWS Cost Explorer API error: {str(e)}")

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    async def get_cost_forecast(
        self,
        request: Union[GetCostForecastRequest, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Get cost forecast.

        Args:
            request: Cost forecast request parameters

        Returns:
            Dict[str, Any]: The cost forecast

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = GetCostForecastRequest(**request)

        try:
            return self.client.get_cost_forecast(
                TimePeriod={
                    "Start": request.time_period.start.strftime("%Y-%m-%d"),
                    "End": request.time_period.end.strftime("%Y-%m-%d"),
                },
                Metric=request.metric.value,
                Granularity=request.granularity.value,
                PredictionIntervalLevel=request.prediction_interval_level,
            )
        except (ClientError, BotoCoreError) as e:
            raise APIError(f"Failed to get cost forecast: {str(e)}")

    async def get_reservation_utilization(
        self,
        request: Union[GetReservationUtilizationRequest, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Get reservation utilization data.

        Args:
            request: Reservation utilization request parameters

        Returns:
            Dict[str, Any]: The reservation utilization data

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = GetReservationUtilizationRequest(**request)

        try:
            return self.client.get_reservation_utilization(
                TimePeriod={
                    "Start": request.time_period.start.strftime("%Y-%m-%d"),
                    "End": request.time_period.end.strftime("%Y-%m-%d"),
                },
                GroupBy=[
                    {"Type": group.type.value, "Key": group.key}
                    for group in (request.group_by or [])
                ],
                Filter=request.filter.dict() if request.filter else None,
            )
        except (ClientError, BotoCoreError) as e:
            raise APIError(f"Failed to get reservation utilization: {str(e)}")

    async def get_savings_plans_utilization(
        self,
        request: Union[GetSavingsPlansUtilizationRequest, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Get Savings Plans utilization data.

        Args:
            request: Savings Plans utilization request parameters

        Returns:
            Dict[str, Any]: The Savings Plans utilization data

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = GetSavingsPlansUtilizationRequest(**request)

        try:
            return self.client.get_savings_plans_utilization(
                TimePeriod={
                    "Start": request.time_period.start.strftime("%Y-%m-%d"),
                    "End": request.time_period.end.strftime("%Y-%m-%d"),
                },
                GroupBy=[
                    {"Type": group.type.value, "Key": group.key}
                    for group in (request.group_by or [])
                ],
                Filter=request.filter.dict() if request.filter else None,
            )
        except (ClientError, BotoCoreError) as e:
            raise APIError(f"Failed to get Savings Plans utilization: {str(e)}")

    def close(self) -> None:
        """Close the client and clean up resources."""
        self._cache.clear()
        if hasattr(self, "client"):
            self.client.close()

    async def __aenter__(self) -> "AWSCostExplorerClient":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        self.close()
