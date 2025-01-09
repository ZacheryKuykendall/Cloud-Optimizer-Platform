"""Tests for the cloud cost optimizer."""

from datetime import datetime
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cloud_cost_optimizer.exceptions import (
    ConfigurationError,
    CostCalculationError,
    MetricsCollectionError,
    OptimizationApplicationError,
    PolicyValidationError,
    ResourceNotFoundError,
    UnsupportedProviderError,
    ValidationError,
)
from cloud_cost_optimizer.models import (
    CloudProvider,
    OptimizationPolicy,
    OptimizationRecommendation,
    OptimizationType,
    ResourceAnalysis,
    ResourceConfiguration,
    ResourceCost,
    ResourceMetrics,
    ResourceType,
    ResourceUsagePattern,
    SeverityLevel,
)
from cloud_cost_optimizer.optimizer import CloudCostOptimizer


@pytest.fixture
def aws_credentials():
    """Sample AWS credentials."""
    return {
        "aws_access_key_id": "test-key",
        "aws_secret_access_key": "test-secret",
        "region": "us-east-1"
    }


@pytest.fixture
def azure_credentials():
    """Sample Azure credentials."""
    return {
        "subscription_id": "test-sub",
        "tenant_id": "test-tenant",
        "client_id": "test-client",
        "client_secret": "test-secret"
    }


@pytest.fixture
def gcp_credentials():
    """Sample GCP credentials."""
    return {
        "project_id": "test-project",
        "credentials_path": "/path/to/credentials.json"
    }


@pytest.fixture
def optimizer(aws_credentials, azure_credentials, gcp_credentials):
    """Create a CloudCostOptimizer instance with mock clients."""
    with patch("aws_cost_explorer.AWSCostExplorerClient"), \
         patch("azure_cost_management.AzureCostManagementClient"), \
         patch("gcp_billing.GCPBillingClient"):
        return CloudCostOptimizer(
            aws_credentials=aws_credentials,
            azure_credentials=azure_credentials,
            gcp_credentials=gcp_credentials
        )


@pytest.fixture
def resource_config():
    """Sample resource configuration."""
    return ResourceConfiguration(
        provider=CloudProvider.AWS,
        resource_type=ResourceType.COMPUTE,
        resource_id="i-1234567890abcdef0",
        name="test-instance",
        region="us-east-1",
        specifications={
            "instance_type": "t3.micro",
            "vcpu": "2",
            "memory": "1GB"
        },
        created_at=datetime.utcnow()
    )


@pytest.fixture
def resource_metrics():
    """Sample resource metrics."""
    return ResourceMetrics(
        cpu_utilization=25.5,
        memory_utilization=45.2,
        disk_iops=100.0,
        network_in=1024.0,
        network_out=2048.0
    )


@pytest.fixture
def resource_cost():
    """Sample resource cost."""
    return ResourceCost(
        hourly_cost=Decimal("0.10"),
        monthly_cost=Decimal("73.00"),
        currency="USD"
    )


def test_initialization(aws_credentials, azure_credentials, gcp_credentials):
    """Test optimizer initialization."""
    # Test with all providers
    optimizer = CloudCostOptimizer(
        aws_credentials=aws_credentials,
        azure_credentials=azure_credentials,
        gcp_credentials=gcp_credentials
    )
    assert CloudProvider.AWS in optimizer.providers
    assert CloudProvider.AZURE in optimizer.providers
    assert CloudProvider.GCP in optimizer.providers
    assert optimizer.default_currency == "USD"

    # Test with subset of providers
    optimizer = CloudCostOptimizer(aws_credentials=aws_credentials)
    assert CloudProvider.AWS in optimizer.providers
    assert CloudProvider.AZURE not in optimizer.providers
    assert CloudProvider.GCP not in optimizer.providers

    # Test with no providers
    with pytest.raises(ConfigurationError):
        CloudCostOptimizer()

    # Test with custom currency
    optimizer = CloudCostOptimizer(
        aws_credentials=aws_credentials,
        default_currency="EUR"
    )
    assert optimizer.default_currency == "EUR"


