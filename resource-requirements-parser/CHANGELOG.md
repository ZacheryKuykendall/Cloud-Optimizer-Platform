# Changelog

All notable changes to the Resource Requirements Parser will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure and core functionality
- Base parser interface and registry
- Data models for resource requirements
- Custom exceptions for error handling
- Terraform parser implementation
  - Support for compute resources
  - Support for storage resources
  - Support for network resources
  - Support for database resources
  - Variable resolution
  - Dependency tracking
- CloudFormation parser implementation
  - Support for compute resources
  - Support for storage resources
  - Support for network resources
  - Support for database resources
  - Parameter resolution
  - Dependency tracking
- Comprehensive documentation
  - README with usage examples
  - Contributing guidelines
  - API documentation

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.1.0] - 2024-01-09

### Added
- First public release
- Core functionality for parsing infrastructure requirements
- Support for Terraform and CloudFormation
- Basic resource type identification
- Resource dependency tracking
- Documentation and examples

[Unreleased]: https://github.com/yourusername/resource-requirements-parser/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/resource-requirements-parser/releases/tag/v0.1.0
