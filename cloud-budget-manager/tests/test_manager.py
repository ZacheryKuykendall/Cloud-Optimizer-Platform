"""Tests for the cloud budget manager."""

from datetime import datetime, timedelta
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cloud_budget_manager.exceptions import (
    AlertNotFoundError,
    AlertUpdateError,
    BudgetAlreadyExistsError,
    BudgetDeletionError,
    BudgetNotFoundError,
    BudgetUpdateError,
    InsufficientDataError,
    InvalidQueryError,
    ValidationError,
)
from cloud_budget_manager.manager import BudgetManager
from cloud_budget_manager.models import (
    AlertSeverity,
    AlertStatus,
    Budget,
    BudgetFilter,
    BudgetPeriod,
    BudgetQuery,
    CloudProvider,
    ForecastAccuracy,
    SpendingAlert,
    SpendingForecast,
    SpendingTrend,
)


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
def budget_manager(aws_credentials, azure_credentials, gcp_credentials):
    """Create a BudgetManager instance with mock clients."""
    with patch("cloud_budget_manager.manager.BudgetManager._init_aws_client"), \
         patch("cloud_budget_manager.manager.BudgetManager._init_azure_client"), \
         patch("cloud_budget_manager.manager.BudgetManager._init_gcp_client"):
        return BudgetManager(
            aws_credentials=aws_credentials,
            azure_credentials=azure_credentials,
            gcp_credentials=gcp_credentials
        )


@pytest.fixture
def sample_budget():
    """Create a sample budget."""
    return Budget(
        id="budget-123",
        name="Test Budget",
        description="Test budget for development",
        amount=Decimal("1000.00"),
        currency="USD",
        period=BudgetPeriod.MONTHLY,
        start_date=datetime.utcnow(),
        filters=BudgetFilter(
            providers={CloudProvider.AWS},
            categories={"compute", "storage"}
        ),
        thresholds=[
            {"percentage": 80, "amount": Decimal("800.00")},
            {"percentage": 100, "amount": Decimal("1000.00")}
        ],
        created_by="test-user"
    )


def test_initialization(aws_credentials, azure_credentials, gcp_credentials):
    """Test manager initialization."""
    # Test with all providers
    manager = BudgetManager(
        aws_credentials=aws_credentials,
        azure_credentials=azure_credentials,
        gcp_credentials=gcp_credentials
    )
    assert CloudProvider.AWS in manager.providers
    assert CloudProvider.AZURE in manager.providers
    assert CloudProvider.GCP in manager.providers
    assert manager.default_currency == "USD"

    # Test with subset of providers
    manager = BudgetManager(aws_credentials=aws_credentials)
    assert CloudProvider.AWS in manager.providers
    assert CloudProvider.AZURE not in manager.providers
    assert CloudProvider.GCP not in manager.providers

    # Test with no providers
    with pytest.raises(ValidationError):
        BudgetManager()

    # Test with custom settings
    manager = BudgetManager(
        aws_credentials=aws_credentials,
        default_currency="EUR",
        alert_buffer_percentage=10.0,
        forecast_data_points=60
    )
    assert manager.default_currency == "EUR"
    assert manager.alert_buffer_percentage == 10.0
    assert manager.forecast_data_points == 60


@pytest.mark.asyncio
async def test_create_budget(budget_manager, sample_budget):
    """Test budget creation."""
    # Test successful creation
    budget = await budget_manager.create_budget(sample_budget)
    assert budget.id == sample_budget.id
    assert budget.name == sample_budget.name
    assert budget.amount == sample_budget.amount
    assert budget.id in budget_manager.state.budgets
    assert budget.id in budget_manager.state.alerts

    # Test duplicate budget
    with pytest.raises(BudgetAlreadyExistsError):
        await budget_manager.create_budget(sample_budget)


@pytest.mark.asyncio
async def test_get_budget(budget_manager, sample_budget):
    """Test budget retrieval."""
    # Add budget to state
    budget_manager.state.budgets[sample_budget.id] = sample_budget

    # Test successful retrieval
    budget = await budget_manager.get_budget(sample_budget.id)
    assert budget.id == sample_budget.id
    assert budget.name == sample_budget.name

    # Test non-existent budget
    with pytest.raises(BudgetNotFoundError):
        await budget_manager.get_budget("non-existent")


@pytest.mark.asyncio
async def test_update_budget(budget_manager, sample_budget):
    """Test budget updates."""
    # Add budget to state
    budget_manager.state.budgets[sample_budget.id] = sample_budget

    # Test successful update
    updates = {
        "name": "Updated Budget",
        "amount": Decimal("2000.00")
    }
    updated = await budget_manager.update_budget(sample_budget.id, updates)
    assert updated.name == "Updated Budget"
    assert updated.amount == Decimal("2000.00")

    # Test non-existent budget
    with pytest.raises(BudgetNotFoundError):
        await budget_manager.update_budget("non-existent", updates)


@pytest.mark.asyncio
async def test_delete_budget(budget_manager, sample_budget):
    """Test budget deletion."""
    # Add budget to state
    budget_manager.state.budgets[sample_budget.id] = sample_budget
    budget_manager.state.alerts[sample_budget.id] = []

    # Test successful deletion
    await budget_manager.delete_budget(sample_budget.id)
    assert sample_budget.id not in budget_manager.state.budgets
    assert sample_budget.id not in budget_manager.state.alerts

    # Test non-existent budget
    with pytest.raises(BudgetNotFoundError):
        await budget_manager.delete_budget("non-existent")


