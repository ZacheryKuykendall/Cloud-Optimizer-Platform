# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of the GCP Cloud Billing client
- Async/await support for all operations
- Comprehensive billing data retrieval
- Built-in response caching
- Automatic retries with exponential backoff
- Type safety with Pydantic models
- Detailed logging
- Extensive test coverage

### Features
- Get billing data and usage information
- Get pricing information for GCP services
- Create and manage budgets
- Export billing data to BigQuery or Cloud Storage
- Filter costs by various dimensions
- Group results by project, service, or other attributes

### Client Capabilities
- Async context manager support
- Configurable caching
- Retry mechanism with exponential backoff
- Comprehensive error handling
- Type-safe request/response models

### Documentation
- Comprehensive README
- Detailed API reference
- Usage guide with examples
- Contributing guidelines
- Code of conduct

## [0.1.0] - 2024-01-01

### Added
- Initial project structure
- Basic client implementation
- Core models and exceptions
- Basic documentation

### Dependencies
- Python 3.9+
- google-cloud-billing
- google-cloud-billing-budgets
- google-auth
- pydantic
- python-dateutil
- tenacity
- cachetools
- aiohttp
- structlog

### Development Dependencies
- pytest
- pytest-asyncio
- pytest-cov
- pytest-mock
- black
- isort
- mypy
- pylint
- types-python-dateutil
- types-cachetools

[Unreleased]: https://github.com/yourusername/gcp-billing-client/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/gcp-billing-client/releases/tag/v0.1.0
