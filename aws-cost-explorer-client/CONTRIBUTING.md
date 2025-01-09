# Contributing to AWS Cost Explorer Client

First off, thank you for considering contributing to AWS Cost Explorer Client! It's people like you that make this project better.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

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
* Explain why this enhancement would be useful
* List any alternative solutions or features you've considered

### Pull Requests

* Fork the repository
* Create a new branch for your feature (`git checkout -b feature/amazing-feature`)
* Make your changes
* Run the test suite
* Commit your changes (`git commit -m 'Add amazing feature'`)
* Push to the branch (`git push origin feature/amazing-feature`)
* Open a Pull Request

## Development Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/aws-cost-explorer-client.git
   cd aws-cost-explorer-client
   ```

2. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Set up pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

## Development Process

### Code Style

We use several tools to maintain code quality:

* Black for code formatting
* isort for import sorting
* mypy for type checking
* pylint for code analysis

Run all checks with:
```bash
poetry run black .
poetry run isort .
poetry run mypy .
poetry run pylint src tests
```

### Testing

We use pytest for testing. Run the test suite with:
```bash
poetry run pytest
```

For coverage report:
```bash
poetry run pytest --cov=aws_cost_explorer
```

### Documentation

* Keep docstrings up to date
* Follow Google style for docstrings
* Update the README.md if needed
* Add examples for new features
* Update the usage documentation

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Branch Naming

* feature/: New features or enhancements
* fix/: Bug fixes
* docs/: Documentation changes
* refactor/: Code refactoring
* test/: Test-related changes

## Project Structure

```
aws-cost-explorer-client/
├── src/
│   └── aws_cost_explorer/
│       ├── __init__.py
│       ├── client.py
│       ├── exceptions.py
│       └── models.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_client.py
├── docs/
│   └── usage.md
├── pyproject.toml
├── README.md
└── CONTRIBUTING.md
```

## Release Process

1. Update version in pyproject.toml
2. Update CHANGELOG.md
3. Create a new release on GitHub
4. GitHub Actions will automatically publish to PyPI

## Type Hints

* Use type hints for all function arguments and return values
* Use Optional[] for optional parameters
* Use Union[] when a parameter can be multiple types
* Add type: ignore comments only when absolutely necessary

## Error Handling

* Create specific exception classes for different error cases
* Include relevant error details in exception messages
* Document all possible exceptions in docstrings
* Use appropriate exception hierarchies

## Testing Guidelines

* Write tests for all new features
* Maintain high test coverage
* Use meaningful test names
* Include both positive and negative test cases
* Mock external services appropriately
* Use fixtures for common test setup

## Documentation Guidelines

* Keep API documentation up to date
* Include examples in docstrings
* Document all parameters and return values
* Explain complex algorithms or business logic
* Update the changelog for all notable changes

## Performance Considerations

* Use caching appropriately
* Implement pagination for large datasets
* Consider memory usage
* Profile code when necessary
* Document performance implications

## Security Guidelines

* Never commit credentials
* Use environment variables for sensitive data
* Follow AWS security best practices
* Report security issues privately
* Review dependencies regularly

## Getting Help

* Check the documentation
* Search existing issues
* Ask questions in discussions
* Join our community chat

## Recognition

Contributors will be recognized in:

* CHANGELOG.md
* GitHub releases
* Project documentation

Thank you for contributing to AWS Cost Explorer Client!