@pytest.mark.asyncio
async def test_get_alerts(budget_manager, sample_budget):
    """Test alert retrieval."""
    # Add budget and alerts to state
    budget_manager.state.budgets[sample_budget.id] = sample_budget
    budget_manager.state.alerts[sample_budget.id] = [
        SpendingAlert(
            id="alert-1",
            budget_id=sample_budget.id,
            threshold=80.0,
            actual_spend=Decimal("800.00"),
            severity=AlertSeverity.MEDIUM,
            status=AlertStatus.ACTIVE,
            message="80% threshold reached"
        ),
        SpendingAlert(
            id="alert-2",
            budget_id=sample_budget.id,
            threshold=100.0,
            actual_spend=Decimal("1000.00"),
            severity=AlertSeverity.HIGH,
            status=AlertStatus.ACKNOWLEDGED,
            message="Budget exceeded"
        )
    ]

    # Test all alerts
    alerts = await budget_manager.get_alerts(sample_budget.id)
    assert len(alerts) == 2

    # Test filtered alerts
    active_alerts = await budget_manager.get_alerts(
        sample_budget.id,
        status=AlertStatus.ACTIVE
    )
    assert len(active_alerts) == 1
    assert active_alerts[0].status == AlertStatus.ACTIVE


@pytest.mark.asyncio
async def test_update_alert(budget_manager, sample_budget):
    """Test alert updates."""
    # Add budget and alert to state
    budget_manager.state.budgets[sample_budget.id] = sample_budget
    alert = SpendingAlert(
        id="alert-1",
        budget_id=sample_budget.id,
        threshold=80.0,
        actual_spend=Decimal("800.00"),
        severity=AlertSeverity.MEDIUM,
        status=AlertStatus.ACTIVE,
        message="80% threshold reached"
    )
    budget_manager.state.alerts[sample_budget.id] = [alert]

    # Test successful update
    updated = await budget_manager.update_alert(
        budget_id=sample_budget.id,
        alert_id=alert.id,
        status=AlertStatus.ACKNOWLEDGED,
        notes="Investigating"
    )
    assert updated.status == AlertStatus.ACKNOWLEDGED
    assert updated.resolution_notes == "Investigating"

    # Test non-existent alert
    with pytest.raises(AlertNotFoundError):
        await budget_manager.update_alert(
            budget_id=sample_budget.id,
            alert_id="non-existent",
            status=AlertStatus.ACKNOWLEDGED
        )


@pytest.mark.asyncio
async def test_get_forecast(budget_manager, sample_budget):
    """Test forecast generation."""
    # Add budget to state
    budget_manager.state.budgets[sample_budget.id] = sample_budget

    # Mock historical spending data
    spending_data = [
        (datetime.utcnow() - timedelta(days=i), Decimal(f"{i * 10}.00"))
        for i in range(30)
    ]
    budget_manager._get_historical_spending = AsyncMock(return_value=spending_data)

    # Test successful forecast
    forecast = await budget_manager.get_forecast(sample_budget.id)
    assert isinstance(forecast, SpendingForecast)
    assert forecast.accuracy in ForecastAccuracy
    assert forecast.trend in SpendingTrend

    # Test insufficient data
    budget_manager._get_historical_spending = AsyncMock(return_value=[])
    with pytest.raises(InsufficientDataError):
        await budget_manager.get_forecast(sample_budget.id)


@pytest.mark.asyncio
async def test_query_budgets(budget_manager):
    """Test budget querying."""
    # Add test budgets
    budgets = [
        Budget(
            id="budget-1",
            name="AWS Dev Budget",
            amount=Decimal("1000.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.utcnow(),
            filters=BudgetFilter(
                providers={CloudProvider.AWS},
                categories={"compute"}
            ),
            thresholds=[{"percentage": 100, "amount": Decimal("1000.00")}],
            created_by="test-user"
        ),
        Budget(
            id="budget-2",
            name="Azure Prod Budget",
            amount=Decimal("5000.00"),
            period=BudgetPeriod.MONTHLY,
            start_date=datetime.utcnow(),
            filters=BudgetFilter(
                providers={CloudProvider.AZURE},
                categories={"compute", "storage"}
            ),
            thresholds=[{"percentage": 100, "amount": Decimal("5000.00")}],
            created_by="test-user"
        )
    ]
    for budget in budgets:
        budget_manager.state.budgets[budget.id] = budget

    # Test query by provider
    query = BudgetQuery(providers=[CloudProvider.AWS])
    results = await budget_manager.query_budgets(query)
    assert len(results) == 1
    assert results[0].filters.providers == {CloudProvider.AWS}

    # Test query by amount range
    query = BudgetQuery(
        min_amount=Decimal("2000.00"),
        max_amount=Decimal("6000.00")
    )
    results = await budget_manager.query_budgets(query)
    assert len(results) == 1
    assert results[0].amount == Decimal("5000.00")

    # Test query with multiple criteria
    query = BudgetQuery(
        providers=[CloudProvider.AZURE],
        min_amount=Decimal("1000.00"),
        period=BudgetPeriod.MONTHLY
    )
    results = await budget_manager.query_budgets(query)
    assert len(results) == 1
    assert results[0].filters.providers == {CloudProvider.AZURE}
    assert results[0].period == BudgetPeriod.MONTHLY

    # Test query with no matches
    query = BudgetQuery(providers=[CloudProvider.GCP])
    results = await budget_manager.query_budgets(query)
    assert len(results) == 0
