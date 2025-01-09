# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of the Cloud Cost Normalization service
- Multi-cloud support for AWS, Azure, and GCP
- Resource type mapping system
- Currency conversion with caching
- Cost aggregation functionality
- Comprehensive test suite
- Detailed documentation

### Features
- Normalize costs from different cloud providers into a standardized format
- Map provider-specific resource types to common categories
- Convert costs between different currencies
- Aggregate costs by various dimensions
- Cache exchange rates for better performance
- Handle historical cost data

### Core Components
- Async/await support for all operations
- Type safety with Pydantic models
- Comprehensive error handling
- Extensive logging
- Resource mapping system
- Currency conversion service

### Documentation
- README with usage examples
- API documentation
- Contributing guidelines
- Code of conduct
- Security policy

## [0.1.0] - 2024-01-01

### Added
- Initial project structure
- Basic data models
- Core normalization logic
- Currency conversion functionality
- Basic test suite

### Dependencies
- Python 3.9+
- pydantic>=2.0.0
- sqlalchemy>=2.0.0
- alembic>=1.9.0
- pandas>=2.0.0
- requests>=2.28.0
- python-dateutil>=2.8.2
- aws-cost-explorer-client>=0.1.0
- azure-mgmt-costmanagement>=3.0.0
- google-cloud-billing>=1.9.0
- forex-python>=1.8.0
- rich>=13.0.0

### Development Dependencies
- pytest>=7.0.0
- pytest-cov>=4.0.0
- pytest-asyncio>=0.21.0
- black>=22.0.0
- isort>=5.0.0
- mypy>=1.0.0
- pylint>=2.15.0

[Unreleased]: https://github.com/yourusername/cloud-cost-normalization/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/cloud-cost-normalization/releases/tag/v0.1.0
