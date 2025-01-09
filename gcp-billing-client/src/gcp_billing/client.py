"""GCP Cloud Billing API client implementation."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from cachetools import TTLCache, cached
from google.cloud import billing, billing_budgets
from google.cloud.billing import CloudBillingClient
from google.cloud.billing_budgets import BudgetServiceClient
from google.cloud.exceptions import NotFound
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import (
    APIError,
    AuthenticationError,
    BigQueryError,
    BudgetError,
    CloudStorageError,
    ConfigurationError,
    CredentialsError,
    DataNotFoundError,
    ExportError,
    InvalidBillingAccountError,
    InvalidFilterError,
    InvalidGroupingError,
    InvalidMetricError,
    InvalidTimeframeError,
    ProjectError,
    PubSubError,
    RateLimitError,
    ServiceError,
)
from .models import (
    BillingQueryDefinition,
    BillingQueryResult,
    BudgetDefinition,
    BudgetStatus,
    CreateBudgetRequest,
    DeleteBudgetRequest,
    ExportDataRequest,
    ExportStatus,
    GetBillingDataRequest,
    GetPricingRequest,
    ListBudgetsRequest,
    PricingInfo,
    ServiceInfo,
    SkuInfo,
    UpdateBudgetRequest,
)

logger = logging.getLogger(__name__)


class GCPBillingClient:
    """Client for interacting with GCP Cloud Billing API."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials: Optional[Any] = None,
        cache_ttl: int = 300,  # 5 minutes
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        """Initialize the GCP Cloud Billing client.

        Args:
            project_id: GCP project ID
            credentials: GCP credentials object
            cache_ttl: Cache TTL in seconds
            max_retries: Maximum number of retries
            timeout: Request timeout in seconds

        Raises:
            ConfigurationError: If the configuration is invalid
            AuthenticationError: If authentication fails
            ProjectError: If the project is invalid
        """
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.timeout = timeout

        try:
            self.billing_client = CloudBillingClient(credentials=credentials)
            self.budgets_client = BudgetServiceClient(credentials=credentials)
            if project_id:
                self.project_id = project_id
        except Exception as e:
            if "unauthorized" in str(e).lower():
                raise AuthenticationError(str(e))
            if "project not found" in str(e).lower():
                raise ProjectError(str(e))
            raise ConfigurationError(f"Failed to initialize GCP Cloud Billing client: {str(e)}")

        # Initialize cache
        self._cache = TTLCache(maxsize=100, ttl=cache_ttl)

    @retry(
        retry=retry_if_exception_type((APIError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_billing_data(
        self, request: Union[GetBillingDataRequest, Dict[str, Any]]
    ) -> BillingQueryResult:
        """Get billing data.

        Args:
            request: Billing query request parameters

        Returns:
            BillingQueryResult: The billing query result

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
            DataNotFoundError: If no data is found
        """
        if isinstance(request, dict):
            request = GetBillingDataRequest(**request)

        try:
            billing_account_path = f"billingAccounts/{request.billing_account}"
            response = self.billing_client.get_billing_account_usage(
                request={
                    "name": billing_account_path,
                    "interval": {
                        "start_time": request.query.time_period.from_date,
                        "end_time": request.query.time_period.to_date,
                    },
                }
            )
            return BillingQueryResult(**response)

        except NotFound:
            raise DataNotFoundError(f"Billing account {request.billing_account} not found")
        except Exception as e:
            if "invalid billing account" in str(e).lower():
                raise InvalidBillingAccountError(str(e))
            if "invalid time range" in str(e).lower():
                raise InvalidTimeframeError(str(e))
            if "invalid metric" in str(e).lower():
                raise InvalidMetricError(str(e))
            if "invalid filter" in str(e).lower():
                raise InvalidFilterError(str(e))
            if "invalid grouping" in str(e).lower():
                raise InvalidGroupingError(str(e))
            if "resource exhausted" in str(e).lower():
                retry_after = int(getattr(e, "retry_after", 0))
                raise RateLimitError(str(e), retry_after=retry_after)
            raise APIError(f"GCP Cloud Billing API error: {str(e)}")

    @cached(cache=TTLCache(maxsize=100, ttl=300))
    async def get_pricing_info(
        self, request: Union[GetPricingRequest, Dict[str, Any]]
    ) -> List[PricingInfo]:
        """Get pricing information.

        Args:
            request: Pricing request parameters

        Returns:
            List[PricingInfo]: List of pricing information

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = GetPricingRequest(**request)

        try:
            services = self.billing_client.list_services()
            pricing_info = []

            for service in services:
                if request.service and service.display_name != request.service:
                    continue

                skus = self.billing_client.list_skus(parent=service.name)
                for sku in skus:
                    if request.sku and sku.sku_id != request.sku:
                        continue
                    if request.region and request.region not in sku.service_regions:
                        continue

                    pricing_info.append(
                        PricingInfo(
                            effective_time=sku.pricing_info[0].effective_time,
                            summary=sku.description,
                            pricing_expression=sku.pricing_info[0].pricing_expression.as_dict(),
                        )
                    )

            return pricing_info

        except Exception as e:
            if "service not found" in str(e).lower():
                raise ServiceError(str(e))
            raise APIError(f"Failed to get pricing information: {str(e)}")

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
            parent = f"billingAccounts/{request.billing_account}"
            budget = self.budgets_client.create_budget(
                parent=parent,
                budget=request.budget.dict(),
            )
            return BudgetStatus(**budget.as_dict())

        except Exception as e:
            if "invalid billing account" in str(e).lower():
                raise InvalidBillingAccountError(str(e))
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
            budget = self.budgets_client.update_budget(
                budget=request.budget.dict(),
                update_mask={"paths": ["amount", "thresholds", "display_name"]},
            )
            return BudgetStatus(**budget.as_dict())

        except Exception as e:
            if "budget not found" in str(e).lower():
                raise DataNotFoundError(str(e))
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
            self.budgets_client.delete_budget(name=request.name)

        except Exception as e:
            if "budget not found" in str(e).lower():
                raise DataNotFoundError(str(e))
            raise BudgetError(f"Failed to delete budget: {str(e)}")

    async def list_budgets(
        self, request: Union[ListBudgetsRequest, Dict[str, Any]]
    ) -> List[BudgetStatus]:
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
            parent = f"billingAccounts/{request.billing_account}"
            budgets = self.budgets_client.list_budgets(
                parent=parent,
                page_size=request.page_size,
                page_token=request.page_token,
            )
            return [BudgetStatus(**budget.as_dict()) for budget in budgets]

        except Exception as e:
            if "invalid billing account" in str(e).lower():
                raise InvalidBillingAccountError(str(e))
            raise BudgetError(f"Failed to list budgets: {str(e)}")

    async def export_billing_data(
        self, request: Union[ExportDataRequest, Dict[str, Any]]
    ) -> ExportStatus:
        """Export billing data to BigQuery or Cloud Storage.

        Args:
            request: Export request parameters

        Returns:
            ExportStatus: The export job status

        Raises:
            ValidationError: If the request parameters are invalid
            APIError: If the API request fails
        """
        if isinstance(request, dict):
            request = ExportDataRequest(**request)

        try:
            if "bigquery" in request.destination.lower():
                return await self._export_to_bigquery(request)
            elif "storage" in request.destination.lower():
                return await self._export_to_storage(request)
            else:
                raise ValidationError("Invalid export destination")

        except Exception as e:
            if "bigquery" in str(e).lower():
                raise BigQueryError(str(e))
            if "storage" in str(e).lower():
                raise CloudStorageError(str(e))
            raise ExportError(f"Failed to export billing data: {str(e)}")

    def close(self) -> None:
        """Close the client and clean up resources."""
        self._cache.clear()
        if hasattr(self, "billing_client"):
            self.billing_client.close()
        if hasattr(self, "budgets_client"):
            self.budgets_client.close()

    async def __aenter__(self) -> "GCPBillingClient":
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        self.close()

    async def _export_to_bigquery(self, request: ExportDataRequest) -> ExportStatus:
        """Export billing data to BigQuery."""
        # Implementation details for BigQuery export
        raise NotImplementedError

    async def _export_to_storage(self, request: ExportDataRequest) -> ExportStatus:
        """Export billing data to Cloud Storage."""
        # Implementation details for Cloud Storage export
        raise NotImplementedError
