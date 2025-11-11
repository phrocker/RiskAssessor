"""Feedback mechanism for recording and learning from incidents."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class FeedbackEntry:
    """Represents feedback about an incident that occurred."""
    
    id: str  # unique identifier
    timestamp: str  # when feedback was recorded
    incident_date: str  # when the incident occurred
    changeset_id: Optional[str]  # ID of the assessment that missed this
    pr_number: Optional[int]  # PR number if applicable
    commit_sha: Optional[str]  # commit SHA if applicable
    
    # Incident details
    severity: str  # critical, high, medium, low
    incident_type: str  # outage, performance, security, data-loss, etc.
    description: str  # what happened
    root_cause: str  # what caused the incident
    
    # What was missed
    affected_files: List[str]  # files involved in the incident
    missed_indicators: List[str]  # what should have been caught
    
    # Assessment details at the time
    original_risk_score: Optional[float]  # what was the score given
    original_risk_level: Optional[str]  # what was the level given
    
    # Resolution
    resolution: str  # how it was fixed
    time_to_resolve_hours: Optional[float]  # how long to fix
    
    # Learning
    lessons_learned: List[str]  # what to watch for next time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackEntry":
        """Create from dictionary."""
        return cls(**data)


class FeedbackCatalog:
    """Manages the catalog of incident feedback."""
    
    def __init__(self, feedback_path: str = ".risk_assessor/feedback.json"):
        """
        Initialize feedback catalog.
        
        Args:
            feedback_path: Path to the feedback file
        """
        self.feedback_path = Path(feedback_path)
        self.entries: List[FeedbackEntry] = []
        self._load()
    
    def _load(self):
        """Load feedback from file."""
        if self.feedback_path.exists():
            with open(self.feedback_path, 'r') as f:
                data = json.load(f)
                self.entries = [FeedbackEntry.from_dict(item) for item in data]
    
    def save(self):
        """Save feedback to file."""
        self.feedback_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.feedback_path, 'w') as f:
            json.dump([entry.to_dict() for entry in self.entries], f, indent=2)
    
    def add_feedback(self, entry: FeedbackEntry):
        """
        Add a feedback entry to the catalog.
        
        Args:
            entry: Feedback entry to add
        """
        # Check if entry with same ID already exists
        existing = self.find_by_id(entry.id)
        if existing:
            # Update existing entry
            self.entries.remove(existing)
        
        self.entries.append(entry)
    
    def find_by_id(self, entry_id: str) -> Optional[FeedbackEntry]:
        """
        Find a feedback entry by ID.
        
        Args:
            entry_id: Feedback entry ID
        
        Returns:
            FeedbackEntry if found, None otherwise
        """
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def search_by_files(self, files: List[str]) -> List[FeedbackEntry]:
        """
        Search for feedback entries related to specific files.
        
        Args:
            files: List of file paths
        
        Returns:
            List of related feedback entries
        """
        related = []
        for entry in self.entries:
            for file in files:
                if any(file in affected_file or affected_file in file 
                       for affected_file in entry.affected_files):
                    related.append(entry)
                    break
        return related
    
    def search_by_severity(self, severity: str) -> List[FeedbackEntry]:
        """
        Search for feedback entries by severity.
        
        Args:
            severity: Severity level (critical, high, medium, low)
        
        Returns:
            List of matching feedback entries
        """
        return [
            entry for entry in self.entries
            if entry.severity.lower() == severity.lower()
        ]
    
    def search_by_incident_type(self, incident_type: str) -> List[FeedbackEntry]:
        """
        Search for feedback entries by incident type.
        
        Args:
            incident_type: Type of incident
        
        Returns:
            List of matching feedback entries
        """
        return [
            entry for entry in self.entries
            if entry.incident_type.lower() == incident_type.lower()
        ]
    
    def get_recent_feedback(self, days: int = 90) -> List[FeedbackEntry]:
        """
        Get feedback entries from the last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of recent feedback entries
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent = []
        
        for entry in self.entries:
            try:
                incident_date = datetime.fromisoformat(
                    entry.incident_date.replace('Z', '+00:00')
                )
                if incident_date.timestamp() > cutoff:
                    recent.append(entry)
            except (ValueError, AttributeError):
                pass
        
        return recent
    
    def calculate_feedback_risk_score(
        self, 
        files_changed: List[str],
        recent_days: int = 180
    ) -> float:
        """
        Calculate a risk score based on feedback for similar file changes.
        
        Args:
            files_changed: List of files being changed
            recent_days: Look back this many days for relevant feedback
        
        Returns:
            Risk score (0-1) based on feedback
        """
        if not files_changed:
            return 0.0
        
        # Get recent feedback
        recent_feedback = self.get_recent_feedback(days=recent_days)
        
        # Find feedback related to these files
        related_feedback = []
        for entry in recent_feedback:
            for file in files_changed:
                if any(file in affected or affected in file 
                       for affected in entry.affected_files):
                    related_feedback.append(entry)
                    break
        
        if not related_feedback:
            return 0.0
        
        # Calculate weighted score based on severity and recency
        severity_weights = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        }
        
        total_weight = 0.0
        for entry in related_feedback:
            severity = entry.severity.lower()
            weight = severity_weights.get(severity, 0.5)
            
            # Apply recency decay (more recent incidents matter more)
            try:
                incident_date = datetime.fromisoformat(
                    entry.incident_date.replace('Z', '+00:00')
                )
                days_ago = (datetime.now() - incident_date).days
                recency_factor = max(0.5, 1.0 - (days_ago / (recent_days * 2)))
                weight *= recency_factor
            except (ValueError, AttributeError):
                pass
            
            total_weight += weight
        
        # Normalize score (more incidents = higher risk)
        # Cap at 1.0
        score = min(1.0, total_weight / 3.0)
        
        return score
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the feedback catalog.
        
        Returns:
            Dictionary of statistics
        """
        total = len(self.entries)
        by_severity = {}
        by_type = {}
        
        total_resolution_time = 0.0
        resolution_count = 0
        
        for entry in self.entries:
            # Count by severity
            severity = entry.severity.lower()
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Count by type
            incident_type = entry.incident_type.lower()
            by_type[incident_type] = by_type.get(incident_type, 0) + 1
            
            # Track resolution times
            if entry.time_to_resolve_hours is not None:
                total_resolution_time += entry.time_to_resolve_hours
                resolution_count += 1
        
        avg_resolution = None
        if resolution_count > 0:
            avg_resolution = total_resolution_time / resolution_count
        
        return {
            'total_entries': total,
            'by_severity': by_severity,
            'by_incident_type': by_type,
            'average_resolution_hours': avg_resolution
        }