@pytest.mark.asyncio
async def test_analyze_resources(optimizer, resource_config, resource_metrics, resource_cost):
    """Test resource analysis."""
    # Mock provider methods
    optimizer.aws_client.get_resources = AsyncMock(return_value=[resource_config])
    optimizer.aws_client.get_metrics = AsyncMock(return_value=resource_metrics)
    optimizer.aws_client.get_cost = AsyncMock(return_value=resource_cost)

    # Test successful analysis
    analyses = await optimizer.analyze_resources(
        providers=[CloudProvider.AWS],
        include_metrics=True,
        include_costs=True
    )
    assert len(analyses) == 1
    
    analysis = analyses[0]
    assert isinstance(analysis, ResourceAnalysis)
    assert analysis.resource == resource_config
    assert analysis.metrics == resource_metrics
    assert analysis.current_cost == resource_cost

    # Test with unsupported provider
    with pytest.raises(ValidationError):
        await optimizer.analyze_resources(providers=["unknown"])

    # Test with resource not found
    optimizer.aws_client.get_resources.side_effect = ResourceNotFoundError(
        "Resource not found",
        provider="aws",
        resource_id="test"
    )
    analyses = await optimizer.analyze_resources(providers=[CloudProvider.AWS])
    assert len(analyses) == 0


@pytest.mark.asyncio
async def test_generate_recommendations(optimizer, resource_config, resource_metrics, resource_cost):
    """Test recommendation generation."""
    analysis = ResourceAnalysis(
        resource=resource_config,
        metrics=resource_metrics,
        current_cost=resource_cost,
        last_analyzed=datetime.utcnow()
    )

    # Test recommendation generation
    recommendations = await optimizer.generate_recommendations(
        analyses=[analysis],
        optimization_types=[OptimizationType.RIGHTSIZING],
        min_savings_amount=Decimal("10.00"),
        min_savings_percentage=20.0
    )

    # Since _generate_recommendation is not implemented, this should return empty list
    assert len(recommendations) == 0


@pytest.mark.asyncio
async def test_apply_recommendation(optimizer):
    """Test recommendation application."""
    recommendation = OptimizationRecommendation(
        id="rec-123",
        resource_id="i-1234567890abcdef0",
        resource_type=ResourceType.COMPUTE,
        provider=CloudProvider.AWS,
        optimization_type=OptimizationType.RIGHTSIZING,
        severity=SeverityLevel.HIGH,
        current_cost=ResourceCost(
            hourly_cost=Decimal("0.10"),
            monthly_cost=Decimal("73.00")
        ),
        estimated_savings=ResourceCost(
            hourly_cost=Decimal("0.05"),
            monthly_cost=Decimal("36.50")
        ),
        implementation_effort="low",
        risk_level="low",
        description="Rightsize instance",
        justification="Instance is underutilized",
        action_items=["Change instance type to t3.nano"]
    )

    # Test dry run
    result = await optimizer.apply_recommendation(recommendation, dry_run=True)
    assert result.status == "simulated"
    assert result.actual_savings == recommendation.estimated_savings

    # Test actual application (should raise NotImplementedError)
    with pytest.raises(NotImplementedError):
        await optimizer.apply_recommendation(recommendation, dry_run=False)


@pytest.mark.asyncio
async def test_validate_policy(optimizer):
    """Test policy validation."""
    # Test valid policy
    policy = OptimizationPolicy(
        id="policy-123",
        name="Test Policy",
        description="Test optimization policy",
        resource_types={ResourceType.COMPUTE},
        providers={CloudProvider.AWS},
        optimization_types={OptimizationType.RIGHTSIZING}
    )
    is_valid, errors = await optimizer.validate_policy(policy)
    assert is_valid
    assert not errors

    # Test invalid policy (no resource types)
    policy.resource_types = set()
    is_valid, errors = await optimizer.validate_policy(policy)
    assert not is_valid
    assert len(errors) == 1
    assert errors[0]["field"] == "resource_types"

    # Test invalid policy (unsupported provider)
    policy.resource_types = {ResourceType.COMPUTE}
    policy.providers = {CloudProvider.GCP}  # Assuming optimizer only has AWS configured
    is_valid, errors = await optimizer.validate_policy(policy)
    assert not is_valid
    assert len(errors) == 1
    assert errors[0]["field"] == "providers"


@pytest.mark.asyncio
async def test_generate_report(optimizer, resource_config, resource_metrics, resource_cost):
    """Test report generation."""
    analysis = ResourceAnalysis(
        resource=resource_config,
        metrics=resource_metrics,
        current_cost=resource_cost,
        last_analyzed=datetime.utcnow()
    )

    recommendation = OptimizationRecommendation(
        id="rec-123",
        resource_id=resource_config.resource_id,
        resource_type=resource_config.resource_type,
        provider=resource_config.provider,
        optimization_type=OptimizationType.RIGHTSIZING,
        severity=SeverityLevel.HIGH,
        current_cost=resource_cost,
        estimated_savings=ResourceCost(
            hourly_cost=Decimal("0.05"),
            monthly_cost=Decimal("36.50")
        ),
        implementation_effort="low",
        risk_level="low",
        description="Rightsize instance",
        justification="Instance is underutilized",
        action_items=["Change instance type to t3.nano"]
    )

    report = await optimizer.generate_report(
        analyses=[analysis],
        recommendations=[recommendation],
        applied_optimizations=[],
        time_period="last-30-days"
    )

    assert report.summary.total_resources_analyzed == 1
    assert report.summary.total_recommendations == 1
    assert report.summary.total_potential_savings.monthly_cost == Decimal("36.50")
    assert len(report.resource_analyses) == 1
    assert len(report.compliance_checks) == 0  # Not implemented yet
    assert len(report.events) == 0  # Not implemented yet


