"""Tests for the Terraform cost analyzer."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from terraform_cost_analyzer.analyzer import TerraformCostAnalyzer
from terraform_cost_analyzer.exceptions import (
    ConfigurationError,
    PricingCalculationError,
    PricingDataNotFoundError,
    ValidationError,
)
from terraform_cost_analyzer.models import (
    CloudProvider,
    CostAnalysis,
    CostBreakdown,
    CostComponent,
    CostSummary,
    ModuleCost,
    PricingData,
    ResourceAction,
    ResourceCost,
    ResourceMetadata,
    ResourceType,
    PricingTier,
)


@pytest.fixture
def mock_aws_client():
    """Create a mock AWS Cost Explorer client."""
    client = AsyncMock()
    client.get_pricing_data = AsyncMock()
    return client


@pytest.fixture
def mock_azure_client():
    """Create a mock Azure Cost Management client."""
    client = AsyncMock()
    client.get_pricing_data = AsyncMock()
    return client


@pytest.fixture
def mock_gcp_client():
    """Create a mock GCP Billing client."""
    client = AsyncMock()
    client.get_pricing_data = AsyncMock()
    return client


@pytest.fixture
def analyzer(mock_aws_client, mock_azure_client, mock_gcp_client):
    """Create a TerraformCostAnalyzer instance with mock clients."""
    return TerraformCostAnalyzer(
        aws_client=mock_aws_client,
        azure_client=mock_azure_client,
        gcp_client=mock_gcp_client
    )


@pytest.fixture
def mock_pricing_data():
    """Create sample pricing data."""
    return {
        (CloudProvider.AWS, "us-east-1"): [
            PricingData(
                provider=CloudProvider.AWS,
                resource_type="aws_instance",
                region="us-east-1",
                pricing_tier=PricingTier.ON_DEMAND,
                unit_price=Decimal("0.10"),
                unit="hour",
                currency="USD",
                effective_date=datetime.utcnow(),
                metadata={"instance_type": "t3.micro"}
            )
        ],
        (CloudProvider.AZURE, "eastus"): [
            PricingData(
                provider=CloudProvider.AZURE,
                resource_type="azurerm_virtual_machine",
                region="eastus",
                pricing_tier=PricingTier.ON_DEMAND,
                unit_price=Decimal("0.12"),
                unit="hour",
                currency="USD",
                effective_date=datetime.utcnow(),
                metadata={"size": "Standard_B2s"}
            )
        ],
        (CloudProvider.GCP, "us-central1"): [
            PricingData(
                provider=CloudProvider.GCP,
                resource_type="google_compute_instance",
                region="us-central1",
                pricing_tier=PricingTier.ON_DEMAND,
                unit_price=Decimal("0.11"),
                unit="hour",
                currency="USD",
                effective_date=datetime.utcnow(),
                metadata={"machine_type": "n1-standard-1"}
            )
        ]
    }


def test_initialization():
    """Test analyzer initialization."""
    # Test with no clients
    with pytest.raises(ConfigurationError):
        TerraformCostAnalyzer(providers=[CloudProvider.AWS])

    # Test with required client
    analyzer = TerraformCostAnalyzer(
        providers=[CloudProvider.AWS],
        aws_client=AsyncMock()
    )
    assert CloudProvider.AWS in analyzer.providers
    assert analyzer.default_currency == "USD"

    # Test with custom currency
    analyzer = TerraformCostAnalyzer(
        aws_client=AsyncMock(),
        default_currency="EUR"
    )
    assert analyzer.default_currency == "EUR"


@pytest.mark.asyncio
async def test_analyze_plan(analyzer, mock_pricing_data):
    """Test plan analysis."""
    # Mock parser methods
    analyzer.parser.parse_plan_file = MagicMock()
    analyzer.parser.extract_resources = MagicMock(return_value=[
        (
            ResourceMetadata(
                provider=CloudProvider.AWS,
                type="aws_instance",
                name="example",
                normalized_type=ResourceType.COMPUTE,
                region="us-east-1",
                pricing_tier=PricingTier.ON_DEMAND,
                specifications={"instance_type": "t3.micro"}
            ),
            ResourceAction.CREATE
        )
    ])
    analyzer.parser.extract_modules = MagicMock(return_value={"module.example"})
    analyzer.parser.extract_providers = MagicMock(return_value={CloudProvider.AWS})
    analyzer.parser.extract_regions = MagicMock(return_value={
        CloudProvider.AWS: {"us-east-1"}
    })

    # Mock pricing data retrieval
    analyzer._get_pricing_data = AsyncMock(return_value=mock_pricing_data)

    # Test analysis
    analysis = await analyzer.analyze_plan("test.tfplan")
    assert isinstance(analysis, CostAnalysis)
    assert len(analysis.resources) == 1
    assert len(analysis.modules) == 1
    assert analysis.summary.total_resources == 1
    assert analysis.summary.resources_to_add == 1


@pytest.mark.asyncio
async def test_get_pricing_data(analyzer, mock_pricing_data):
    """Test pricing data retrieval."""
    # Mock client responses
    analyzer.aws_client.get_pricing_data.return_value = mock_pricing_data[
        (CloudProvider.AWS, "us-east-1")
    ]
    analyzer.azure_client.get_pricing_data.return_value = mock_pricing_data[
        (CloudProvider.AZURE, "eastus")
    ]
    analyzer.gcp_client.get_pricing_data.return_value = mock_pricing_data[
        (CloudProvider.GCP, "us-central1")
    ]

    # Test retrieval
    providers = {CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP}
    regions = {
        CloudProvider.AWS: {"us-east-1"},
        CloudProvider.AZURE: {"eastus"},
        CloudProvider.GCP: {"us-central1"}
    }
    data = await analyzer._get_pricing_data(providers, regions, "USD")

    assert len(data) == 3
    assert (CloudProvider.AWS, "us-east-1") in data
    assert (CloudProvider.AZURE, "eastus") in data
    assert (CloudProvider.GCP, "us-central1") in data


@pytest.mark.asyncio
async def test_calculate_resource_cost(analyzer, mock_pricing_data):
    """Test resource cost calculation."""
    metadata = ResourceMetadata(
        provider=CloudProvider.AWS,
        type="aws_instance",
        name="example",
        normalized_type=ResourceType.COMPUTE,
        region="us-east-1",
        pricing_tier=PricingTier.ON_DEMAND,
        specifications={"instance_type": "t3.micro"}
    )

    cost = await analyzer._calculate_resource_cost(
        metadata=metadata,
        action=ResourceAction.CREATE,
        pricing_data=mock_pricing_data,
        include_previous=False
    )

    assert isinstance(cost, ResourceCost)
    assert cost.hourly_cost == Decimal("0.10")
    assert cost.monthly_cost == Decimal("73.00")  # 0.10 * 730 hours
    assert len(cost.components) == 1
    assert cost.components[0].name == "Base Cost"


def test_calculate_module_cost(analyzer):
    """Test module cost calculation."""
    resources = [
        ResourceCost(
            id="test-1",
            metadata=ResourceMetadata(
                provider=CloudProvider.AWS,
                type="aws_instance",
                name="example1",
                normalized_type=ResourceType.COMPUTE,
                region="us-east-1",
                pricing_tier=PricingTier.ON_DEMAND
            ),
            action=ResourceAction.CREATE,
            hourly_cost=Decimal("0.10"),
            monthly_cost=Decimal("73.00")
        ),
        ResourceCost(
            id="test-2",
            metadata=ResourceMetadata(
                provider=CloudProvider.AWS,
                type="aws_instance",
                name="example2",
                normalized_type=ResourceType.COMPUTE,
                region="us-east-1",
                pricing_tier=PricingTier.ON_DEMAND
            ),
            action=ResourceAction.CREATE,
            hourly_cost=Decimal("0.20"),
            monthly_cost=Decimal("146.00")
        )
    ]

    cost = analyzer._calculate_module_cost(
        name="module.example",
        resources=resources,
        currency="USD"
    )

    assert isinstance(cost, ModuleCost)
    assert cost.hourly_cost == Decimal("0.30")
    assert cost.monthly_cost == Decimal("219.00")
    assert len(cost.resources) == 2


def test_create_summary(analyzer):
    """Test cost summary creation."""
    resources = [
        ResourceCost(
            id="test-1",
            metadata=ResourceMetadata(
                provider=CloudProvider.AWS,
                type="aws_instance",
                name="example1",
                normalized_type=ResourceType.COMPUTE,
                region="us-east-1",
                pricing_tier=PricingTier.ON_DEMAND
            ),
            action=ResourceAction.CREATE,
            hourly_cost=Decimal("0.10"),
            monthly_cost=Decimal("73.00")
        ),
        ResourceCost(
            id="test-2",
            metadata=ResourceMetadata(
                provider=CloudProvider.AWS,
                type="aws_s3_bucket",
                name="example2",
                normalized_type=ResourceType.STORAGE,
                region="us-east-1",
                pricing_tier=PricingTier.ON_DEMAND
            ),
            action=ResourceAction.UPDATE,
            hourly_cost=Decimal("0.02"),
            monthly_cost=Decimal("14.60")
        )
    ]

    summary = analyzer._create_summary(resources, "USD")

    assert isinstance(summary, CostSummary)
    assert summary.total_resources == 2
    assert summary.resources_to_add == 1
    assert summary.resources_to_update == 1
    assert summary.total_hourly_cost == Decimal("0.12")
    assert summary.total_monthly_cost == Decimal("87.60")
    assert summary.breakdown.compute == Decimal("73.00")
    assert summary.breakdown.storage == Decimal("14.60")


@pytest.mark.asyncio
async def test_error_handling(analyzer):
    """Test error handling scenarios."""
    # Test unsupported provider
    analyzer.parser.extract_providers = MagicMock(return_value={
        "unsupported_provider"
    })
    with pytest.raises(ValidationError):
        await analyzer.analyze_plan("test.tfplan")

    # Test pricing data not found
    analyzer.parser.extract_providers = MagicMock(return_value={CloudProvider.AWS})
    analyzer.aws_client.get_pricing_data.side_effect = Exception("API Error")
    with pytest.raises(PricingDataNotFoundError):
        await analyzer.analyze_plan("test.tfplan")

    # Test calculation error
    analyzer._calculate_resource_cost = AsyncMock(
        side_effect=PricingCalculationError(
            "Calculation failed",
            resource_type="test"
        )
    )
    with pytest.raises(PricingCalculationError):
        await analyzer.analyze_plan("test.tfplan")
