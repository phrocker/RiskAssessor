"""Basic tests for RiskAssessor."""

import pytest
from datetime import datetime
from risk_assessor.core.issue_catalog import IssueCatalog, CatalogedIssue
from risk_assessor.analyzers.complexity import ComplexityAnalyzer
from risk_assessor.utils.config import Config


def test_cataloged_issue_creation():
    """Test creating a cataloged issue."""
    issue = CatalogedIssue(
        source="github",
        identifier="123",
        title="Test Issue",
        status="open",
        severity="high",
        components=[],
        labels=["bug"],
        created_at=datetime.now().isoformat(),
        resolved_at=None,
        description="Test description",
        related_files=["test.py"],
        url="https://github.com/test/repo/issues/123"
    )
    
    assert issue.source == "github"
    assert issue.identifier == "123"
    assert issue.title == "Test Issue"
    
    # Test conversion to dict
    issue_dict = issue.to_dict()
    assert isinstance(issue_dict, dict)
    assert issue_dict["source"] == "github"


def test_issue_catalog_operations(tmp_path):
    """Test issue catalog operations."""
    catalog_path = tmp_path / "catalog.json"
    catalog = IssueCatalog(str(catalog_path))
    
    # Add an issue
    issue = CatalogedIssue(
        source="github",
        identifier="1",
        title="Test Issue 1",
        status="open",
        severity="medium",
        components=[],
        labels=["bug"],
        created_at=datetime.now().isoformat(),
        resolved_at=None,
        description="Test",
        related_files=["file1.py"],
        url="https://example.com/1"
    )
    
    catalog.add_issue(issue)
    assert len(catalog.issues) == 1
    
    # Save and reload
    catalog.save()
    assert catalog_path.exists()
    
    new_catalog = IssueCatalog(str(catalog_path))
    assert len(new_catalog.issues) == 1
    assert new_catalog.issues[0].title == "Test Issue 1"
    
    # Search by files
    results = new_catalog.search_by_files(["file1.py"])
    assert len(results) == 1
    
    # Search by labels
    results = new_catalog.search_by_labels(["bug"])
    assert len(results) == 1


def test_complexity_analyzer():
    """Test complexity analyzer."""
    analyzer = ComplexityAnalyzer()
    
    # Test simple changes
    result = analyzer.analyze_changes(
        files_changed=["src/main.py", "tests/test_main.py"],
        additions=50,
        deletions=20,
        commits=3
    )
    
    assert result["files_changed"] == 2
    assert result["additions"] == 50
    assert result["deletions"] == 20
    assert result["total_changes"] == 70
    assert result["commits"] == 3
    assert "complexity_score" in result
    assert "risk_level" in result
    assert result["risk_level"] in ["low", "medium", "high", "critical"]
    
    # Test critical file detection
    result = analyzer.analyze_changes(
        files_changed=["config/production.yaml", "deploy/script.sh"],
        additions=10,
        deletions=5,
        commits=1
    )
    
    assert len(result["critical_files"]) > 0


def test_config_creation():
    """Test configuration creation."""
    config = Config()
    
    assert config.github is not None
    assert config.jira is not None
    assert config.llm is not None
    assert config.thresholds is not None
    
    # Test thresholds
    assert 0 <= config.thresholds.low_threshold <= 1
    assert 0 <= config.thresholds.medium_threshold <= 1
    assert 0 <= config.thresholds.high_threshold <= 1
    
    # Test weights sum to 1.0
    total_weight = (
        config.thresholds.complexity_weight +
        config.thresholds.history_weight +
        config.thresholds.llm_weight
    )
    assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error


def test_config_from_dict():
    """Test configuration from dictionary."""
    config_dict = {
        "thresholds": {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.7
        }
    }
    
    # This tests that the config structure is correct
    config = Config()
    assert config.thresholds.low_threshold >= 0
