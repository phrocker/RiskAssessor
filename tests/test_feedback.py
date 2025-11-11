"""Tests for the feedback mechanism."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json

from risk_assessor.core.feedback import FeedbackCatalog, FeedbackEntry


@pytest.fixture
def temp_feedback_path():
    """Create a temporary feedback file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "feedback.json")


def test_feedback_entry_creation():
    """Test creating a feedback entry."""
    entry = FeedbackEntry(
        id="feedback-123",
        timestamp=datetime.now().isoformat(),
        incident_date="2025-11-10T10:00:00Z",
        changeset_id="pr-456",
        pr_number=456,
        commit_sha="abc123",
        severity="critical",
        incident_type="outage",
        description="Service went down",
        root_cause="Configuration error in deployment",
        affected_files=["config/deploy.yaml", "src/server.py"],
        missed_indicators=["No validation on config schema"],
        original_risk_score=0.3,
        original_risk_level="low",
        resolution="Fixed config and added validation",
        time_to_resolve_hours=2.5,
        lessons_learned=["Always validate config before deployment"]
    )
    
    assert entry.id == "feedback-123"
    assert entry.severity == "critical"
    assert entry.incident_type == "outage"
    assert len(entry.affected_files) == 2
    assert len(entry.lessons_learned) == 1


def test_feedback_entry_serialization():
    """Test converting feedback entry to/from dict."""
    entry = FeedbackEntry(
        id="feedback-456",
        timestamp=datetime.now().isoformat(),
        incident_date="2025-11-10T10:00:00Z",
        changeset_id=None,
        pr_number=None,
        commit_sha=None,
        severity="high",
        incident_type="performance",
        description="Slow response times",
        root_cause="Database query inefficiency",
        affected_files=["db/queries.py"],
        missed_indicators=["No performance testing"],
        original_risk_score=None,
        original_risk_level=None,
        resolution="Optimized queries",
        time_to_resolve_hours=4.0,
        lessons_learned=["Add performance benchmarks"]
    )
    
    # Convert to dict
    data = entry.to_dict()
    assert data["id"] == "feedback-456"
    assert data["severity"] == "high"
    
    # Convert back from dict
    restored = FeedbackEntry.from_dict(data)
    assert restored.id == entry.id
    assert restored.severity == entry.severity
    assert restored.affected_files == entry.affected_files


def test_feedback_catalog_operations(temp_feedback_path):
    """Test basic feedback catalog operations."""
    catalog = FeedbackCatalog(temp_feedback_path)
    
    # Should start empty
    assert len(catalog.entries) == 0
    
    # Add a feedback entry
    entry1 = FeedbackEntry(
        id="feedback-1",
        timestamp=datetime.now().isoformat(),
        incident_date="2025-11-10T10:00:00Z",
        changeset_id="pr-100",
        pr_number=100,
        commit_sha=None,
        severity="critical",
        incident_type="outage",
        description="Service outage",
        root_cause="Memory leak",
        affected_files=["src/memory.py"],
        missed_indicators=["No memory profiling"],
        original_risk_score=0.4,
        original_risk_level="medium",
        resolution="Fixed memory leak",
        time_to_resolve_hours=1.5,
        lessons_learned=["Monitor memory usage"]
    )
    
    catalog.add_feedback(entry1)
    assert len(catalog.entries) == 1
    
    # Save and reload
    catalog.save()
    
    # Create new catalog instance and load
    catalog2 = FeedbackCatalog(temp_feedback_path)
    assert len(catalog2.entries) == 1
    assert catalog2.entries[0].id == "feedback-1"
    assert catalog2.entries[0].severity == "critical"


def test_feedback_search_by_files(temp_feedback_path):
    """Test searching feedback by files."""
    catalog = FeedbackCatalog(temp_feedback_path)
    
    # Add entries with different files
    entry1 = FeedbackEntry(
        id="feedback-1",
        timestamp=datetime.now().isoformat(),
        incident_date="2025-11-10T10:00:00Z",
        changeset_id=None,
        pr_number=None,
        commit_sha=None,
        severity="high",
        incident_type="outage",
        description="Test",
        root_cause="Test",
        affected_files=["src/api.py", "src/database.py"],
        missed_indicators=[],
        original_risk_score=None,
        original_risk_level=None,
        resolution="Fixed",
        time_to_resolve_hours=None,
        lessons_learned=[]
    )
    
    entry2 = FeedbackEntry(
        id="feedback-2",
        timestamp=datetime.now().isoformat(),
        incident_date="2025-11-09T10:00:00Z",
        changeset_id=None,
        pr_number=None,
        commit_sha=None,
        severity="medium",
        incident_type="performance",
        description="Test",
        root_cause="Test",
        affected_files=["src/cache.py"],
        missed_indicators=[],
        original_risk_score=None,
        original_risk_level=None,
        resolution="Fixed",
        time_to_resolve_hours=None,
        lessons_learned=[]
    )
    
    catalog.add_feedback(entry1)
    catalog.add_feedback(entry2)
    
    # Search for api.py
    results = catalog.search_by_files(["src/api.py"])
    assert len(results) == 1
    assert results[0].id == "feedback-1"
    
    # Search for cache.py
    results = catalog.search_by_files(["src/cache.py"])
    assert len(results) == 1
    assert results[0].id == "feedback-2"
    
    # Search for non-existent file
    results = catalog.search_by_files(["src/notfound.py"])
    assert len(results) == 0


