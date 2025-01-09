# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Core AWS Cost Explorer client implementation
- Async/await support for all operations
- Built-in response caching
- Automatic retries with exponential backoff
- Comprehensive error handling
- Type safety with Pydantic models
- Detailed logging
- Test suite with mocked AWS responses
- Documentation with usage examples

### Features
- Cost and usage data retrieval
- Cost forecasting
- Reservation utilization analysis
- Savings Plans utilization analysis
- Cost filtering and grouping
- Support for all AWS Cost Explorer metrics
- Pagination handling
- Session management
- Credential handling

### Models
- Request/response models for all operations
- Cost data structures
- Filter expressions
- Grouping definitions
- Date intervals
- Metric definitions

### Error Handling
- Custom exception hierarchy
- Detailed error messages
- AWS error code mapping
- Rate limit handling
- Retry mechanism

## [0.1.0] - 2024-01-09

### Added
- Initial release
- Basic AWS Cost Explorer API integration
- Core functionality for cost data retrieval
- Essential data models
- Basic error handling
- Simple caching mechanism
- Async support
- Basic documentation

[Unreleased]: https://github.com/yourusername/aws-cost-explorer-client/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/aws-cost-explorer-client/releases/tag/v0.1.0
