# Cloud Budget Manager

A Python library for managing cloud budgets, spending alerts, and cost forecasting across multiple cloud providers (AWS, Azure, GCP). This service provides centralized budget management with support for spending tracking, alerts, and cost forecasting.

## Features

- **Multi-Cloud Support**: Track and manage budgets across AWS, Azure, and GCP
- **Budget Management**: Create, update, and delete budgets with flexible filtering
- **Spending Alerts**: Configure and manage spending thresholds and alerts
- **Cost Forecasting**: Generate spending forecasts using machine learning
- **Budget Analytics**: Track spending patterns and trends
- **Flexible Querying**: Search and filter budgets using various criteria
- **Type Safety**: Full type hints and Pydantic models for reliable data handling
- **Async Support**: Asynchronous operations for better performance
- **Extensible**: Easy to add support for additional cloud providers

## Installation

```bash
pip install cloud-budget-manager
```

## Requirements

- Python 3.9+
- Dependencies:
  - pydantic>=2.0.0
  - boto3>=1.26.0
  - azure-mgmt-consumption>=10.0.0
  - azure-identity>=1.12.0
  - google-cloud-billing>=1.9.0
  - google-auth>=2.22.0
  - aiohttp>=3.8.0
  - pandas>=2.0.0
  - numpy>=1.24.0
  - scikit-learn>=1.3.0

## Quick Start

```python
from datetime import datetime
from decimal import Decimal
from cloud_budget_manager import (
    BudgetManager,
    Budget,
    BudgetFilter,
    BudgetPeriod,
    CloudProvider,
)

# Initialize manager with cloud credentials
manager = BudgetManager(
    aws_credentials={
        "aws_access_key_id": "your-key",
        "aws_secret_access_key": "your-secret",
        "region": "us-east-1"
    },
    azure_credentials={
        "subscription_id": "your-sub",
        "tenant_id": "your-tenant",
        "client_id": "your-client",
        "client_secret": "your-secret"
    }
)

# Create a budget
budget = await manager.create_budget(
    Budget(
        id="dev-budget-2023",
        name="Development Budget 2023",
        description="Budget for development resources",
        amount=Decimal("10000.00"),
        currency="USD",
        period=BudgetPeriod.MONTHLY,
        start_date=datetime.utcnow(),
        filters=BudgetFilter(
            providers={CloudProvider.AWS, CloudProvider.AZURE},
            categories={"compute", "storage"},
            tags={"env": "dev", "team": "platform"}
        ),
        thresholds=[
            {"percentage": 80, "amount": Decimal("8000.00")},
            {"percentage": 100, "amount": Decimal("10000.00")}
        ],
        created_by="admin"
    )
)

# Get budget summary
summary = await manager.get_summary(budget.id)
print(f"Current spend: ${summary.current_spend}")
print(f"Remaining budget: ${summary.remaining_budget}")
print(f"Percentage used: {summary.percentage_used}%")

# Get spending forecast
forecast = await manager.get_forecast(budget.id)
print(f"Forecasted amount: ${forecast.forecasted_amount}")
print(f"Trend: {forecast.trend}")
print(f"Accuracy: {forecast.accuracy}")

# Get active alerts
alerts = await manager.get_alerts(budget.id, status="active")
for alert in alerts:
    print(f"Alert: {alert.message}")
    print(f"Severity: {alert.severity}")
    print(f"Threshold: {alert.threshold}%")
```

## Usage Examples

### Budget Creation

```python
# Create a budget with custom thresholds
budget = await manager.create_budget(
    Budget(
        id="prod-budget-2023",
        name="Production Budget 2023",
        amount=Decimal("50000.00"),
        period=BudgetPeriod.MONTHLY,
        start_date=datetime.utcnow(),
        filters=BudgetFilter(
            providers={CloudProvider.AWS},
            categories={"compute", "database"},
            regions={"us-east-1", "us-west-2"}
        ),
        thresholds=[
            {"percentage": 50, "amount": Decimal("25000.00")},
            {"percentage": 80, "amount": Decimal("40000.00")},
            {"percentage": 100, "amount": Decimal("50000.00")}
        ],
        created_by="admin"
    )
)
```

### Budget Querying

```python
# Query budgets by criteria
budgets = await manager.query_budgets(
    BudgetQuery(
        providers=[CloudProvider.AWS],
        min_amount=Decimal("10000.00"),
        max_amount=Decimal("50000.00"),
        period=BudgetPeriod.MONTHLY,
        tags={"env": "prod"},
        has_alerts=True
    )
)
```

### Alert Management

```python
# Get and update alerts
alerts = await manager.get_alerts(budget_id)
for alert in alerts:
    if alert.severity == AlertSeverity.HIGH:
        # Acknowledge high severity alert
        await manager.update_alert(
            budget_id=budget_id,
            alert_id=alert.id,
            status=AlertStatus.ACKNOWLEDGED,
            notes="Investigating high spend"
        )
```

### Cost Forecasting

```python
# Generate forecast with custom period
forecast = await manager.get_forecast(
    budget_id=budget_id,
    period=BudgetPeriod.QUARTERLY
)

print(f"Forecasted amount: ${forecast.forecasted_amount}")
print(f"Confidence interval: ${forecast.confidence_interval}")
print(f"Contributing factors:")
for factor in forecast.contributing_factors:
    print(f"- {factor}")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-budget-manager.git
cd cloud-budget-manager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_manager.py
```

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy .

# Linting
pylint src tests
```

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
