"""Provider selection engine.

This module provides the core functionality for making intelligent decisions
about resource placement across different cloud providers.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple

from vm_comparison.comparison import VmComparisonEngine
from storage_comparison.comparison import StorageComparisonEngine
from network_comparison.comparison import NetworkComparisonEngine

from provider_selection.exceptions import (
    BudgetError,
    CapabilityMatchError,
    ComplianceError,
    ConcurrencyError,
    DependencyError,
    NoMatchingProvidersError,
    PerformanceError,
    PolicyValidationError,
    RegionAvailabilityError,
    RuleEvaluationError,
    ScoreCalculationError,
    SelectionTimeoutError,
    ValidationError,
)
from provider_selection.models import (
    ComplianceFramework,
    ComplianceScore,
    CostEstimate,
    PerformanceMetric,
    PerformanceScore,
    PolicyEvaluation,
    ProviderCapability,
    ProviderOption,
    ResourceRequirements,
    ResourceType,
    RuleEvaluation,
    SelectionPolicy,
    SelectionResult,
    SelectionRule,
)


logger = logging.getLogger(__name__)


class ProviderSelectionEngine:
    """Engine for selecting optimal cloud providers for resources."""

    def __init__(
        self,
        vm_engine: VmComparisonEngine,
        storage_engine: StorageComparisonEngine,
        network_engine: NetworkComparisonEngine,
        selection_timeout: int = 30,
        cache_ttl: int = 3600,
        concurrent_evaluations: int = 10,
    ):
        """Initialize provider selection engine.

        Args:
            vm_engine: VM comparison engine
            storage_engine: Storage comparison engine
            network_engine: Network comparison engine
            selection_timeout: Selection timeout in seconds
            cache_ttl: Cache TTL in seconds
            concurrent_evaluations: Max concurrent evaluations
        """
        self.vm_engine = vm_engine
        self.storage_engine = storage_engine
        self.network_engine = network_engine
        self.selection_timeout = selection_timeout
        self.cache_ttl = cache_ttl
        self.concurrent_evaluations = concurrent_evaluations
        self._active_evaluations: Dict[str, asyncio.Task] = {}

    async def select_provider(
        self,
        requirements: ResourceRequirements,
        policy: Optional[SelectionPolicy] = None,
    ) -> SelectionResult:
        """Select optimal provider based on requirements and policy.

        Args:
            requirements: Resource requirements
            policy: Optional selection policy

        Returns:
            Selection result with optimal provider and alternatives

        Raises:
            ValidationError: If requirements are invalid
            NoMatchingProvidersError: If no providers match requirements
            SelectionTimeoutError: If selection times out
        """
        # Validate requirements
        self._validate_requirements(requirements)

        # Check concurrent evaluations limit
        if len(self._active_evaluations) >= self.concurrent_evaluations:
            raise ConcurrencyError(
                "Maximum concurrent evaluations limit reached",
                resource_name=requirements.name,
                conflicting_operation="select_provider",
                operation_id=str(len(self._active_evaluations)),
            )

        try:
            # Start evaluation task
            task = asyncio.create_task(
                self._evaluate_providers(requirements, policy)
            )
            self._active_evaluations[requirements.name] = task

            # Wait for result with timeout
            result = await asyncio.wait_for(
                task,
                timeout=self.selection_timeout
            )

            return result

        except asyncio.TimeoutError as e:
            raise SelectionTimeoutError(
                f"Provider selection timed out after {self.selection_timeout} seconds",
                timeout_seconds=self.selection_timeout,
            ) from e

        finally:
            # Clean up task
            self._active_evaluations.pop(requirements.name, None)

    async def _evaluate_providers(
        self,
        requirements: ResourceRequirements,
        policy: Optional[SelectionPolicy] = None,
    ) -> SelectionResult:
        """Evaluate providers against requirements and policy.

        Args:
            requirements: Resource requirements
            policy: Optional selection policy

        Returns:
            Selection result

        Raises:
            NoMatchingProvidersError: If no providers match requirements
        """
        # Get provider capabilities
        capabilities = await self._get_provider_capabilities(
            requirements.resource_type,
            requirements.regions,
        )

        # Filter providers by basic requirements
        valid_providers = self._filter_providers(requirements, capabilities)

        if not valid_providers:
            raise NoMatchingProvidersError(
                "No providers match the basic requirements",
                requirements=requirements.dict(),
                checked_providers=[c.provider for c in capabilities],
                failure_reasons={},  # TODO: Track failure reasons
            )

        # Get cost estimates
        cost_estimates = await self._get_cost_estimates(
            requirements=requirements,
            providers=[p.provider for p in valid_providers],
        )

        # Filter by budget if specified
        if requirements.max_monthly_budget:
            valid_providers = [
                p for p in valid_providers
                if cost_estimates[p.provider].monthly_cost <= requirements.max_monthly_budget
            ]

            if not valid_providers:
                raise BudgetError(
                    "No providers meet the budget requirements",
                    provider="all",
                    resource_type=requirements.resource_type.value,
                    max_budget=float(requirements.max_monthly_budget),
                    estimated_cost=float(min(
                        e.monthly_cost for e in cost_estimates.values()
                    )),
                )

        # Get performance scores
        performance_scores = await self._get_performance_scores(
            requirements=requirements,
            providers=[p.provider for p in valid_providers],
        )

        # Get compliance scores
        compliance_scores = await self._get_compliance_scores(
            requirements=requirements,
            providers=[p.provider for p in valid_providers],
        )

        # Create provider options
        options = [
            ProviderOption(
                provider=p.provider,
                resource_type=requirements.resource_type,
                region=next(iter(requirements.regions)),  # TODO: Handle multi-region
                capability=p,
                cost_estimate=cost_estimates[p.provider],
                performance_score=performance_scores[p.provider],
                compliance_score=compliance_scores[p.provider],
                total_score=0.0,  # Will be set after ranking
                ranking_factors={},  # Will be set after ranking
            )
            for p in valid_providers
        ]

        # Rank options
        ranked_options = self._rank_options(
            options=options,
            requirements=requirements,
            policy=policy,
        )

        if not ranked_options:
            raise NoMatchingProvidersError(
                "No providers meet all requirements after ranking",
                requirements=requirements.dict(),
                checked_providers=[o.provider for o in options],
                failure_reasons={},  # TODO: Track failure reasons
            )

        # Create selection result
        result = SelectionResult(
            resource_requirements=requirements,
            selected_option=ranked_options[0],
            alternative_options=ranked_options[1:],
            selection_factors=ranked_options[0].ranking_factors,
            cost_comparison=cost_estimates,
            performance_comparison=performance_scores,
            compliance_comparison=compliance_scores,
            valid_until=datetime.utcnow() + timedelta(seconds=self.cache_ttl),
        )

        return result

    def _validate_requirements(self, requirements: ResourceRequirements) -> None:
        """Validate resource requirements.

        Args:
            requirements: Resource requirements to validate

        Raises:
            ValidationError: If requirements are invalid
        """
        # Validate regions
        if not requirements.regions:
            raise ValidationError(
                "At least one region must be specified",
                field="regions",
                value=requirements.regions,
                constraints={"min_items": 1},
            )

        # Validate availability
        if requirements.min_availability < 0 or requirements.min_availability > 100:
            raise ValidationError(
                "Availability must be between 0 and 100",
                field="min_availability",
                value=requirements.min_availability,
                constraints={"min": 0, "max": 100},
            )

        # Validate budget
        if requirements.max_monthly_budget is not None:
            if requirements.max_monthly_budget <= 0:
                raise ValidationError(
                    "Budget must be greater than 0",
                    field="max_monthly_budget",
                    value=requirements.max_monthly_budget,
                    constraints={"min": 0},
                )

        # Validate resource-specific requirements
        if requirements.resource_type == ResourceType.COMPUTE:
            self._validate_compute_requirements(requirements.compute_requirements)
        elif requirements.resource_type == ResourceType.STORAGE:
            self._validate_storage_requirements(requirements.storage_requirements)
        elif requirements.resource_type == ResourceType.NETWORK:
            self._validate_network_requirements(requirements.network_requirements)

    async def _get_provider_capabilities(
        self,
        resource_type: ResourceType,
        regions: Set[str],
    ) -> List[ProviderCapability]:
        """Get provider capabilities for resource type and regions.

        Args:
            resource_type: Resource type
            regions: Required regions

        Returns:
            List of provider capabilities
        """
        capabilities = []

        # Get capabilities from comparison engines
        if resource_type == ResourceType.COMPUTE:
            for region in regions:
                vm_options = await self.vm_engine.list_instance_types(region)
                for provider, options in vm_options.items():
                    capabilities.append(
                        ProviderCapability(
                            provider=provider,
                            resource_type=resource_type,
                            region=region,
                            features=set(),  # TODO: Extract from options
                            certifications=set(),  # TODO: Extract from options
                            compliance_frameworks=set(),  # TODO: Extract from options
                            performance_metrics={},  # TODO: Extract from options
                            availability_sla=99.9,  # TODO: Get from provider
                            pricing_model={},  # TODO: Extract from options
                        )
                    )

        elif resource_type == ResourceType.STORAGE:
            for region in regions:
                storage_options = await self.storage_engine.list_storage_options(region)
                for provider, options in storage_options.items():
                    capabilities.append(
                        ProviderCapability(
                            provider=provider,
                            resource_type=resource_type,
                            region=region,
                            features=set(),  # TODO: Extract from options
                            certifications=set(),  # TODO: Extract from options
                            compliance_frameworks=set(),  # TODO: Extract from options
                            performance_metrics={},  # TODO: Extract from options
                            availability_sla=99.9,  # TODO: Get from provider
                            pricing_model={},  # TODO: Extract from options
                        )
                    )

        elif resource_type == ResourceType.NETWORK:
            for region in regions:
                network_options = await self.network_engine.list_network_options(region)
                for provider, options in network_options.items():
                    capabilities.append(
                        ProviderCapability(
                            provider=provider,
                            resource_type=resource_type,
                            region=region,
                            features=set(),  # TODO: Extract from options
                            certifications=set(),  # TODO: Extract from options
                            compliance_frameworks=set(),  # TODO: Extract from options
                            performance_metrics={},  # TODO: Extract from options
                            availability_sla=99.9,  # TODO: Get from provider
                            pricing_model={},  # TODO: Extract from options
                        )
                    )

        return capabilities

    def _filter_providers(
        self,
        requirements: ResourceRequirements,
        capabilities: List[ProviderCapability],
    ) -> List[ProviderCapability]:
        """Filter providers by basic requirements.

        Args:
            requirements: Resource requirements
            capabilities: Provider capabilities

        Returns:
            Filtered list of provider capabilities
        """
        valid_providers = []

        for capability in capabilities:
            # Check if provider is excluded
            if (
                requirements.excluded_providers
                and capability.provider in requirements.excluded_providers
            ):
                continue

            # Check if provider supports all required regions
            if not all(
                any(c.region == r for c in capabilities)
                for r in requirements.regions
            ):
                continue

            # Check if provider meets availability requirement
            if capability.availability_sla < requirements.min_availability:
                continue

            # Check if provider has required features
            if not requirements.required_features.issubset(capability.features):
                continue

            # Check if provider has required certifications
            if not requirements.required_certifications.issubset(capability.certifications):
                continue

            # Check if provider supports required compliance frameworks
            if not requirements.compliance_frameworks.issubset(capability.compliance_frameworks):
                continue

            valid_providers.append(capability)

        return valid_providers

    async def _get_cost_estimates(
        self,
        requirements: ResourceRequirements,
        providers: List[str],
    ) -> Dict[str, CostEstimate]:
        """Get cost estimates from providers.

        Args:
            requirements: Resource requirements
            providers: List of providers to check

        Returns:
            Dictionary mapping providers to cost estimates
        """
        estimates = {}

        # Get estimates from comparison engines
        if requirements.resource_type == ResourceType.COMPUTE:
            vm_costs = await self.vm_engine.get_instance_costs(
                providers=providers,
                region=next(iter(requirements.regions)),  # TODO: Handle multi-region
                requirements=requirements.compute_requirements,
            )
            for provider, cost in vm_costs.items():
                estimates[provider] = CostEstimate(
                    provider=provider,
                    resource_type=requirements.resource_type,
                    region=next(iter(requirements.regions)),
                    monthly_cost=cost.monthly_cost,
                    compute_cost=cost.compute_cost,
                    storage_cost=cost.storage_cost,
                    network_cost=cost.network_cost,
                )

        elif requirements.resource_type == ResourceType.STORAGE:
            storage_costs = await self.storage_engine.get_storage_costs(
                providers=providers,
                region=next(iter(requirements.regions)),
                requirements=requirements.storage_requirements,
            )
            for provider, cost in storage_costs.items():
                estimates[provider] = CostEstimate(
                    provider=provider,
                    resource_type=requirements.resource_type,
                    region=next(iter(requirements.regions)),
                    monthly_cost=cost.monthly_cost,
                    storage_cost=cost.storage_cost,
                    network_cost=cost.network_cost,
                )

        elif requirements.resource_type == ResourceType.NETWORK:
            network_costs = await self.network_engine.get_network_costs(
                providers=providers,
                region=next(iter(requirements.regions)),
                requirements=requirements.network_requirements,
            )
            for provider, cost in network_costs.items():
                estimates[provider] = CostEstimate(
                    provider=provider,
                    resource_type=requirements.resource_type,
                    region=next(iter(requirements.regions)),
                    monthly_cost=cost.monthly_cost,
                    network_cost=cost.network_cost,
                )

        return estimates

    async def _get_performance_scores(
        self,
        requirements: ResourceRequirements,
        providers: List[str],
    ) -> Dict[str, PerformanceScore]:
        """Get performance scores for providers.

        Args:
            requirements: Resource requirements
            providers: List of providers to check

        Returns:
            Dictionary mapping providers to performance scores
        """
        scores = {}

        for provider in providers:
            # Calculate scores based on requirements and capabilities
            latency_score = self._calculate_latency_score(provider, requirements)
            throughput_score = self._calculate_throughput_score(provider, requirements)
            reliability_score = self._calculate_reliability_score(provider, requirements)
            scalability_score = self._calculate_scalability_score(provider, requirements)

            # Calculate overall score
            overall_score = (
                latency_score * 0.3 +
                throughput_score * 0.3 +
                reliability_score * 0.2 +
                scalability_score * 0.2
            )

            scores[provider] = PerformanceScore(
                provider=provider,
                resource_type=requirements.resource_type,
                region=next(iter(requirements.regions)),
                latency_score=latency_score,
                throughput_score=throughput_score,
                reliability_score=reliability_score,
                scalability_score=scalability_score,
                overall_score=overall_score,
                metrics={},  # TODO: Add actual metrics
            )

        return scores

    async def _get_compliance_scores(
        self,
        requirements: ResourceRequirements,
        providers: List[str],
    ) -> Dict[str, ComplianceScore]:
        """Get compliance scores for providers.

        Args:
            requirements: Resource requirements
            providers: List of providers to check

        Returns:
            Dictionary mapping providers to compliance scores
        """
        scores = {}

        for provider in providers:
            # Calculate framework coverage
            framework_scores = {}
            for framework in ComplianceFramework:
                framework_scores[framework] = self._calculate_framework_score(
                    provider, requirements, framework
                )

            # Calculate certification and feature coverage
            certification_coverage = self._calculate_certification_coverage(
                provider, requirements
            )
            feature_coverage = self._calculate_feature_coverage(
                provider, requirements
            )

            # Calculate overall score
            overall_score = (
                sum(framework_scores.values()) / len(framework_scores) * 0.4 +
                certification_coverage * 0.3 +
                feature_coverage * 0.3
            )

            scores[provider] = ComplianceScore(
                provider=provider,
                resource_type=requirements.resource_type,
                region=next(iter(requirements.regions)),
                framework_scores=framework_scores,
                certification_coverage=certification_coverage,
                feature_coverage=feature_coverage,
                overall_score=overall_score,
            )

        return scores

    def _rank_options(
        self,
        options: List[ProviderOption],
        requirements: ResourceRequirements,
        policy: Optional[SelectionPolicy] = None,
    ) -> List[ProviderOption]:
        """Rank provider options based on requirements and policy.

        Args:
            options: Provider options to rank
            requirements: Resource requirements
            policy: Optional selection policy

        Returns:
            Ranked list of provider options
        """
        if not options:
            return []

        # Define scoring weights
        weights = {
            "cost": 0.4,
            "performance": 0.3,
            "compliance": 0.2,
            "preference": 0.1,
        }

        # Override weights if policy specified
        if policy and policy.default_weights:
            weights.update(policy.default_weights)

        # Calculate total scores
        for option in options:
            # Calculate component scores
            cost_score = self._calculate_cost_score(option, requirements)
            performance_score = option.performance_score.overall_score
            compliance_score = option.compliance_score.overall_score
            preference_score = self._calculate_preference_score(
                option, requirements
            )

            # Apply weights
            total_score = (
                cost_score * weights["cost"] +
                performance_score * weights["performance"] +
                compliance_score * weights["compliance"] +
                preference_score * weights["preference"]
            )

            option.total_score = total_score
            option.ranking_factors = {
                "cost_score": cost_score,
                "performance_score": performance_score,
                "compliance_score": compliance_score,
                "preference_score": preference_score,
                "weights": weights,
            }

        # Sort by total score descending
        return sorted(options, key=lambda x: x.total_score, reverse=True)

    def _calculate_cost_score(
        self,
        option: ProviderOption,
        requirements: ResourceRequirements,
    ) -> float:
        """Calculate cost score for provider option.

        Args:
            option: Provider option
            requirements: Resource requirements

        Returns:
            Cost score between 0 and 1
        """
        if requirements.max_monthly_budget:
            # Score based on percentage of budget used
            budget_ratio = float(
                option.cost_estimate.monthly_cost
                / requirements.max_monthly_budget
            )
            return max(0.0, min(1.0, 1.0 - budget_ratio))
        else:
            # Score based on relative cost compared to other providers
            # TODO: Implement relative cost scoring
            return 0.5

    def _calculate_preference_score(
        self,
        option: ProviderOption,
        requirements: ResourceRequirements,
    ) -> float:
        """Calculate preference score for provider option.

        Args:
            option: Provider option
            requirements: Resource requirements

        Returns:
            Preference score between 0 and 1
        """
        if requirements.preferred_providers:
            return 1.0 if option.provider in requirements.preferred_providers else 0.0
        return 0.5

    def _calculate_latency_score(
        self,
        provider: str,
        requirements: ResourceRequirements,
    ) -> float:
        """Calculate latency score for provider.

        Args:
            provider: Provider name
            requirements: Resource requirements

        Returns:
            Latency score between 0 and 1
        """
        # TODO: Implement actual latency scoring
        return 0.5

    def _calculate_throughput_score(
        self,
        provider: str,
        requirements: ResourceRequirements,
    ) -> float:
        """Calculate throughput score for provider.

        Args:
            provider: Provider name
            requirements: Resource requirements

        Returns:
            Throughput score between 0 and 1
        """
        # TODO: Implement actual throughput scoring
        return 0.5

    def _calculate_reliability_score(
        self,
        provider: str,
        requirements: ResourceRequirements,
    ) -> float:
        """Calculate reliability score for provider.

        Args:
            provider: Provider name
            requirements: Resource requirements

        Returns:
            Reliability score between 0 and 1
        """
        # TODO: Implement actual reliability scoring
        return 0.5

    def _calculate_scalability_score(
        self,
        provider: str,
        requirements: ResourceRequirements,
    ) -> float:
        """Calculate scalability score for provider.

        Args:
            provider: Provider name
            requirements: Resource requirements

        Returns:
            Scalability score between 0 and 1
        """
        # TODO: Implement actual scalability scoring
        return 0.5

    def _calculate_framework_score(
        self,
        provider: str,
        requirements: ResourceRequirements,
        framework: ComplianceFramework,
    ) -> float:
        """Calculate compliance framework score for provider.

        Args:
            provider: Provider name
            requirements: Resource requirements
            framework: Compliance framework

        Returns:
            Framework score between 0 and 1
        """
        # TODO: Implement actual framework scoring
        return 0.5

    def _calculate_certification_coverage(
        self,
        provider: str,
        requirements: ResourceRequirements,
    ) -> float:
        """Calculate certification coverage for provider.

        Args:
            provider: Provider name
            requirements: Resource requirements

        Returns:
            Certification coverage between 0 and 1
        """
        # TODO: Implement actual certification coverage calculation
        return 0.5

    def _calculate_feature_coverage(
        self,
        provider: str,
        requirements: ResourceRequirements,
    ) -> float:
        """Calculate feature coverage for provider.

        Args:
            provider: Provider name
            requirements: Resource requirements

        Returns:
            Feature coverage between 0 and 1
        """
        # TODO: Implement actual feature coverage calculation
        return 0.5

    def _validate_compute_requirements(
        self,
        requirements: Optional[Dict[str, Any]],
    ) -> None:
        """Validate compute-specific requirements.

        Args:
            requirements: Compute requirements to validate

        Raises:
            ValidationError: If requirements are invalid
        """
        if not requirements:
            raise ValidationError(
                "Compute requirements must be specified",
                field="compute_requirements",
                value=None,
                constraints={"required": True},
            )

        # TODO: Add compute-specific validation

    def _validate_storage_requirements(
        self,
        requirements: Optional[Dict[str, Any]],
    ) -> None:
        """Validate storage-specific requirements.

        Args:
            requirements: Storage requirements to validate

        Raises:
            ValidationError: If requirements are invalid
        """
        if not requirements:
            raise ValidationError(
                "Storage requirements must be specified",
                field="storage_requirements",
                value=None,
                constraints={"required": True},
            )

        # TODO: Add storage-specific validation

    def _validate_network_requirements(
        self,
        requirements: Optional[Dict[str, Any]],
    ) -> None:
        """Validate network-specific requirements.

        Args:
            requirements: Network requirements to validate

        Raises:
            ValidationError: If requirements are invalid
        """
        if not requirements:
            raise ValidationError(
                "Network requirements must be specified",
                field="network_requirements",
                value=None,
                constraints={"required": True},
            )

        # TODO: Add network-specific validation
