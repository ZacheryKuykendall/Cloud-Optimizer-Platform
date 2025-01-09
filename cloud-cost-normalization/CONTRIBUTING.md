# Contributing to Cloud Cost Normalization

Thank you for your interest in contributing to the Cloud Cost Normalization project! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [maintainers@yourdomain.com].

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include stack traces or error messages
* Include the Python version and operating system

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* A clear and descriptive title
* A detailed description of the proposed functionality
* Explain why this enhancement would be useful
* List any alternative solutions or features you've considered
* Include any relevant examples or mock-ups

### Pull Requests

1. Fork the repository and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Process

1. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/cloud-cost-normalization.git
   cd cloud-cost-normalization
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

5. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a Pull Request

## Development Environment Setup

### Required Tools

* Python 3.9 or higher
* pip
* git

### Dependencies

Install all dependencies including development tools:

```bash
pip install -e ".[dev]"
```

This will install:
* Core dependencies (pydantic, sqlalchemy, etc.)
* Testing tools (pytest, pytest-cov)
* Code quality tools (black, isort, mypy, pylint)

### Code Style

We use several tools to maintain code quality:

1. Black for code formatting:
   ```bash
   black .
   ```

2. isort for import sorting:
   ```bash
   isort .
   ```

3. mypy for type checking:
   ```bash
   mypy .
   ```

4. pylint for linting:
   ```bash
   pylint src tests
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src

# Run specific test file
pytest tests/test_normalizer.py

# Run tests in watch mode
pytest-watch
```

## Project Structure

```
cloud-cost-normalization/
├── src/
│   └── cloud_cost_normalization/
│       ├── __init__.py
│       ├── models.py          # Data models
│       ├── normalizer.py      # Core normalization logic
│       ├── currency.py        # Currency conversion
│       └── exceptions.py      # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_normalizer.py
│   └── test_currency.py
├── docs/
│   ├── usage.md
│   └── api.md
├── examples/
│   └── basic_usage.py
├── pyproject.toml            # Project metadata and dependencies
├── README.md                 # Project overview
├── CONTRIBUTING.md          # This file
├── LICENSE                  # MIT License
└── .gitignore
```

## Adding Support for New Cloud Providers

1. Add provider enum in `models.py`:
   ```python
   class CloudProvider(str, Enum):
       NEW_PROVIDER = "new_provider"
   ```

2. Add resource mappings in `normalizer.py`:
   ```python
   self._resource_mappings[CloudProvider.NEW_PROVIDER] = [
       ResourceMapping(
           provider=CloudProvider.NEW_PROVIDER,
           provider_type="ComputeService",
           normalized_type=ResourceType.COMPUTE,
           metadata_mapping={...}
       ),
       # Add more mappings...
   ]
   ```

3. Add normalization method in `normalizer.py`:
   ```python
   def _normalize_new_provider_cost(
       self,
       cost_data: dict,
       start_time: datetime,
       end_time: datetime
   ) -> List[NormalizedCostEntry]:
       # Implement normalization logic
       pass
   ```

4. Add tests in `tests/test_normalizer.py`

## Documentation

* Update documentation when adding new features
* Include docstrings for all public methods
* Follow Google style for docstrings
* Keep the README.md up to date
* Add examples for new functionality

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a new release on GitHub
4. Build and upload to PyPI:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Getting Help

* Open an issue for bugs or feature requests
* Join our community chat/forum
* Contact maintainers at [maintainers@yourdomain.com]

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
