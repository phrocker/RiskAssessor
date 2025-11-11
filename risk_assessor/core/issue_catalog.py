"""Issue catalog for storing and retrieving historical issues."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class CatalogedIssue:
    """Represents a cataloged issue from any source."""
    
    source: str  # 'github' or 'jira'
    identifier: str  # issue number or key
    title: str
    status: str
    severity: Optional[str]
    components: List[str]
    labels: List[str]
    created_at: str
    resolved_at: Optional[str]
    description: str
    related_files: List[str]
    url: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CatalogedIssue":
        """Create from dictionary."""
        return cls(**data)


class IssueCatalog:
    """Manages the catalog of historical issues."""
    
    def __init__(self, catalog_path: str = ".risk_assessor/catalog.json"):
        """
        Initialize issue catalog.
        
        Args:
            catalog_path: Path to the catalog file
        """
        self.catalog_path = Path(catalog_path)
        self.issues: List[CatalogedIssue] = []
        self._load()
    
    def _load(self):
        """Load catalog from file."""
        if self.catalog_path.exists():
            with open(self.catalog_path, 'r') as f:
                data = json.load(f)
                self.issues = [CatalogedIssue.from_dict(item) for item in data]
    
    def save(self):
        """Save catalog to file."""
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.catalog_path, 'w') as f:
            json.dump([issue.to_dict() for issue in self.issues], f, indent=2)
    
    def add_issue(self, issue: CatalogedIssue):
        """
        Add an issue to the catalog.
        
        Args:
            issue: Issue to add
        """
        # Check if issue already exists
        existing = self.find_issue(issue.source, issue.identifier)
        if existing:
            # Update existing issue
            self.issues.remove(existing)
        
        self.issues.append(issue)
    
    def add_issues(self, issues: List[CatalogedIssue]):
        """
        Add multiple issues to the catalog.
        
        Args:
            issues: List of issues to add
        """
        for issue in issues:
            self.add_issue(issue)
    
    def find_issue(self, source: str, identifier: str) -> Optional[CatalogedIssue]:
        """
        Find an issue by source and identifier.
        
        Args:
            source: Issue source ('github' or 'jira')
            identifier: Issue identifier
        
        Returns:
            CatalogedIssue if found, None otherwise
        """
        for issue in self.issues:
            if issue.source == source and issue.identifier == identifier:
                return issue
        return None
    
    def search_by_files(self, files: List[str]) -> List[CatalogedIssue]:
        """
        Search for issues related to specific files.
        
        Args:
            files: List of file paths
        
        Returns:
            List of related issues
        """
        related = []
        for issue in self.issues:
            for file in files:
                if any(file in related_file or related_file in file 
                       for related_file in issue.related_files):
                    related.append(issue)
                    break
        return related
    
    def search_by_components(self, components: List[str]) -> List[CatalogedIssue]:
        """
        Search for issues by components.
        
        Args:
            components: List of component names
        
        Returns:
            List of matching issues
        """
        return [
            issue for issue in self.issues
            if any(comp in issue.components for comp in components)
        ]
    
    def search_by_labels(self, labels: List[str]) -> List[CatalogedIssue]:
        """
        Search for issues by labels.
        
        Args:
            labels: List of labels
        
        Returns:
            List of matching issues
        """
        return [
            issue for issue in self.issues
            if any(label in issue.labels for label in labels)
        ]
    
    def get_recent_issues(self, days: int = 90) -> List[CatalogedIssue]:
        """
        Get issues from the last N days.
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of recent issues
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent = []
        
        for issue in self.issues:
            try:
                created = datetime.fromisoformat(issue.created_at.replace('Z', '+00:00'))
                if created.timestamp() > cutoff:
                    recent.append(issue)
            except (ValueError, AttributeError):
                pass
        
        return recent
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the catalog.
        
        Returns:
            Dictionary of statistics
        """
        total = len(self.issues)
        by_source = {}
        by_status = {}
        
        for issue in self.issues:
            by_source[issue.source] = by_source.get(issue.source, 0) + 1
            by_status[issue.status] = by_status.get(issue.status, 0) + 1
        
        return {
            'total_issues': total,
            'by_source': by_source,
            'by_status': by_status
        }