def test_feedback_search_by_severity(temp_feedback_path):
    """Test searching feedback by severity."""
    catalog = FeedbackCatalog(temp_feedback_path)
    
    # Add entries with different severities
    for i, severity in enumerate(["critical", "high", "medium", "low"]):
        entry = FeedbackEntry(
            id=f"feedback-{i}",
            timestamp=datetime.now().isoformat(),
            incident_date="2025-11-10T10:00:00Z",
            changeset_id=None,
            pr_number=None,
            commit_sha=None,
            severity=severity,
            incident_type="test",
            description="Test",
            root_cause="Test",
            affected_files=[],
            missed_indicators=[],
            original_risk_score=None,
            original_risk_level=None,
            resolution="Fixed",
            time_to_resolve_hours=None,
            lessons_learned=[]
        )
        catalog.add_feedback(entry)
    
    # Search by severity
    critical = catalog.search_by_severity("critical")
    assert len(critical) == 1
    assert critical[0].severity == "critical"
    
    high = catalog.search_by_severity("high")
    assert len(high) == 1
    
    # Case insensitive
    medium = catalog.search_by_severity("MEDIUM")
    assert len(medium) == 1


def test_feedback_calculate_risk_score(temp_feedback_path):
    """Test calculating risk score from feedback."""
    catalog = FeedbackCatalog(temp_feedback_path)
    
    # No feedback should give 0 score
    score = catalog.calculate_feedback_risk_score(["src/api.py"])
    assert score == 0.0
    
    # Add a critical incident
    entry1 = FeedbackEntry(
        id="feedback-1",
        timestamp=datetime.now().isoformat(),
        incident_date=datetime.now().isoformat(),
        changeset_id=None,
        pr_number=None,
        commit_sha=None,
        severity="critical",
        incident_type="outage",
        description="Test",
        root_cause="Test",
        affected_files=["src/api.py"],
        missed_indicators=[],
        original_risk_score=None,
        original_risk_level=None,
        resolution="Fixed",
        time_to_resolve_hours=None,
        lessons_learned=[]
    )
    catalog.add_feedback(entry1)
    
    # Should have higher score now
    score = catalog.calculate_feedback_risk_score(["src/api.py"])
    assert score > 0.0
    assert score <= 1.0
    
    # Add another high severity incident
    entry2 = FeedbackEntry(
        id="feedback-2",
        timestamp=datetime.now().isoformat(),
        incident_date=datetime.now().isoformat(),
        changeset_id=None,
        pr_number=None,
        commit_sha=None,
        severity="high",
        incident_type="performance",
        description="Test",
        root_cause="Test",
        affected_files=["src/api.py"],
        missed_indicators=[],
        original_risk_score=None,
        original_risk_level=None,
        resolution="Fixed",
        time_to_resolve_hours=None,
        lessons_learned=[]
    )
    catalog.add_feedback(entry2)
    
    # Score should be higher with more incidents
    score2 = catalog.calculate_feedback_risk_score(["src/api.py"])
    assert score2 > score


def test_feedback_statistics(temp_feedback_path):
    """Test feedback statistics."""
    catalog = FeedbackCatalog(temp_feedback_path)
    
    # Add some entries
    for i in range(3):
        entry = FeedbackEntry(
            id=f"feedback-{i}",
            timestamp=datetime.now().isoformat(),
            incident_date="2025-11-10T10:00:00Z",
            changeset_id=None,
            pr_number=None,
            commit_sha=None,
            severity="critical" if i == 0 else "high",
            incident_type="outage" if i < 2 else "performance",
            description="Test",
            root_cause="Test",
            affected_files=[],
            missed_indicators=[],
            original_risk_score=None,
            original_risk_level=None,
            resolution="Fixed",
            time_to_resolve_hours=float(i + 1),
            lessons_learned=[]
        )
        catalog.add_feedback(entry)
    
    stats = catalog.get_statistics()
    
    assert stats["total_entries"] == 3
    assert stats["by_severity"]["critical"] == 1
    assert stats["by_severity"]["high"] == 2
    assert stats["by_incident_type"]["outage"] == 2
    assert stats["by_incident_type"]["performance"] == 1
    assert stats["average_resolution_hours"] == 2.0  # (1 + 2 + 3) / 3


def test_feedback_recent_entries(temp_feedback_path):
    """Test getting recent feedback entries."""
    catalog = FeedbackCatalog(temp_feedback_path)
    
    # Add old entry
    old_entry = FeedbackEntry(
        id="feedback-old",
        timestamp=datetime.now().isoformat(),
        incident_date=(datetime.now() - timedelta(days=100)).isoformat(),
        changeset_id=None,
        pr_number=None,
        commit_sha=None,
        severity="low",
        incident_type="test",
        description="Test",
        root_cause="Test",
        affected_files=[],
        missed_indicators=[],
        original_risk_score=None,
        original_risk_level=None,
        resolution="Fixed",
        time_to_resolve_hours=None,
        lessons_learned=[]
    )
    
    # Add recent entry
    recent_entry = FeedbackEntry(
        id="feedback-recent",
        timestamp=datetime.now().isoformat(),
        incident_date=(datetime.now() - timedelta(days=10)).isoformat(),
        changeset_id=None,
        pr_number=None,
        commit_sha=None,
        severity="high",
        incident_type="test",
        description="Test",
        root_cause="Test",
        affected_files=[],
        missed_indicators=[],
        original_risk_score=None,
        original_risk_level=None,
        resolution="Fixed",
        time_to_resolve_hours=None,
        lessons_learned=[]
    )
    
    catalog.add_feedback(old_entry)
    catalog.add_feedback(recent_entry)
    
    # Get recent feedback (last 90 days)
    recent = catalog.get_recent_feedback(days=90)
    assert len(recent) == 1
    assert recent[0].id == "feedback-recent"
