# CI/CD Workflows

This directory contains GitHub Actions workflows for the RiskAssessor project.

## Workflows

### 1. CI/CD Pipeline (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**

#### Test Suite
- Runs on: `ubuntu-latest`
- Python versions: 3.8, 3.9, 3.10, 3.11 (matrix strategy)
- Steps:
  1. Checkout code
  2. Set up Python with pip caching
  3. Install dependencies (`pip install -e .` and requirements)
  4. Run pytest with coverage reporting
  5. Upload coverage to Codecov (Python 3.11 only)
  6. Upload test results as artifacts (7-day retention)

#### Code Quality
- Runs on: `ubuntu-latest`
- Python version: 3.11
- Steps:
  1. Checkout code
  2. Set up Python with pip caching
  3. Install linting dependencies (Black, flake8, mypy)
  4. Check code formatting with Black
  5. Lint with flake8

**Permissions:** `contents: read` (minimal required permissions)

---

### 2. Risk Assessment (`risk-assessment.yml`)

**Triggers:**
- Pull requests to `main` or `develop` branches
- Events: opened, synchronize, reopened

**Jobs:**

#### Assess PR Risk
- Runs on: `ubuntu-latest`
- Python version: 3.11
- Steps:
  1. Checkout code with full history (`fetch-depth: 0`)
  2. Set up Python with pip caching
  3. Install RiskAssessor and dependencies
  4. Run risk assessment on the PR itself (dogfooding)
     - Attempts contract format (v2.0) first
     - Falls back to legacy format if needed
     - Generates JSON output
  5. Generate formatted risk summary in Markdown
  6. Post/update risk assessment as PR comment
  7. Upload risk assessment artifacts (30-day retention)
  8. Check risk threshold and warn on HIGH/CRITICAL

**Permissions:**
- `contents: read` - Read repository contents
- `pull-requests: write` - Post comments on PRs
- `issues: write` - Update PR comments

**Environment Variables:**
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- `GITHUB_REPO` - Repository name (e.g., `owner/repo`)
- `OPENAI_API_KEY` - (Optional) For LLM-based analysis. If not set, uses complexity + history only.

**Outputs:**
- Risk assessment JSON file (artifact)
- Risk summary comment on PR
- Warning on HIGH/CRITICAL risk levels

---

## Configuration

### Adding LLM Analysis

To enable LLM-powered risk analysis in the Risk Assessment workflow:

1. Go to your repository Settings → Secrets and variables → Actions
2. Add a new repository secret named `OPENAI_API_KEY`
3. Set the value to your OpenAI API key
4. Uncomment the OPENAI_API_KEY line in `risk-assessment.yml`:
   ```yaml
   env:
     GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
     GITHUB_REPO: ${{ github.repository }}
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}  # Uncomment this line
   ```

### Failing on HIGH Risk

To make the workflow fail (and block merging) when HIGH or CRITICAL risk is detected:

1. Open `.github/workflows/risk-assessment.yml`
2. Find the "Check Risk Level Threshold" step
3. Uncomment the last line:
   ```yaml
   - name: Check Risk Level Threshold
     if: steps.risk-assessment.outputs.risk_level == 'HIGH' || steps.risk-assessment.outputs.risk_level == 'CRITICAL'
     run: |
       echo "::warning::High risk detected! Risk Level: ${{ steps.risk-assessment.outputs.risk_level }}"
       echo "This PR requires careful review and staged rollout."
       exit 1  # Uncomment to fail the workflow
   ```

### Codecov Integration

The CI workflow uploads coverage reports to Codecov. To view coverage reports:

1. Sign up at [codecov.io](https://codecov.io)
2. Connect your GitHub repository
3. Coverage reports will appear automatically on PRs

Alternatively, you can add a `CODECOV_TOKEN` secret to your repository for private repos.

---

## Testing the Workflows

### Locally

You can test the workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or download from GitHub releases

# Test the CI workflow
act push -W .github/workflows/ci.yml

# Test the risk assessment workflow (requires PR context)
act pull_request -W .github/workflows/risk-assessment.yml
```

### On GitHub

The workflows will run automatically when:
- You push to `main` or `develop` branches (CI workflow)
- You open, update, or reopen a PR to `main` or `develop` (both workflows)

---

## Artifacts

### Test Results
- Name: `test-results-{python-version}`
- Retention: 7 days
- Contents: pytest cache, coverage XML

### Risk Assessment
- Name: `risk-assessment-{pr-number}`
- Retention: 30 days
- Contents: risk contract JSON, legacy assessment JSON, Markdown summary

---

## Troubleshooting

### Tests fail due to missing dependencies
- Ensure `requirements.txt` is up to date
- Check that test dependencies (pytest, pytest-cov, pytest-mock) are installed

### Risk assessment fails to run
- Check that the PR has commits to analyze
- Verify `GITHUB_TOKEN` permissions are correct
- Check workflow logs for specific error messages

### Coverage upload fails
- This is normal if you don't have Codecov set up
- The workflow continues even if this step fails (`continue-on-error: true`)
- Set up Codecov or remove the upload step if not needed

### Risk assessment comment not posted
- Check that the workflow has `pull-requests: write` permission
- Ensure the PR is against `main` or `develop` branch
- Check workflow logs for API errors

---

## Example Outputs

### Successful CI Run
```
✓ Test Suite (Python 3.8) - passed
✓ Test Suite (Python 3.9) - passed
✓ Test Suite (Python 3.10) - passed
✓ Test Suite (Python 3.11) - passed
✓ Code Quality - passed
```

### Risk Assessment Comment
```markdown
🎯 Risk Assessment Report

**Risk Level:** MEDIUM
**Risk Score:** 0.45
**Confidence:** 0.85

### 📊 Overall Assessment
This change introduces moderate risk due to modifications in configuration files
and new feature additions. Recommend thorough testing before deployment.

### 🔍 Risk Factors
- **configuration**: 2 files modified (Weight: 0.15)
- **code**: 127 lines added, 45 deleted (Weight: 0.25)
- **testing**: Test coverage: 85% (Weight: 0.10)

### 💡 Recommendations
- Review configuration changes in staging environment
- Ensure all new features have adequate test coverage
- Consider feature flags for new functionality
- Deploy to canary environment first

---
*Generated by RiskAssessor v2.0 - Contract ID: changeset-abc123*
```

---

## Best Practices

1. **Branch Protection Rules**: Set up branch protection rules requiring:
   - CI workflow to pass
   - At least one code review
   - Risk assessment to complete (optional: can require passing)

2. **Review Risk Assessments**: Always review the risk assessment comment before merging
   
3. **LLM Analysis**: Enable OPENAI_API_KEY for more comprehensive risk analysis

4. **Incremental Changes**: Keep PRs small to maintain LOW risk scores

5. **Monitor Trends**: Track risk scores over time to identify problematic patterns

---

For more information about RiskAssessor, see the [main README](../../README.md).
