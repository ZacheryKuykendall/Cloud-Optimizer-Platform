# Contributing to Resource Requirements Parser

Thank you for your interest in contributing to the Resource Requirements Parser! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include any error messages or stack traces

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* A clear and descriptive title
* A detailed description of the proposed functionality
* Any possible implementation details
* Why this enhancement would be useful to most users

### Adding Support for New Source Types

If you want to add support for a new infrastructure definition source type:

1. Create a new parser class in `src/resource_requirements_parser/parsers/`
2. Implement the `BaseParser` interface
3. Add appropriate tests
4. Update documentation
5. Register the parser in `__init__.py`

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python style guides
* Include tests for new functionality
* Update documentation as needed
* End all files with a newline

## Development Process

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/your-username/resource-requirements-parser.git
cd resource-requirements-parser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e ".[dev,test]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=resource_requirements_parser

# Run specific test file
pytest tests/test_terraform_parser.py
```

### Code Style

This project uses several tools to maintain code quality:

* black for code formatting
* isort for import sorting
* mypy for type checking
* pylint for code analysis

Run all style checks:

```bash
# Format code
black .
isort .

# Type checking
mypy src/resource_requirements_parser

# Linting
pylint src/resource_requirements_parser
```

## Project Structure

```
resource-requirements-parser/
├── src/
│   └── resource_requirements_parser/
│       ├── __init__.py
│       ├── models.py          # Data models
│       ├── exceptions.py      # Custom exceptions
│       ├── parser.py          # Base parser interface
│       └── parsers/          # Parser implementations
│           ├── __init__.py
│           ├── terraform.py
│           └── cloudformation.py
├── tests/                    # Test files
├── docs/                     # Documentation
├── examples/                 # Example usage
├── LICENSE
├── README.md
├── CONTRIBUTING.md
└── pyproject.toml
```

## Documentation

* Use Google-style docstrings
* Include type hints
* Update README.md for significant changes
* Add examples for new features

Example docstring:

```python
def parse_resource(self, resource_id: str, data: Dict[str, Any]) -> ResourceRequirements:
    """Parse resource data into requirements.

    Args:
        resource_id: Unique identifier for the resource
        data: Raw resource definition data

    Returns:
        ResourceRequirements: Parsed resource requirements

    Raises:
        ValidationError: If resource data is invalid
        ResourceTypeError: If resource type cannot be determined
    """
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a new GitHub release
4. GitHub Actions will automatically publish to PyPI

## Getting Help

* Check the documentation
* Look for similar issues
* Ask questions in discussions
* Contact the maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
