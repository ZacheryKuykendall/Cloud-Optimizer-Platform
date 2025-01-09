# Cloud Governance Manager

A Python library for managing cloud governance policies and controls across different providers. This library provides functionality for policy management, access control, and governance monitoring.

## Features

- Policy Management:
  - Policy creation and enforcement
  - Access control policies
  - Resource policies
  - Cost policies
  - Custom policies
  - Policy templates

- Governance Controls:
  - Role-based access control
  - Resource tagging
  - Service restrictions
  - Compliance controls
  - Policy sets

- Governance Monitoring:
  - Policy violations
  - Access reviews
  - Activity monitoring
  - Audit logging
  - Metrics collection

## Installation

```bash
pip install cloud-governance-manager
```

## Prerequisites

- Python 3.8 or higher
- Cloud provider credentials:
  - AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
  - Azure credentials (AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID, etc.)
  - GCP credentials (GOOGLE_APPLICATION_CREDENTIALS)

## Quick Start

### Basic Usage

```python
from cloud_governance_manager import (
    Policy,
    PolicyType,
    PolicyScope,
    PolicyEffect,
    PolicyCondition,
    PolicyAction
)

# Create a policy
policy = Policy(
    name="restrict-instance-types",
    type=PolicyType.RESOURCE,
    scope=PolicyScope.ORGANIZATION,
    effect=PolicyEffect.DENY,
    conditions=[
        PolicyCondition(
            field="resource.type",
            operator="equals",
            value="aws_instance"
        ),
        PolicyCondition(
            field="resource.instance_type",
            operator="not_in",
            value=["t3.micro", "t3.small"]
        )
    ],
    actions=[
        PolicyAction(
            name="notify_admin",
            parameters={
                "channel": "email",
                "recipient": "admin@example.com"
            }
        )
    ]
)

# Apply the policy
governance_manager.apply_policy(policy)
```

### Access Control

```python
from cloud_governance_manager import Role, RolePermission, AccessLevel

# Create a role
role = Role(
    name="developer",
    permissions=[
        RolePermission(
            resource_type="compute",
            access_level=AccessLevel.WRITE,
            conditions=[
                PolicyCondition(
                    field="resource.environment",
                    operator="equals",
                    value="development"
                )
            ]
        )
    ],
    scope=PolicyScope.PROJECT
)

# Assign the role
governance_manager.assign_role(role, "user@example.com")
```

### Governance Monitoring

```python
from cloud_governance_manager import AccessReview, GovernanceReport

# Create access review
review = AccessReview(
    reviewer="security@example.com",
    subject="developer-role",
    scope=PolicyScope.PROJECT,
    status="pending"
)

# Generate governance report
report = governance_manager.generate_report(
    report_type="policy_compliance",
    period_start="2024-01-01",
    period_end="2024-01-31"
)
```

## Architecture

The library consists of several key components:

1. **Policy Engine**:
   - Policy definition
   - Policy evaluation
   - Policy enforcement
   - Template management

2. **Access Control**:
   - Role management
   - Permission evaluation
   - Access reviews
   - Identity management

3. **Governance System**:
   - Control implementation
   - Monitoring
   - Reporting
   - Metrics collection

4. **Provider Integration**:
   - AWS Organizations
   - Azure Management Groups
   - GCP Resource Manager
   - Cross-provider normalization

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cloud-governance-manager.git
cd cloud-governance-manager
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_policies.py
```

### Code Style

The project uses several tools to maintain code quality:

```bash
# Format code
black .

# Sort imports
isort .

# Type checking
mypy src tests

# Linting
pylint src tests
```

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

- [ ] Advanced policy engine
- [ ] Custom control frameworks
- [ ] Machine learning for anomaly detection
- [ ] Real-time monitoring
- [ ] Integration with CI/CD
- [ ] Multi-account governance
- [ ] Policy analytics
- [ ] Automated remediation

## Support

If you encounter any issues or have questions:

1. Check the documentation
2. Look for similar issues in the issue tracker
3. Open a new issue if needed

## Related Projects

- [AWS Cost Explorer Client](https://github.com/yourusername/aws-cost-explorer-client)
- [Cloud Cost Normalization](https://github.com/yourusername/cloud-cost-normalization)
- [Terraform Cost Analyzer](https://github.com/yourusername/terraform-cost-analyzer)
- [Cloud Network Manager](https://github.com/yourusername/cloud-network-manager)
- [Cloud Resource Inventory](https://github.com/yourusername/cloud-resource-inventory)
- [Cloud Budget Manager](https://github.com/yourusername/cloud-budget-manager)
- [Cloud Compliance Manager](https://github.com/yourusername/cloud-compliance-manager)

## Acknowledgments

- AWS Organizations
- Azure Management Groups
- Google Cloud Resource Manager
- Cloud provider documentation
