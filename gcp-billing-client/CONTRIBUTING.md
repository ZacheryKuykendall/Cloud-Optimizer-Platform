# Contributing to GCP Cloud Billing Client

We love your input! We want to make contributing to the GCP Cloud Billing client as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with GitHub

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [GitHub Flow](https://guides.github.com/introduction/flow/index.html)

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Process

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/gcp-billing-client.git
   cd gcp-billing-client
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   poetry install
   ```

3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

4. Create a new branch:
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

## Development Setup

1. Install Python 3.9 or higher
2. Install Poetry for dependency management
3. Install development dependencies:
   ```bash
   poetry install
   ```

## Running Tests

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=gcp_billing

# Run specific test file
poetry run pytest tests/test_client.py

# Run tests in watch mode
poetry run pytest-watch
```

## Code Style

We use several tools to maintain code quality:

1. Black for code formatting:
   ```bash
   poetry run black .
   ```

2. isort for import sorting:
   ```bash
   poetry run isort .
   ```

3. mypy for type checking:
   ```bash
   poetry run mypy .
   ```

4. pylint for linting:
   ```bash
   poetry run pylint src tests
   ```

## Documentation

- Update documentation if you change functionality.
- Separate code changes from documentation changes in different commits.
- Follow the existing documentation style.

### Documentation Structure

- `README.md`: Overview and quick start
- `docs/usage.md`: Detailed usage guide
- `docs/api.md`: API reference
- `CHANGELOG.md`: Version history
- `CONTRIBUTING.md`: This file
- Docstrings: Use Google style

## Testing Guidelines

1. Write tests for new features
2. Update tests for bug fixes
3. Maintain test coverage above 90%
4. Use meaningful test names and descriptions
5. Structure tests using Arrange-Act-Assert pattern

Example test:

```python
@pytest.mark.asyncio
async def test_get_billing_data_success():
    """Test successful retrieval of billing data."""
    # Arrange
    client = GCPBillingClient()
    request = GetBillingDataRequest(...)

    # Act
    result = await client.get_billing_data(request)

    # Assert
    assert result.billing_account_id == "test-account"
    assert len(result.rows) > 0
```

## Versioning

We follow [Semantic Versioning](https://semver.org/). For version numbers X.Y.Z:

- X: Major version (breaking changes)
- Y: Minor version (new features, no breaking changes)
- Z: Patch version (bug fixes, no breaking changes)

## Commit Messages

Format: `<type>(<scope>): <subject>`

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation only changes
- style: Code style changes (formatting, etc)
- refactor: Code changes that neither fix bugs nor add features
- perf: Performance improvements
- test: Adding or modifying tests
- chore: Maintenance tasks

Example:
```
feat(client): Add support for budget alerts
```

## Pull Request Process

1. Update documentation
2. Update CHANGELOG.md
3. Update version number
4. Get review from maintainers
5. Merge after approval

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issue tracker](https://github.com/yourusername/gcp-billing-client/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/yourusername/gcp-billing-client/issues/new).

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## References

This document was adapted from the open-source contribution guidelines for [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md).
