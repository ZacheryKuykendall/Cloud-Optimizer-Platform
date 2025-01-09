"""Cloud cost optimizer.

This module provides the core functionality for analyzing cloud resources
and generating cost optimization recommendations.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple
from uuid import uuid4

from aws_cost_explorer import AWSCostExplorerClient
from azure_cost_management import AzureCostManagementClient
from gcp_billing import GCPBillingClient

from cloud_cost_optimizer.exceptions import (
    ConfigurationError,
    CostCalculationError,
    MetricsCollectionError,
    OptimizationAnalysisError,
    OptimizationApplicationError,
    PolicyValidationError,
    ProviderAuthenticationError,
    ResourceNotFoundError,
    UnsupportedProviderError,
    ValidationError,
)
from cloud_cost_optimizer.models import (
    CloudProvider,
    ComplianceCheck,
    OptimizationEvent,
    OptimizationPolicy,
    OptimizationRecommendation,
    OptimizationReport,
    OptimizationResult,
    OptimizationSummary,
    OptimizationType,
    ResourceAnalysis,
    ResourceConfiguration,
    ResourceCost,
    ResourceMetrics,
    ResourceType,
    ResourceUsagePattern,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


class CloudCostOptimizer:
    """Optimizer for cloud resource costs."""

    def __init__(
        self,
        aws_credentials: Optional[Dict[str, str]] = None,
        azure_credentials: Optional[Dict[str, str]] = None,
        gcp_credentials: Optional[Dict[str, str]] = None,
        default_currency: str = "USD",
    ):
        """Initialize the optimizer.

        Args:
            aws_credentials: Optional AWS credentials.
            azure_credentials: Optional Azure credentials.
            gcp_credentials: Optional GCP credentials.
            default_currency: Default currency for cost calculations.
        """
        self.providers: Set[CloudProvider] = set()
        self.default_currency = default_currency.upper()

        # Initialize provider clients
        self.aws_client = None
        self.azure_client = None
        self.gcp_client = None

        if aws_credentials:
            self.aws_client = AWSCostExplorerClient(**aws_credentials)
            self.providers.add(CloudProvider.AWS)

        if azure_credentials:
            self.azure_client = AzureCostManagementClient(**azure_credentials)
            self.providers.add(CloudProvider.AZURE)

        if gcp_credentials:
            self.gcp_client = GCPBillingClient(**gcp_credentials)
            self.providers.add(CloudProvider.GCP)

        # Validate configuration
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate optimizer configuration.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        if not self.providers:
            raise ConfigurationError(
                "At least one cloud provider must be configured"
            )

    async def analyze_resources(
        self,
        resource_ids: Optional[List[str]] = None,
        resource_types: Optional[List[ResourceType]] = None,
        providers: Optional[List[CloudProvider]] = None,
        include_metrics: bool = True,
        include_costs: bool = True,
    ) -> List[ResourceAnalysis]:
        """Analyze cloud resources for optimization opportunities.

        Args:
            resource_ids: Optional list of specific resource IDs to analyze.
            resource_types: Optional list of resource types to analyze.
            providers: Optional list of providers to analyze.
            include_metrics: Whether to include resource metrics.
            include_costs: Whether to include cost information.

        Returns:
            List of resource analyses.

        Raises:
            ValidationError: If input validation fails.
            ResourceNotFoundError: If a resource cannot be found.
        """
        # Validate providers
        if providers:
            unsupported = set(providers) - self.providers
            if unsupported:
                raise ValidationError(
                    f"Unsupported providers: {', '.join(p.value for p in unsupported)}"
                )
        else:
            providers = list(self.providers)

        analyses = []
        for provider in providers:
            try:
                # Get resources for provider
                resources = await self._get_provider_resources(
                    provider,
                    resource_ids,
                    resource_types
                )

                # Analyze each resource
                for resource in resources:
                    analysis = await self._analyze_resource(
                        resource,
                        include_metrics,
                        include_costs
                    )
                    analyses.append(analysis)

            except Exception as e:
                logger.error(f"Error analyzing {provider.value} resources: {str(e)}")
                continue

        return analyses

    async def generate_recommendations(
        self,
        analyses: List[ResourceAnalysis],
        optimization_types: Optional[List[OptimizationType]] = None,
        min_savings_amount: Optional[Decimal] = None,
        min_savings_percentage: Optional[float] = None,
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations from resource analyses.

        Args:
            analyses: List of resource analyses.
            optimization_types: Optional list of optimization types to consider.
            min_savings_amount: Minimum absolute savings amount.
            min_savings_percentage: Minimum savings as percentage.

        Returns:
            List of optimization recommendations.

        Raises:
            ValidationError: If input validation fails.
        """
        recommendations = []

        for analysis in analyses:
            try:
                # Generate recommendations for each optimization type
                for opt_type in optimization_types or OptimizationType:
                    recommendation = await self._generate_recommendation(
                        analysis,
                        opt_type,
                        min_savings_amount,
                        min_savings_percentage
                    )
                    if recommendation:
                        recommendations.append(recommendation)

            except Exception as e:
                logger.error(
                    f"Error generating recommendations for {analysis.resource.resource_id}: {str(e)}"
                )
                continue

        return recommendations

    async def apply_recommendation(
        self,
        recommendation: OptimizationRecommendation,
        dry_run: bool = False,
    ) -> OptimizationResult:
        """Apply an optimization recommendation.

        Args:
            recommendation: Recommendation to apply.
            dry_run: Whether to simulate the application.

        Returns:
            Result of the optimization application.

        Raises:
            OptimizationApplicationError: If application fails.
        """
        try:
            # Validate recommendation
            if recommendation.expires_at and recommendation.expires_at < datetime.utcnow():
                raise ValidationError("Recommendation has expired")

            # Apply optimization based on type
            if dry_run:
                status = "simulated"
                completed_at = None
            else:
                result = await self._apply_optimization(recommendation)
                status = result["status"]
                completed_at = datetime.utcnow()

            return OptimizationResult(
                recommendation_id=recommendation.id,
                resource_id=recommendation.resource_id,
                status=status,
                completed_at=completed_at,
                actual_savings=recommendation.estimated_savings if dry_run else None
            )

        except Exception as e:
            raise OptimizationApplicationError(
                f"Failed to apply optimization: {str(e)}",
                recommendation_id=recommendation.id,
                resource_id=recommendation.resource_id,
                details={"original_error": str(e)}
            ) from e

    async def validate_policy(
        self,
        policy: OptimizationPolicy
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Validate an optimization policy.

        Args:
            policy: Policy to validate.

        Returns:
            Tuple of (is_valid, validation_errors).

        Raises:
            PolicyValidationError: If validation fails.
        """
        errors = []

        # Validate providers
        unsupported = policy.providers - self.providers
        if unsupported:
            errors.append({
                "field": "providers",
                "error": f"Unsupported providers: {', '.join(p.value for p in unsupported)}"
            })

        # Validate resource types
        if not policy.resource_types:
            errors.append({
                "field": "resource_types",
                "error": "At least one resource type must be specified"
            })

        # Validate optimization types
        if not policy.optimization_types:
            errors.append({
                "field": "optimization_types",
                "error": "At least one optimization type must be specified"
            })

        # Validate schedule if provided
        if policy.schedule and not self._is_valid_cron(policy.schedule):
            errors.append({
                "field": "schedule",
                "error": "Invalid cron expression"
            })

        return (len(errors) == 0, errors)

    async def generate_report(
        self,
        analyses: List[ResourceAnalysis],
        recommendations: List[OptimizationRecommendation],
        applied_optimizations: List[OptimizationResult],
        time_period: str,
    ) -> OptimizationReport:
        """Generate a detailed optimization report.

        Args:
            analyses: List of resource analyses.
            recommendations: List of recommendations.
            applied_optimizations: List of applied optimizations.
            time_period: Time period for the report.

        Returns:
            Detailed optimization report.
        """
        # Generate summary
        summary = OptimizationSummary(
            total_resources_analyzed=len(analyses),
            resources_with_recommendations=len({r.resource_id for r in recommendations}),
            total_recommendations=len(recommendations),
            total_potential_savings=self._calculate_total_savings(recommendations),
            recommendations_by_type=self._group_recommendations_by_type(recommendations),
            recommendations_by_severity=self._group_recommendations_by_severity(recommendations),
            savings_by_provider=self._group_savings_by_provider(recommendations)
        )

        # Run compliance checks
        compliance_checks = await self._run_compliance_checks(analyses, recommendations)

        # Generate report
        return OptimizationReport(
            id=str(uuid4()),
            report_type="detailed",
            time_period=time_period,
            summary=summary,
            resource_analyses=analyses,
            applied_optimizations=applied_optimizations,
            compliance_checks=compliance_checks,
            events=await self._get_optimization_events(time_period),
            generated_at=datetime.utcnow()
        )

    async def _get_provider_resources(
        self,
        provider: CloudProvider,
        resource_ids: Optional[List[str]] = None,
        resource_types: Optional[List[ResourceType]] = None,
    ) -> List[ResourceConfiguration]:
        """Get resources from a specific provider."""
        if provider == CloudProvider.AWS:
            return await self.aws_client.get_resources(resource_ids, resource_types)
        elif provider == CloudProvider.AZURE:
            return await self.azure_client.get_resources(resource_ids, resource_types)
        elif provider == CloudProvider.GCP:
            return await self.gcp_client.get_resources(resource_ids, resource_types)
        else:
            raise UnsupportedProviderError(f"Unsupported provider: {provider}", provider.value)

    async def _analyze_resource(
        self,
        resource: ResourceConfiguration,
        include_metrics: bool,
        include_costs: bool,
    ) -> ResourceAnalysis:
        """Analyze a single resource."""
        metrics = None
        usage_pattern = None
        current_cost = None

        if include_metrics:
            metrics = await self._collect_resource_metrics(resource)
            usage_pattern = await self._analyze_usage_pattern(resource, metrics)

        if include_costs:
            current_cost = await self._get_resource_cost(resource)

        return ResourceAnalysis(
            resource=resource,
            metrics=metrics,
            usage_pattern=usage_pattern,
            current_cost=current_cost,
            last_analyzed=datetime.utcnow()
        )

    async def _collect_resource_metrics(
        self,
        resource: ResourceConfiguration
    ) -> ResourceMetrics:
        """Collect metrics for a resource."""
        try:
            if resource.provider == CloudProvider.AWS:
                return await self.aws_client.get_metrics(resource.resource_id)
            elif resource.provider == CloudProvider.AZURE:
                return await self.azure_client.get_metrics(resource.resource_id)
            elif resource.provider == CloudProvider.GCP:
                return await self.gcp_client.get_metrics(resource.resource_id)
            else:
                raise UnsupportedProviderError(
                    f"Unsupported provider: {resource.provider}",
                    resource.provider.value
                )
        except Exception as e:
            raise MetricsCollectionError(
                f"Failed to collect metrics: {str(e)}",
                resource_id=resource.resource_id,
                metric_names=["cpu", "memory", "disk", "network"],
                details={"original_error": str(e)}
            ) from e

    async def _analyze_usage_pattern(
        self,
        resource: ResourceConfiguration,
        metrics: ResourceMetrics
    ) -> ResourceUsagePattern:
        """Analyze resource usage patterns."""
        # TODO: Implement usage pattern analysis
        return ResourceUsagePattern()

    async def _get_resource_cost(
        self,
        resource: ResourceConfiguration
    ) -> ResourceCost:
        """Get cost information for a resource."""
        try:
            if resource.provider == CloudProvider.AWS:
                return await self.aws_client.get_cost(resource.resource_id)
            elif resource.provider == CloudProvider.AZURE:
                return await self.azure_client.get_cost(resource.resource_id)
            elif resource.provider == CloudProvider.GCP:
                return await self.gcp_client.get_cost(resource.resource_id)
            else:
                raise UnsupportedProviderError(
                    f"Unsupported provider: {resource.provider}",
                    resource.provider.value
                )
        except Exception as e:
            raise CostCalculationError(
                f"Failed to get resource cost: {str(e)}",
                resource_id=resource.resource_id,
                calculation_type="current",
                details={"original_error": str(e)}
            ) from e

    async def _generate_recommendation(
        self,
        analysis: ResourceAnalysis,
        optimization_type: OptimizationType,
        min_savings_amount: Optional[Decimal],
        min_savings_percentage: Optional[float],
    ) -> Optional[OptimizationRecommendation]:
        """Generate a single optimization recommendation."""
        try:
            # Generate recommendation based on optimization type
            if optimization_type == OptimizationType.RIGHTSIZING:
                return await self._generate_rightsizing_recommendation(analysis)
            elif optimization_type == OptimizationType.SCHEDULING:
                return await self._generate_scheduling_recommendation(analysis)
            # Add other optimization types...

        except Exception as e:
            logger.error(
                f"Error generating {optimization_type.value} recommendation for "
                f"{analysis.resource.resource_id}: {str(e)}"
            )
            return None

    async def _apply_optimization(
        self,
        recommendation: OptimizationRecommendation
    ) -> Dict[str, Any]:
        """Apply an optimization to a resource."""
        # TODO: Implement optimization application
        raise NotImplementedError("Optimization application not yet implemented")

    def _is_valid_cron(self, expression: str) -> bool:
        """Validate a cron expression."""
        # TODO: Implement cron expression validation
        return True

    def _calculate_total_savings(
        self,
        recommendations: List[OptimizationRecommendation]
    ) -> ResourceCost:
        """Calculate total potential savings."""
        total_hourly = sum(r.estimated_savings.hourly_cost for r in recommendations)
        total_monthly = sum(r.estimated_savings.monthly_cost for r in recommendations)
        return ResourceCost(
            hourly_cost=total_hourly,
            monthly_cost=total_monthly,
            currency=self.default_currency
        )

    def _group_recommendations_by_type(
        self,
        recommendations: List[OptimizationRecommendation]
    ) -> Dict[OptimizationType, int]:
        """Group recommendations by optimization type."""
        groups = {}
        for r in recommendations:
            groups[r.optimization_type] = groups.get(r.optimization_type, 0) + 1
        return groups

    def _group_recommendations_by_severity(
        self,
        recommendations: List[OptimizationRecommendation]
    ) -> Dict[SeverityLevel, int]:
        """Group recommendations by severity level."""
        groups = {}
        for r in recommendations:
            groups[r.severity] = groups.get(r.severity, 0) + 1
        return groups

    def _group_savings_by_provider(
        self,
        recommendations: List[OptimizationRecommendation]
    ) -> Dict[CloudProvider, ResourceCost]:
        """Group potential savings by provider."""
        savings = {}
        for r in recommendations:
            if r.provider not in savings:
                savings[r.provider] = ResourceCost(
                    hourly_cost=Decimal("0"),
                    monthly_cost=Decimal("0"),
                    currency=self.default_currency
                )
            savings[r.provider].hourly_cost += r.estimated_savings.hourly_cost
            savings[r.provider].monthly_cost += r.estimated_savings.monthly_cost
        return savings

    async def _run_compliance_checks(
        self,
        analyses: List[ResourceAnalysis],
        recommendations: List[OptimizationRecommendation]
    ) -> List[ComplianceCheck]:
        """Run compliance checks on analyses and recommendations."""
        # TODO: Implement compliance checks
        return []

    async def _get_optimization_events(
        self,
        time_period: str
    ) -> List[OptimizationEvent]:
        """Get optimization-related events."""
        # TODO: Implement event retrieval
        return []
