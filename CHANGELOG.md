# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-11

### Added
- Initial release of RiskAssessor
- GitHub integration for fetching issues and pull requests
- Jira integration for fetching issues
- Issue catalog system for storing and querying historical issues
- Complexity analyzer for code changes
- LLM-based risk assessment using OpenAI API
- Risk engine combining multiple analysis factors
- CLI with commands: sync, assess-pr, assess-commits, catalog-stats, init-config
- Configuration management via YAML files and environment variables
- Comprehensive documentation and examples
- Test suite with pytest
- Python API for programmatic usage

### Features
- Multi-factor risk assessment (complexity, history, LLM)
- Configurable risk thresholds and weights
- Support for GitHub and Jira issue tracking
- Rich CLI output with color-coded risk levels
- JSON export for CI/CD integration
- Historical issue pattern recognition
- Critical file detection
- Deployment risk recommendations

[0.1.0]: https://github.com/phrocker/RiskAssessor/releases/tag/v0.1.0
