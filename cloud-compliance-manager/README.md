# Cloud Compliance Manager

A Python library for managing and monitoring cloud compliance across different providers. This library provides functionality for compliance frameworks, rules, monitoring, and remediation actions.

## Features

- Compliance Frameworks:
  - CIS Benchmarks
  - HIPAA
  - PCI DSS
  - SOC 2
  - NIST
  - ISO 27001
  - GDPR
  - Custom frameworks

- Compliance Monitoring:
  - Resource scanning
  - Configuration auditing
  - Security checks
  - Access reviews
  - Real-time monitoring

- Compliance Reporting:
  - Compliance status
  - Violation tracking
  - Remediation tracking
  - Audit trails
  - Custom reports

## Installation

```bash
pip install cloud-compliance-manager
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
from cloud_compliance_manager import (
    ComplianceFramework,
    ComplianceRule,
    ComplianceMonitor,
    ResourceType
)

# Create a compliance rule
rule = ComplianceRule(
    framework=ComplianceFramework.CIS,
    rule_id="CIS.1.1",
    title="Maintain current contact details",
    description="Ensure contact email and telephone details for AWS accounts are current and valid",
    level="REQUIRED",
    resource_type=ResourceType.IDENTITY
)

# Set up compliance monitoring
monitor = ComplianceMonitor(
    name="cis-monitoring",
    frameworks=[ComplianceFramework.CIS],
    resource_types=[ResourceType.IDENTITY, ResourceType.SECURITY],
    schedule="0 * * * *"  # Run hourly
)

# Start monitoring
compliance_manager.start_monitoring(monitor)
```

### Compliance Checking

```python
from cloud_compliance_manager import ComplianceCheck, ComplianceStatus

# Run compliance check
check = ComplianceCheck(
    rule_id=rule.id,
    resource_id="account-123",
    status=ComplianceStatus.COMPLIANT,
    details={
        "contacts": {
            "email": "valid@example.com",
            "phone": "+1234567890"
        }
    }
)

# Process check results
if check.status == ComplianceStatus.NON_COMPLIANT:
    violation = compliance_manager.create_violation(check)
    compliance_manager.trigger_remediation(violation)
```

### Remediation Actions

```python
from cloud_compliance_manager import RemediationAction, RemediationType

# Configure remediation
action = RemediationAction(
    violation_id=violation.id,
    action_type="update_contacts",
    parameters={
        "email": "security@example.com",
        "phone": "+1987654321"
    },
    automated=True
)

# Execute remediation
compliance_manager.execute_remediation(action)
```

## Architecture

The library consists of several key components:

1. **Framework Management**:
   - Framework definitions
   - Rule management
   - Policy configuration
   - Custom framework support

2. **Compliance Monitoring**:
   - Resource scanning
   - Configuration checks
   - Security assessments
   - Real-time monitoring

3. **Remediation System**:
   - Action definitions
   - Automated fixes
   - Manual procedures
   - Approval workflows

4. **Reporting Engine**:
   - Status reporting
   - Violation tracking
   - Audit logging
   - Metrics collection

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cloud-compliance-manager.git
cd cloud-compliance-manager
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
pytest tests/test_compliance.py
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

- [ ] Additional compliance frameworks
- [ ] Advanced remediation actions
- [ ] Machine learning for risk assessment
- [ ] Custom rule engine
- [ ] Integration with CI/CD
- [ ] Real-time alerting
- [ ] Compliance analytics
- [ ] Multi-account support

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

## Acknowledgments

- AWS Security Hub
- Azure Security Center
- Google Cloud Security Command Center
- CIS Benchmarks
- Cloud provider documentation
