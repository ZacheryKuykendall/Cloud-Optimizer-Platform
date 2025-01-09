"""Cloud network manager.

This module provides the core functionality for managing networks and VPN
connections across different cloud providers.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from cloud_network_manager.exceptions import (
    ConfigurationError,
    NetworkCreationError,
    NetworkDeletionError,
    NetworkUpdateError,
    ProviderAuthenticationError,
    UnsupportedProviderError,
    ValidationError,
    VPNCreationError,
    VPNDeletionError,
    VPNUpdateError,
)
from cloud_network_manager.models import (
    CloudProvider,
    NetworkConfiguration,
    NetworkDiff,
    NetworkState,
    NetworkValidationError,
    NetworkValidationResult,
    VPNConnection,
    VPNGatewayConfiguration,
    VPNStatus,
    VPNTunnelConfiguration,
)
from cloud_network_manager.vpn_modules.aws_azure.manager import AWSAzureVPNManager
from cloud_network_manager.vpn_modules.azure_gcp.manager import AzureGCPVPNManager
from cloud_network_manager.vpn_modules.aws_gcp.manager import AWSGCPVPNManager

logger = logging.getLogger(__name__)


class CloudNetworkManager:
    """Manager for cloud networks and VPN connections."""

    def __init__(
        self,
        aws_credentials: Optional[Dict[str, str]] = None,
        azure_credentials: Optional[Dict[str, str]] = None,
        gcp_credentials: Optional[Dict[str, str]] = None,
    ):
        """Initialize the manager.

        Args:
            aws_credentials: Optional AWS credentials.
            azure_credentials: Optional Azure credentials.
            gcp_credentials: Optional GCP credentials.
        """
        self.providers: Set[CloudProvider] = set()
        self.vpn_managers: Dict[Tuple[CloudProvider, CloudProvider], object] = {}

        # Initialize provider clients based on provided credentials
        if aws_credentials:
            self.providers.add(CloudProvider.AWS)
        if azure_credentials:
            self.providers.add(CloudProvider.AZURE)
        if gcp_credentials:
            self.providers.add(CloudProvider.GCP)

        # Initialize VPN managers for provider pairs
        if CloudProvider.AWS in self.providers and CloudProvider.AZURE in self.providers:
            self.vpn_managers[(CloudProvider.AWS, CloudProvider.AZURE)] = AWSAzureVPNManager(
                aws_credentials=aws_credentials,
                azure_credentials=azure_credentials
            )

        if CloudProvider.AZURE in self.providers and CloudProvider.GCP in self.providers:
            self.vpn_managers[(CloudProvider.AZURE, CloudProvider.GCP)] = AzureGCPVPNManager(
                azure_credentials=azure_credentials,
                gcp_credentials=gcp_credentials
            )

        if CloudProvider.AWS in self.providers and CloudProvider.GCP in self.providers:
            self.vpn_managers[(CloudProvider.AWS, CloudProvider.GCP)] = AWSGCPVPNManager(
                aws_credentials=aws_credentials,
                gcp_credentials=gcp_credentials
            )

    async def create_network(
        self,
        config: NetworkConfiguration,
        validate: bool = True
    ) -> str:
        """Create a new network in the specified cloud provider.

        Args:
            config: Network configuration.
            validate: Whether to validate the configuration.

        Returns:
            ID of the created network.

        Raises:
            ValidationError: If validation fails.
            NetworkCreationError: If network creation fails.
            UnsupportedProviderError: If provider not supported.
        """
        # Validate provider
        if config.provider not in self.providers:
            raise UnsupportedProviderError(
                f"Provider not supported: {config.provider}",
                provider=config.provider.value
            )

        # Validate configuration
        if validate:
            validation = await self.validate_network_config(config)
            if not validation.valid:
                raise ValidationError(
                    "Network configuration validation failed",
                    validation_errors=[e.dict() for e in validation.errors]
                )

        try:
            # Get appropriate VPN manager
            manager = self._get_vpn_manager_for_provider(config.provider)
            
            # Create network
            network_id = await manager.create_network(config)
            logger.info(
                "Created network %s in %s",
                config.name,
                config.provider.value
            )
            return network_id

        except Exception as e:
            raise NetworkCreationError(
                f"Failed to create network: {str(e)}",
                provider=config.provider.value,
                network_name=config.name,
                details={"original_error": str(e)}
            ) from e

    async def delete_network(
        self,
        provider: CloudProvider,
        network_id: str
    ) -> None:
        """Delete a network.

        Args:
            provider: Cloud provider.
            network_id: Network ID.

        Raises:
            NetworkDeletionError: If network deletion fails.
            UnsupportedProviderError: If provider not supported.
        """
        # Validate provider
        if provider not in self.providers:
            raise UnsupportedProviderError(
                f"Provider not supported: {provider}",
                provider=provider.value
            )

        try:
            # Get appropriate VPN manager
            manager = self._get_vpn_manager_for_provider(provider)
            
            # Delete network
            await manager.delete_network(network_id)
            logger.info(
                "Deleted network %s from %s",
                network_id,
                provider.value
            )

        except Exception as e:
            raise NetworkDeletionError(
                f"Failed to delete network: {str(e)}",
                provider=provider.value,
                network_id=network_id,
                details={"original_error": str(e)}
            ) from e

    async def create_vpn_connection(
        self,
        source_network: NetworkConfiguration,
        target_network: NetworkConfiguration,
        source_gateway: VPNGatewayConfiguration,
        target_gateway: VPNGatewayConfiguration,
        tunnels: List[VPNTunnelConfiguration],
        validate: bool = True
    ) -> VPNConnection:
        """Create a VPN connection between two networks.

        Args:
            source_network: Source network configuration.
            target_network: Target network configuration.
            source_gateway: Source VPN gateway configuration.
            target_gateway: Target VPN gateway configuration.
            tunnels: List of tunnel configurations.
            validate: Whether to validate the configuration.

        Returns:
            Created VPN connection.

        Raises:
            ValidationError: If validation fails.
            VPNCreationError: If VPN creation fails.
            UnsupportedProviderError: If provider pair not supported.
        """
        # Get provider pair
        provider_pair = (source_network.provider, target_network.provider)
        
        # Get appropriate VPN manager
        manager = self._get_vpn_manager_for_pair(*provider_pair)
        if not manager:
            raise UnsupportedProviderError(
                f"Provider pair not supported: {provider_pair}",
                provider=f"{provider_pair[0].value}-{provider_pair[1].value}"
            )

        try:
            # Create VPN connection
            connection = await manager.create_vpn_connection(
                source_network=source_network,
                target_network=target_network,
                source_gateway=source_gateway,
                target_gateway=target_gateway,
                tunnels=tunnels
            )
            logger.info(
                "Created VPN connection between %s and %s",
                source_network.name,
                target_network.name
            )
            return connection

        except Exception as e:
            raise VPNCreationError(
                f"Failed to create VPN connection: {str(e)}",
                source_network=source_network.name,
                target_network=target_network.name,
                details={"original_error": str(e)}
            ) from e

    async def delete_vpn_connection(
        self,
        connection_id: str,
        source_provider: CloudProvider,
        target_provider: CloudProvider
    ) -> None:
        """Delete a VPN connection.

        Args:
            connection_id: VPN connection ID.
            source_provider: Source cloud provider.
            target_provider: Target cloud provider.

        Raises:
            VPNDeletionError: If VPN deletion fails.
            UnsupportedProviderError: If provider pair not supported.
        """
        # Get provider pair
        provider_pair = (source_provider, target_provider)
        
        # Get appropriate VPN manager
        manager = self._get_vpn_manager_for_pair(*provider_pair)
        if not manager:
            raise UnsupportedProviderError(
                f"Provider pair not supported: {provider_pair}",
                provider=f"{provider_pair[0].value}-{provider_pair[1].value}"
            )

        try:
            # Delete VPN connection
            await manager.delete_vpn_connection(connection_id)
            logger.info(
                "Deleted VPN connection %s between %s and %s",
                connection_id,
                source_provider.value,
                target_provider.value
            )

        except Exception as e:
            raise VPNDeletionError(
                f"Failed to delete VPN connection: {str(e)}",
                vpn_id=connection_id,
                details={"original_error": str(e)}
            ) from e

    async def get_network_state(self) -> NetworkState:
        """Get current state of all networks and VPN connections.

        Returns:
            Current network state.
        """
        networks = {}
        vpn_connections = {}
        route_tables = {}
        network_acls = {}
        security_groups = {}

        # Get state from each provider
        for provider in self.providers:
            manager = self._get_vpn_manager_for_provider(provider)
            state = await manager.get_network_state()
            networks.update(state.networks)
            vpn_connections.update(state.vpn_connections)
            route_tables.update(state.route_tables)
            network_acls.update(state.network_acls)
            security_groups.update(state.security_groups)

        return NetworkState(
            networks=networks,
            vpn_connections=vpn_connections,
            route_tables=route_tables,
            network_acls=network_acls,
            security_groups=security_groups,
            last_updated=datetime.utcnow()
        )

    async def validate_network_config(
        self,
        config: NetworkConfiguration
    ) -> NetworkValidationResult:
        """Validate a network configuration.

        Args:
            config: Network configuration to validate.

        Returns:
            Validation result.
        """
        errors = []
        warnings = []

        # Basic validation
        if not config.name:
            errors.append(
                NetworkValidationError(
                    resource_id="",
                    resource_type="network",
                    error_type="validation",
                    description="Network name is required",
                    severity="high"
                )
            )

        if not config.cidr_block:
            errors.append(
                NetworkValidationError(
                    resource_id="",
                    resource_type="network",
                    error_type="validation",
                    description="CIDR block is required",
                    severity="high"
                )
            )

        # Provider-specific validation
        if config.provider in self.providers:
            manager = self._get_vpn_manager_for_provider(config.provider)
            provider_validation = await manager.validate_network_config(config)
            errors.extend(provider_validation.errors)
            warnings.extend(provider_validation.warnings)

        return NetworkValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            timestamp=datetime.utcnow()
        )

    def _get_vpn_manager_for_provider(self, provider: CloudProvider) -> object:
        """Get VPN manager for a single provider.

        Args:
            provider: Cloud provider.

        Returns:
            VPN manager instance.

        Raises:
            UnsupportedProviderError: If provider not supported.
        """
        # Find any manager that supports this provider
        for (p1, p2), manager in self.vpn_managers.items():
            if provider in (p1, p2):
                return manager

        raise UnsupportedProviderError(
            f"Provider not supported: {provider}",
            provider=provider.value
        )

    def _get_vpn_manager_for_pair(
        self,
        provider1: CloudProvider,
        provider2: CloudProvider
    ) -> Optional[object]:
        """Get VPN manager for a provider pair.

        Args:
            provider1: First cloud provider.
            provider2: Second cloud provider.

        Returns:
            VPN manager instance, or None if pair not supported.
        """
        # Try both orderings of the pair
        return (
            self.vpn_managers.get((provider1, provider2))
            or self.vpn_managers.get((provider2, provider1))
        )
