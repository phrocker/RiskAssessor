# Contributing to RiskAssessor

Thank you for your interest in contributing to RiskAssessor! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/RiskAssessor.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Install in development mode: `pip install -e .`
5. Install dev dependencies: `pip install pytest pytest-cov pytest-mock`

## Development Workflow

### Making Changes

1. Make your changes in your feature branch
2. Add tests for new functionality
3. Ensure all tests pass: `pytest tests/`
4. Update documentation if needed

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to all public functions and classes
- Keep functions focused and single-purpose

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Run tests locally before submitting PR: `pytest tests/ -v`

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Reference issue numbers when applicable

Example:
```
Add support for GitLab integration

- Implement GitLab API client
- Add tests for GitLab issue fetching
- Update documentation

Fixes #123
```

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the CHANGELOG.md with your changes
3. Ensure all tests pass
4. Submit your pull request with a clear description
5. Address any review comments

## Areas for Contribution

We welcome contributions in these areas:

- **New Integrations**: Support for other issue tracking systems (GitLab, Bitbucket, etc.)
- **Analyzers**: Additional risk analysis methods
- **LLM Providers**: Support for other LLM providers (Anthropic, local models, etc.)
- **Documentation**: Improvements to docs, guides, and examples
- **Tests**: Additional test coverage
- **Bug Fixes**: Fix any bugs you encounter
- **Features**: New features that align with the project goals

## Feature Requests

To request a feature:

1. Check if it's already been requested in Issues
2. Open a new issue with the "enhancement" label
3. Describe the feature and its use case
4. Discuss the implementation approach

## Bug Reports

To report a bug:

1. Check if it's already been reported
2. Open a new issue with the "bug" label
3. Include:
   - Description of the bug
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version, etc.)

## Code of Conduct

- Be respectful and inclusive
- Assume good intentions
- Focus on constructive feedback
- Help create a welcoming environment

## Questions?

If you have questions:
- Check the documentation in README.md and GUIDE.md
- Search existing issues
- Open a new discussion or issue

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to RiskAssessor!
