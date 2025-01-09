"""Cloud resource inventory manager.

This module provides the core functionality for tracking and managing cloud
resources across different providers.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import uuid4

from cloud_resource_inventory.exceptions import (
    GroupAlreadyExistsError,
    GroupNotFoundError,
    InvalidQueryError,
    ProviderAuthenticationError,
    ProviderAPIError,
    QueryTimeoutError,
    ResourceAccessError,
    ResourceAlreadyExistsError,
    ResourceDeletionError,
    ResourceNotFoundError,
    ResourceUpdateError,
    TagLimitExceededError,
    TagValidationError,
    UnsupportedProviderError,
    ValidationError,
)
from cloud_resource_inventory.models import (
    CloudProvider,
    Resource,
    ResourceConfiguration,
    ResourceCost,
    ResourceCriticality,
    ResourceGroup,
    ResourceInventoryState,
    ResourceLifecycle,
    ResourceMetrics,
    ResourceMonitoring,
    ResourceQuery,
    ResourceStatus,
    ResourceSummary,
    ResourceTag,
    ResourceType,
)

logger = logging.getLogger(__name__)


class ResourceInventoryManager:
    """Manager for cloud resource inventory."""

    def __init__(
        self,
        aws_credentials: Optional[Dict[str, str]] = None,
        azure_credentials: Optional[Dict[str, str]] = None,
        gcp_credentials: Optional[Dict[str, str]] = None,
        max_tags_per_resource: int = 50,
    ):
        """Initialize the inventory manager.

        Args:
            aws_credentials: Optional AWS credentials.
            azure_credentials: Optional Azure credentials.
            gcp_credentials: Optional GCP credentials.
            max_tags_per_resource: Maximum number of tags per resource.
        """
        self.providers: Set[CloudProvider] = set()
        self.max_tags_per_resource = max_tags_per_resource
        self.state = ResourceInventoryState(
            resources={},
            groups={},
            summary=ResourceSummary(total_resources=0)
        )

        # Initialize provider clients
        self.aws_client = None
        self.azure_client = None
        self.gcp_client = None

        if aws_credentials:
            self.aws_client = self._init_aws_client(aws_credentials)
            self.providers.add(CloudProvider.AWS)

        if azure_credentials:
            self.azure_client = self._init_azure_client(azure_credentials)
            self.providers.add(CloudProvider.AZURE)

        if gcp_credentials:
            self.gcp_client = self._init_gcp_client(gcp_credentials)
            self.providers.add(CloudProvider.GCP)

        # Validate configuration
        self._validate_configuration()

    async def discover_resources(
        self,
        providers: Optional[List[CloudProvider]] = None,
        resource_types: Optional[List[ResourceType]] = None,
        regions: Optional[List[str]] = None,
        include_metrics: bool = True,
        include_costs: bool = True,
    ) -> List[Resource]:
        """Discover cloud resources across providers.

        Args:
            providers: Optional list of providers to discover from.
            resource_types: Optional list of resource types to discover.
            regions: Optional list of regions to discover in.
            include_metrics: Whether to include resource metrics.
            include_costs: Whether to include resource costs.

        Returns:
            List of discovered resources.

        Raises:
            UnsupportedProviderError: If an unsupported provider is specified.
            ProviderAuthenticationError: If authentication fails.
            ProviderAPIError: If API calls fail.
        """
        if not providers:
            providers = list(self.providers)

        # Validate providers
        unsupported = set(providers) - self.providers
        if unsupported:
            raise UnsupportedProviderError(
                f"Unsupported providers: {', '.join(p.value for p in unsupported)}",
                provider=next(iter(unsupported)).value
            )

        discovered = []
        for provider in providers:
            try:
                resources = await self._discover_provider_resources(
                    provider,
                    resource_types,
                    regions,
                    include_metrics,
                    include_costs
                )
                discovered.extend(resources)
            except Exception as e:
                logger.error(f"Error discovering resources from {provider.value}: {str(e)}")
                continue

        # Update inventory state
        for resource in discovered:
            self.state.resources[resource.id] = resource

        self._update_summary()
        return discovered

    async def get_resource(self, resource_id: str) -> Resource:
        """Get a resource by ID.

        Args:
            resource_id: Resource ID.

        Returns:
            Resource details.

        Raises:
            ResourceNotFoundError: If resource not found.
        """
        if resource_id not in self.state.resources:
            raise ResourceNotFoundError(
                f"Resource not found: {resource_id}",
                provider="unknown",
                resource_id=resource_id
            )
        return self.state.resources[resource_id]

    async def update_resource(
        self,
        resource_id: str,
        updates: Dict[str, Any]
    ) -> Resource:
        """Update a resource.

        Args:
            resource_id: Resource ID.
            updates: Dictionary of updates to apply.

        Returns:
            Updated resource.

        Raises:
            ResourceNotFoundError: If resource not found.
            ResourceUpdateError: If update fails.
            ValidationError: If updates are invalid.
        """
        resource = await self.get_resource(resource_id)

        try:
            # Update provider-specific resource
            await self._update_provider_resource(resource, updates)

            # Update local state
            for key, value in updates.items():
                setattr(resource, key, value)
            resource.last_updated = datetime.utcnow()

            self._update_summary()
            return resource

        except Exception as e:
            raise ResourceUpdateError(
                f"Failed to update resource: {str(e)}",
                provider=resource.provider.value,
                resource_id=resource_id,
                details={"updates": updates}
            ) from e

    async def delete_resource(self, resource_id: str) -> None:
        """Delete a resource.

        Args:
            resource_id: Resource ID.

        Raises:
            ResourceNotFoundError: If resource not found.
            ResourceDeletionError: If deletion fails.
        """
        resource = await self.get_resource(resource_id)

        try:
            # Delete from provider
            await self._delete_provider_resource(resource)

            # Update local state
            del self.state.resources[resource_id]

            # Remove from any groups
            for group in self.state.groups.values():
                group.resources.discard(resource_id)

            self._update_summary()

        except Exception as e:
            raise ResourceDeletionError(
                f"Failed to delete resource: {str(e)}",
                provider=resource.provider.value,
                resource_id=resource_id
            ) from e

    async def tag_resource(
        self,
        resource_id: str,
        tags: Dict[str, str]
    ) -> Resource:
        """Tag a resource.

        Args:
            resource_id: Resource ID.
            tags: Tags to apply.

        Returns:
            Updated resource.

        Raises:
            ResourceNotFoundError: If resource not found.
            TagValidationError: If tags are invalid.
            TagLimitExceededError: If tag limit exceeded.
        """
        resource = await self.get_resource(resource_id)

        # Validate tags
        for key, value in tags.items():
            if not self._is_valid_tag(key, value):
                raise TagValidationError(
                    "Invalid tag",
                    tag_key=key,
                    tag_value=value
                )

        # Check tag limit
        if len(resource.tags) + len(tags) > self.max_tags_per_resource:
            raise TagLimitExceededError(
                "Tag limit exceeded",
                resource_id=resource_id,
                current_count=len(resource.tags),
                max_count=self.max_tags_per_resource
            )

        # Apply tags
        for key, value in tags.items():
            resource.tags[key] = ResourceTag(
                key=key,
                value=value
            )

        # Update provider tags
        await self._update_provider_tags(resource)

        return resource

    async def create_group(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> ResourceGroup:
        """Create a resource group.

        Args:
            name: Group name.
            description: Optional group description.
            tags: Optional group tags.

        Returns:
            Created group.

        Raises:
            GroupAlreadyExistsError: If group already exists.
            ValidationError: If parameters are invalid.
        """
        # Generate group ID
        group_id = str(uuid4())

        # Check if group exists
        if any(g.name == name for g in self.state.groups.values()):
            raise GroupAlreadyExistsError(
                f"Group already exists: {name}",
                group_id=group_id
            )

        # Create group
        group = ResourceGroup(
            id=group_id,
            name=name,
            description=description,
            tags={k: ResourceTag(key=k, value=v) for k, v in (tags or {}).items()}
        )

        self.state.groups[group_id] = group
        return group

    async def add_to_group(
        self,
        group_id: str,
        resource_ids: List[str]
    ) -> ResourceGroup:
        """Add resources to a group.

        Args:
            group_id: Group ID.
            resource_ids: Resource IDs to add.

        Returns:
            Updated group.

        Raises:
            GroupNotFoundError: If group not found.
            ResourceNotFoundError: If any resource not found.
        """
        # Get group
        if group_id not in self.state.groups:
            raise GroupNotFoundError(
                f"Group not found: {group_id}",
                group_id=group_id
            )
        group = self.state.groups[group_id]

        # Validate resources
        for resource_id in resource_ids:
            if resource_id not in self.state.resources:
                raise ResourceNotFoundError(
                    f"Resource not found: {resource_id}",
                    provider="unknown",
                    resource_id=resource_id
                )

        # Add resources
        group.resources.update(resource_ids)
        group.updated_at = datetime.utcnow()

        return group

    async def query_resources(self, query: ResourceQuery) -> List[Resource]:
        """Query resources based on criteria.

        Args:
            query: Query parameters.

        Returns:
            List of matching resources.

        Raises:
            InvalidQueryError: If query is invalid.
            QueryTimeoutError: If query times out.
        """
        try:
            results = []
            for resource in self.state.resources.values():
                if self._matches_query(resource, query):
                    results.append(resource)
            return results

        except Exception as e:
            raise InvalidQueryError(
                f"Invalid query: {str(e)}",
                query_params=query.dict()
            ) from e

    def _init_aws_client(self, credentials: Dict[str, str]) -> Any:
        """Initialize AWS client."""
        # TODO: Implement AWS client initialization
        return None

    def _init_azure_client(self, credentials: Dict[str, str]) -> Any:
        """Initialize Azure client."""
        # TODO: Implement Azure client initialization
        return None

    def _init_gcp_client(self, credentials: Dict[str, str]) -> Any:
        """Initialize GCP client."""
        # TODO: Implement GCP client initialization
        return None

    def _validate_configuration(self) -> None:
        """Validate manager configuration."""
        if not self.providers:
            raise ValidationError(
                "At least one cloud provider must be configured"
            )

    async def _discover_provider_resources(
        self,
        provider: CloudProvider,
        resource_types: Optional[List[ResourceType]],
        regions: Optional[List[str]],
        include_metrics: bool,
        include_costs: bool,
    ) -> List[Resource]:
        """Discover resources from a specific provider."""
        # TODO: Implement provider-specific resource discovery
        return []

    async def _update_provider_resource(
        self,
        resource: Resource,
        updates: Dict[str, Any]
    ) -> None:
        """Update a resource in its provider."""
        # TODO: Implement provider-specific resource updates
        pass

    async def _delete_provider_resource(self, resource: Resource) -> None:
        """Delete a resource from its provider."""
        # TODO: Implement provider-specific resource deletion
        pass

    async def _update_provider_tags(self, resource: Resource) -> None:
        """Update resource tags in provider."""
        # TODO: Implement provider-specific tag updates
        pass

    def _is_valid_tag(self, key: str, value: str) -> bool:
        """Validate a tag key-value pair."""
        # TODO: Implement tag validation
        return True

    def _matches_query(self, resource: Resource, query: ResourceQuery) -> bool:
        """Check if a resource matches query criteria."""
        if query.providers and resource.provider not in query.providers:
            return False

        if query.types and resource.type not in query.types:
            return False

        if query.regions and resource.region not in query.regions:
            return False

        if query.statuses and resource.status not in query.statuses:
            return False

        if query.lifecycles and resource.lifecycle not in query.lifecycles:
            return False

        if query.criticalities and resource.criticality not in query.criticalities:
            return False

        if query.tags:
            for key, value in query.tags.items():
                if key not in resource.tags or resource.tags[key].value != value:
                    return False

        if query.created_after and resource.metadata.created_at < query.created_after:
            return False

        if query.created_before and resource.metadata.created_at > query.created_before:
            return False

        if query.updated_after and resource.last_updated < query.updated_after:
            return False

        if query.updated_before and resource.last_updated > query.updated_before:
            return False

        return True

    def _update_summary(self) -> None:
        """Update inventory summary statistics."""
        summary = ResourceSummary(total_resources=len(self.state.resources))

        # Group by provider
        for resource in self.state.resources.values():
            summary.resources_by_provider[resource.provider] = (
                summary.resources_by_provider.get(resource.provider, 0) + 1
            )

            summary.resources_by_type[resource.type] = (
                summary.resources_by_type.get(resource.type, 0) + 1
            )

            summary.resources_by_status[resource.status] = (
                summary.resources_by_status.get(resource.status, 0) + 1
            )

            summary.resources_by_lifecycle[resource.lifecycle] = (
                summary.resources_by_lifecycle.get(resource.lifecycle, 0) + 1
            )

            summary.resources_by_criticality[resource.criticality] = (
                summary.resources_by_criticality.get(resource.criticality, 0) + 1
            )

            if resource.cost:
                currency = resource.cost.currency
                summary.total_cost[currency] = (
                    summary.total_cost.get(currency, 0.0) +
                    resource.cost.monthly_cost
                )

        self.state.summary = summary
        self.state.last_updated = datetime.utcnow()