def test_calculate_total_savings(optimizer):
    """Test savings calculation."""
    recommendations = [
        OptimizationRecommendation(
            id="rec-1",
            resource_id="res-1",
            resource_type=ResourceType.COMPUTE,
            provider=CloudProvider.AWS,
            optimization_type=OptimizationType.RIGHTSIZING,
            severity=SeverityLevel.HIGH,
            current_cost=ResourceCost(
                hourly_cost=Decimal("0.10"),
                monthly_cost=Decimal("73.00")
            ),
            estimated_savings=ResourceCost(
                hourly_cost=Decimal("0.05"),
                monthly_cost=Decimal("36.50")
            ),
            implementation_effort="low",
            risk_level="low",
            description="Test recommendation 1",
            justification="Test justification 1",
            action_items=["Action 1"]
        ),
        OptimizationRecommendation(
            id="rec-2",
            resource_id="res-2",
            resource_type=ResourceType.STORAGE,
            provider=CloudProvider.AWS,
            optimization_type=OptimizationType.STORAGE_TIER,
            severity=SeverityLevel.MEDIUM,
            current_cost=ResourceCost(
                hourly_cost=Decimal("0.20"),
                monthly_cost=Decimal("146.00")
            ),
            estimated_savings=ResourceCost(
                hourly_cost=Decimal("0.10"),
                monthly_cost=Decimal("73.00")
            ),
            implementation_effort="medium",
            risk_level="low",
            description="Test recommendation 2",
            justification="Test justification 2",
            action_items=["Action 2"]
        )
    ]

    total_savings = optimizer._calculate_total_savings(recommendations)
    assert total_savings.hourly_cost == Decimal("0.15")  # 0.05 + 0.10
    assert total_savings.monthly_cost == Decimal("109.50")  # 36.50 + 73.00


def test_group_recommendations(optimizer):
    """Test recommendation grouping."""
    recommendations = [
        OptimizationRecommendation(
            id="rec-1",
            resource_id="res-1",
            resource_type=ResourceType.COMPUTE,
            provider=CloudProvider.AWS,
            optimization_type=OptimizationType.RIGHTSIZING,
            severity=SeverityLevel.HIGH,
            current_cost=ResourceCost(
                hourly_cost=Decimal("0.10"),
                monthly_cost=Decimal("73.00")
            ),
            estimated_savings=ResourceCost(
                hourly_cost=Decimal("0.05"),
                monthly_cost=Decimal("36.50")
            ),
            implementation_effort="low",
            risk_level="low",
            description="Test recommendation 1",
            justification="Test justification 1",
            action_items=["Action 1"]
        ),
        OptimizationRecommendation(
            id="rec-2",
            resource_id="res-2",
            resource_type=ResourceType.COMPUTE,
            provider=CloudProvider.AWS,
            optimization_type=OptimizationType.RIGHTSIZING,
            severity=SeverityLevel.MEDIUM,
            current_cost=ResourceCost(
                hourly_cost=Decimal("0.20"),
                monthly_cost=Decimal("146.00")
            ),
            estimated_savings=ResourceCost(
                hourly_cost=Decimal("0.10"),
                monthly_cost=Decimal("73.00")
            ),
            implementation_effort="medium",
            risk_level="low",
            description="Test recommendation 2",
            justification="Test justification 2",
            action_items=["Action 2"]
        )
    ]

    # Test grouping by type
    by_type = optimizer._group_recommendations_by_type(recommendations)
    assert by_type[OptimizationType.RIGHTSIZING] == 2

    # Test grouping by severity
    by_severity = optimizer._group_recommendations_by_severity(recommendations)
    assert by_severity[SeverityLevel.HIGH] == 1
    assert by_severity[SeverityLevel.MEDIUM] == 1

    # Test grouping savings by provider
    by_provider = optimizer._group_savings_by_provider(recommendations)
    assert by_provider[CloudProvider.AWS].monthly_cost == Decimal("109.50")
