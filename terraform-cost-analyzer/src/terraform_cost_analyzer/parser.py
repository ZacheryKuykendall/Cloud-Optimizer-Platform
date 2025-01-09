"""Terraform plan parser for cost analysis.

This module provides functionality to parse Terraform plans and extract
resource information needed for cost analysis.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from terraform_cost_analyzer.exceptions import (
    ModuleParsingError,
    PlanParsingError,
    ResourceParsingError,
    ValidationError,
)
from terraform_cost_analyzer.models import (
    CloudProvider,
    ResourceAction,
    ResourceMetadata,
    ResourceType,
)

logger = logging.getLogger(__name__)


class TerraformPlanParser:
    """Parser for Terraform plan files."""

    def __init__(self):
        """Initialize the parser."""
        self._provider_mappings = self._load_provider_mappings()
        self._resource_mappings = self._load_resource_mappings()

    def _load_provider_mappings(self) -> Dict[str, CloudProvider]:
        """Load mappings between Terraform providers and cloud providers."""
        return {
            "aws": CloudProvider.AWS,
            "azurerm": CloudProvider.AZURE,
            "google": CloudProvider.GCP,
            "google-beta": CloudProvider.GCP,
        }

    def _load_resource_mappings(self) -> Dict[CloudProvider, Dict[str, ResourceType]]:
        """Load mappings between provider-specific and normalized resource types."""
        return {
            CloudProvider.AWS: {
                "aws_instance": ResourceType.COMPUTE,
                "aws_ebs_volume": ResourceType.STORAGE,
                "aws_s3_bucket": ResourceType.STORAGE,
                "aws_rds_cluster": ResourceType.DATABASE,
                "aws_rds_instance": ResourceType.DATABASE,
                "aws_vpc": ResourceType.NETWORK,
                "aws_subnet": ResourceType.NETWORK,
                "aws_lambda_function": ResourceType.SERVERLESS,
                "aws_ecs_cluster": ResourceType.CONTAINER,
                "aws_eks_cluster": ResourceType.CONTAINER,
                "aws_emr_cluster": ResourceType.ANALYTICS,
                "aws_waf_web_acl": ResourceType.SECURITY,
                "aws_cloudwatch_log_group": ResourceType.MANAGEMENT,
            },
            CloudProvider.AZURE: {
                "azurerm_virtual_machine": ResourceType.COMPUTE,
                "azurerm_managed_disk": ResourceType.STORAGE,
                "azurerm_storage_account": ResourceType.STORAGE,
                "azurerm_sql_database": ResourceType.DATABASE,
                "azurerm_mysql_server": ResourceType.DATABASE,
                "azurerm_virtual_network": ResourceType.NETWORK,
                "azurerm_subnet": ResourceType.NETWORK,
                "azurerm_function_app": ResourceType.SERVERLESS,
                "azurerm_container_group": ResourceType.CONTAINER,
                "azurerm_kubernetes_cluster": ResourceType.CONTAINER,
                "azurerm_hdinsight_cluster": ResourceType.ANALYTICS,
                "azurerm_firewall": ResourceType.SECURITY,
                "azurerm_log_analytics_workspace": ResourceType.MANAGEMENT,
            },
            CloudProvider.GCP: {
                "google_compute_instance": ResourceType.COMPUTE,
                "google_compute_disk": ResourceType.STORAGE,
                "google_storage_bucket": ResourceType.STORAGE,
                "google_sql_database_instance": ResourceType.DATABASE,
                "google_compute_network": ResourceType.NETWORK,
                "google_compute_subnetwork": ResourceType.NETWORK,
                "google_cloudfunctions_function": ResourceType.SERVERLESS,
                "google_container_cluster": ResourceType.CONTAINER,
                "google_bigquery_dataset": ResourceType.ANALYTICS,
                "google_cloud_armor_policy": ResourceType.SECURITY,
                "google_monitoring_workspace": ResourceType.MANAGEMENT,
            },
        }

    def parse_plan_file(self, plan_file: Union[str, Path]) -> Dict[str, Any]:
        """Parse a Terraform plan file.

        Args:
            plan_file: Path to the plan file (JSON format).

        Returns:
            Parsed plan data.

        Raises:
            PlanParsingError: If parsing fails.
        """
        try:
            with open(plan_file, "r") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            raise PlanParsingError(
                f"Failed to parse plan file: {str(e)}",
                plan_file=str(plan_file)
            ) from e

    def extract_resources(
        self,
        plan_data: Dict[str, Any]
    ) -> List[Tuple[ResourceMetadata, ResourceAction]]:
        """Extract resource information from plan data.

        Args:
            plan_data: Parsed Terraform plan data.

        Returns:
            List of tuples containing resource metadata and action.

        Raises:
            ResourceParsingError: If resource parsing fails.
        """
        resources = []
        resource_changes = plan_data.get("resource_changes", [])

        for change in resource_changes:
            try:
                # Extract basic resource info
                address = change.get("address", "")
                type_ = change.get("type", "")
                name = change.get("name", "")
                provider_name = change.get("provider_name", "")
                action = self._parse_action(change.get("change", {}))

                # Skip resources with no changes
                if action == ResourceAction.NO_CHANGE:
                    continue

                # Extract provider and region
                provider = self._parse_provider(provider_name)
                region = self._extract_region(change)

                # Map to normalized resource type
                normalized_type = self._map_resource_type(provider, type_)

                # Create resource metadata
                metadata = ResourceMetadata(
                    provider=provider,
                    type=type_,
                    name=name,
                    normalized_type=normalized_type,
                    region=region,
                    specifications=self._extract_specifications(change)
                )

                resources.append((metadata, action))

            except Exception as e:
                raise ResourceParsingError(
                    f"Failed to parse resource: {str(e)}",
                    resource_type=type_,
                    resource_name=name
                ) from e

        return resources

    def _parse_action(self, change: Dict[str, Any]) -> ResourceAction:
        """Parse the resource action from change data."""
        actions = set(change.get("actions", []))
        
        if not actions:
            return ResourceAction.NO_CHANGE
        elif actions == {"create"}:
            return ResourceAction.CREATE
        elif actions == {"update"}:
            return ResourceAction.UPDATE
        elif actions == {"delete"}:
            return ResourceAction.DELETE
        else:
            # Handle complex changes (e.g., replace = delete + create)
            if {"create", "delete"}.issubset(actions):
                return ResourceAction.UPDATE
            return ResourceAction.NO_CHANGE

    def _parse_provider(self, provider_name: str) -> CloudProvider:
        """Parse the cloud provider from provider name."""
        for prefix, provider in self._provider_mappings.items():
            if provider_name.startswith(prefix):
                return provider
        raise ValidationError(
            f"Unsupported provider: {provider_name}",
            provider_name
        )

    def _extract_region(self, resource: Dict[str, Any]) -> str:
        """Extract region information from resource data."""
        # Try to get region from provider config
        provider_config = resource.get("provider_config", {})
        if "region" in provider_config:
            return provider_config["region"]

        # Try to get region from resource attributes
        change = resource.get("change", {})
        after = change.get("after", {})
        
        # Common region attributes
        region_keys = ["region", "location", "availability_zone"]
        for key in region_keys:
            if key in after:
                return after[key]

        # Default to unknown if region can't be determined
        return "unknown"

    def _map_resource_type(
        self,
        provider: CloudProvider,
        terraform_type: str
    ) -> ResourceType:
        """Map Terraform resource type to normalized type."""
        mappings = self._resource_mappings.get(provider, {})
        return mappings.get(terraform_type, ResourceType.OTHER)

    def _extract_specifications(self, resource: Dict[str, Any]) -> Dict[str, str]:
        """Extract resource specifications from resource data."""
        specs = {}
        change = resource.get("change", {})
        after = change.get("after", {})

        # Common specifications
        if "instance_type" in after:
            specs["instance_type"] = after["instance_type"]
        if "size" in after:
            specs["size"] = after["size"]
        if "tier" in after:
            specs["tier"] = after["tier"]
        if "sku" in after:
            specs["sku"] = after["sku"]

        # Extract tags
        tags = after.get("tags", {})
        if tags:
            specs["tags"] = json.dumps(tags)

        return specs

    def extract_modules(
        self,
        plan_data: Dict[str, Any]
    ) -> Set[str]:
        """Extract module information from plan data.

        Args:
            plan_data: Parsed Terraform plan data.

        Returns:
            Set of module names.

        Raises:
            ModuleParsingError: If module parsing fails.
        """
        try:
            modules = set()
            for resource in plan_data.get("resource_changes", []):
                module = resource.get("module_address")
                if module:
                    modules.add(module)
            return modules
        except Exception as e:
            raise ModuleParsingError(
                f"Failed to extract modules: {str(e)}"
            ) from e

    def extract_providers(
        self,
        plan_data: Dict[str, Any]
    ) -> Set[CloudProvider]:
        """Extract cloud providers from plan data.

        Args:
            plan_data: Parsed Terraform plan data.

        Returns:
            Set of cloud providers.

        Raises:
            ValidationError: If provider parsing fails.
        """
        providers = set()
        for resource in plan_data.get("resource_changes", []):
            provider_name = resource.get("provider_name", "")
            try:
                provider = self._parse_provider(provider_name)
                providers.add(provider)
            except ValidationError:
                # Skip unsupported providers
                continue
        return providers

    def extract_regions(
        self,
        plan_data: Dict[str, Any]
    ) -> Dict[CloudProvider, Set[str]]:
        """Extract regions used by each provider.

        Args:
            plan_data: Parsed Terraform plan data.

        Returns:
            Dictionary mapping providers to their regions.
        """
        regions = {provider: set() for provider in CloudProvider}
        
        for resource in plan_data.get("resource_changes", []):
            try:
                provider = self._parse_provider(resource.get("provider_name", ""))
                region = self._extract_region(resource)
                if region != "unknown":
                    regions[provider].add(region)
            except ValidationError:
                continue

        return regions
