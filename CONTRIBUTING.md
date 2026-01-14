# Contributing to TTE2026_sleep

We love your input! We want to make contributing to this project as easy and transparent as possible.

## Development Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the style guidelines
6. Issue that pull request!

## Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Before committing, run:
```bash
black src/
isort src/
flake8 src/
mypy src/
```

Or use pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

## Testing

Run tests with pytest:
```bash
pytest tests/ -v
pytest tests/ --cov=src  # with coverage
```

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the CHANGELOG.md with a note describing your changes
3. The PR will be merged once you have sign-off from a maintainer

## Any contributions you make will be under the MIT Software License

When you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project.

## Report bugs using GitHub's [issue tracker](https://github.com/yourusername/TTE2026_sleep/issues)

We use GitHub issues to track public bugs. Report a bug by opening a new issue.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
