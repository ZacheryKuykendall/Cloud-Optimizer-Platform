"""Azure Cost Management API client implementation."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    QueryDefinition,
    QueryResult,
    QueryTimePeriod,
)
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
    BudgetError,
    ConfigurationError,
    CredentialsError,
    DataNotFoundError,
    InvalidFilterError,
    InvalidGroupingError,
    InvalidMetricError,
    InvalidScopeError,
    InvalidTimeframeError,
    RateLimitError,
    ResourceGroupError,
    RetryError,
    SubscriptionError,
)
from .models import (
    BudgetDefinition,
    BudgetStatus,
    CostQueryDefinition,
    CostQueryResult,
    CreateBudgetRequest,
    DeleteBudgetRequest,
    ForecastDefinition,
    ForecastResult,
    GetCostRequest,
    GetForecastRequest,
    ListBudgetsRequest,
    UpdateBudgetRequest,
)

logger = logging.getLogger(__name__)


class AzureCostManagementClient:
    """Client for interacting with Azure Cost Management API."""

    def __init__(
        self,
        subscription_id: Optional[str] = None,
        credential: Optional[DefaultAzureCredential] = None,
        cache_ttl: int = 300,  # 5 minutes
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        """Initialize the Azure Cost Management client.

        Args:
            subscription_id: Azure subscription ID
            credential: Azure credential object
            cache_ttl: Cache TTL in seconds
            max_retries: Maximum number of retries
            timeout: Request timeout in seconds

        Raises:
            ConfigurationError: If the configuration is invalid
            AuthenticationError: If authentication fails
            SubscriptionError: If the subscription is invalid
        """
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.timeout = timeout

        try:
            self.credential = credential or DefaultAzureCredential()
            self.client = CostManagementClient(self.credential, timeout=timeout)
            if subscription_id:
                self.client.config.subscription_id = subscription_id
        except Exception as e:
            if "AuthenticationFailed" in str(e):
                raise AuthenticationError(str(e))
            if "SubscriptionNotFound" in str(e):
                raise SubscriptionError(str(e))
            raise ConfigurationError(f"Failed to initialize Azure Cost Management client: {str(e)}")

        # Initialize cache
        self._cache = TTLCache(maxsize=100, ttl=cache_ttl)

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_cost_and_usage(self, request: Union[GetCostRequest, Dict[str, Any]]) -> CostQueryResult:
        """Get cost and usage data.

        Args:
            request: Cost query request parameters

        Returns:
            CostQueryResult: The cost query result

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
            DataNotFoundError: If no data is found
        """
        if isinstance(request, dict):
            request = GetCostRequest(**request)

        try:
            query = QueryDefinition(
                type=request.query.type,
                timeframe=request.query.timeframe,
                time_period=QueryTimePeriod(
                    from_property=request.query.time_period.from_date,
                    to=request.query.time_period.to_date,
                ) if request.query.time_period else None,
                dataset=request.query.dataset.dict(),
            )

            response = self.client.query.usage(scope=request.scope, parameters=query)
            return CostQueryResult(**response.as_dict())

        except Exception as e:
            if "InvalidScope" in str(e):
                raise InvalidScopeError(str(e))
            if "InvalidTimeframe" in str(e):
                raise InvalidTimeframeError(str(e))
            if "InvalidMetric" in str(e):
                raise InvalidMetricError(str(e))
            if "InvalidFilter" in str(e):
                raise InvalidFilterError(str(e))
            if "InvalidGrouping" in str(e):
                raise InvalidGroupingError(str(e))
            if "ResourceNotFound" in str(e):
                raise DataNotFoundError(str(e))
            if "TooManyRequests" in str(e):
                retry_after = int(getattr(e.response, "retry_after", 0))
                raise RateLimitError(str(e), retry_after=retry_after)
            raise APIError(f"Azure Cost Management API error: {str(e)}")

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    async def get_cost_forecast(
        self, request: Union[GetForecastRequest, Dict[str, Any]]
    ) -> ForecastResult:
        """Get cost forecast.

        Args:
            request: Forecast request parameters

        Returns:
            ForecastResult: The forecast result

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = GetForecastRequest(**request)

        try:
            query = QueryDefinition(
                type=request.query.type,
                timeframe=request.query.timeframe,
                time_period=QueryTimePeriod(
                    from_property=request.query.time_period.from_date,
                    to=request.query.time_period.to_date,
                ) if request.query.time_period else None,
                dataset=request.query.dataset.dict(),
            )

            response = self.client.forecast.usage(scope=request.scope, parameters=query)
            return ForecastResult(**response.as_dict())

        except Exception as e:
            if "InvalidScope" in str(e):
                raise InvalidScopeError(str(e))
            raise APIError(f"Failed to get cost forecast: {str(e)}")

    async def create_budget(self, request: Union[CreateBudgetRequest, Dict[str, Any]]) -> BudgetStatus:
        """Create a budget.

        Args:
            request: Budget creation request parameters

        Returns:
            BudgetStatus: The created budget status

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = CreateBudgetRequest(**request)

        try:
            response = self.client.budgets.create_or_update(
                scope=request.scope,
                budget_name=request.budget_name,
                parameters=request.budget.dict(),
            )
            return BudgetStatus(**response.as_dict())

        except Exception as e:
            if "InvalidScope" in str(e):
                raise InvalidScopeError(str(e))
            raise BudgetError(f"Failed to create budget: {str(e)}")

    async def update_budget(self, request: Union[UpdateBudgetRequest, Dict[str, Any]]) -> BudgetStatus:
        """Update a budget.

        Args:
            request: Budget update request parameters

        Returns:
            BudgetStatus: The updated budget status

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = UpdateBudgetRequest(**request)

        try:
            response = self.client.budgets.create_or_update(
                scope=request.scope,
                budget_name=request.budget_name,
                parameters=request.budget.dict(),
            )
            return BudgetStatus(**response.as_dict())

        except Exception as e:
            if "InvalidScope" in str(e):
                raise InvalidScopeError(str(e))
            raise BudgetError(f"Failed to update budget: {str(e)}")

    async def delete_budget(self, request: Union[DeleteBudgetRequest, Dict[str, Any]]) -> None:
        """Delete a budget.

        Args:
            request: Budget deletion request parameters

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = DeleteBudgetRequest(**request)

        try:
            self.client.budgets.delete(
                scope=request.scope,
                budget_name=request.budget_name,
            )

        except Exception as e:
            if "InvalidScope" in str(e):
                raise InvalidScopeError(str(e))
            raise BudgetError(f"Failed to delete budget: {str(e)}")

    async def list_budgets(self, request: Union[ListBudgetsRequest, Dict[str, Any]]) -> List[BudgetStatus]:
        """List budgets.

        Args:
            request: Budget listing request parameters

        Returns:
            List[BudgetStatus]: List of budget statuses

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = ListBudgetsRequest(**request)

        try:
            response = self.client.budgets.list(
                scope=request.scope,
                filter=request.filter,
                top=request.top,
                skip=request.skip,
            )
            return [BudgetStatus(**budget.as_dict()) for budget in response]

        except Exception as e:
            if "InvalidScope" in str(e):
                raise InvalidScopeError(str(e))
            raise BudgetError(f"Failed to list budgets: {str(e)}")

    def close(self) -> None:
        """Close the client and clean up resources."""
        self._cache.clear()
        if hasattr(self, "client"):
            self.client.close()

    async def __aenter__(self) -> "AzureCostManagementClient":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        self.close()
