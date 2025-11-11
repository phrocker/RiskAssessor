"""Jira integration for fetching issues."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from jira import JIRA


@dataclass
class JiraIssue:
    """Represents a Jira issue."""
    
    key: str
    summary: str
    status: str
    issue_type: str
    priority: Optional[str]
    created: datetime
    updated: datetime
    resolved: Optional[datetime]
    labels: List[str]
    assignee: Optional[str]
    reporter: Optional[str]
    description: str
    url: str
    components: List[str]
    fix_versions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime objects to strings
        for key in ['created', 'updated', 'resolved']:
            if data[key]:
                data[key] = data[key].isoformat()
        return data


class JiraClient:
    """Client for interacting with Jira API."""
    
    def __init__(self, server: str, username: str, token: str):
        """
        Initialize Jira client.
        
        Args:
            server: Jira server URL
            username: Jira username/email
            token: Jira API token
        """
        self.jira = JIRA(server=server, basic_auth=(username, token))
        self.server = server
    
    def get_issues(
        self,
        project: str,
        status: Optional[List[str]] = None,
        issue_type: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[JiraIssue]:
        """
        Fetch issues from Jira project.
        
        Args:
            project: Jira project key
            status: Filter by status
            issue_type: Filter by issue type
            labels: Filter by labels
            max_results: Maximum number of results to return
        
        Returns:
            List of JiraIssue objects
        """
        # Build JQL query
        jql_parts = [f'project = {project}']
        
        if status:
            status_str = ', '.join(f'"{s}"' for s in status)
            jql_parts.append(f'status IN ({status_str})')
        
        if issue_type:
            type_str = ', '.join(f'"{t}"' for t in issue_type)
            jql_parts.append(f'issuetype IN ({type_str})')
        
        if labels:
            label_conditions = ' OR '.join(f'labels = "{label}"' for label in labels)
            jql_parts.append(f'({label_conditions})')
        
        jql = ' AND '.join(jql_parts)
        jql += ' ORDER BY created DESC'
        
        issues = []
        jira_issues = self.jira.search_issues(jql, maxResults=max_results)
        
        for issue in jira_issues:
            issues.append(JiraIssue(
                key=issue.key,
                summary=issue.fields.summary,
                status=issue.fields.status.name,
                issue_type=issue.fields.issuetype.name,
                priority=issue.fields.priority.name if issue.fields.priority else None,
                created=datetime.fromisoformat(issue.fields.created.replace('Z', '+00:00')),
                updated=datetime.fromisoformat(issue.fields.updated.replace('Z', '+00:00')),
                resolved=datetime.fromisoformat(issue.fields.resolutiondate.replace('Z', '+00:00')) if issue.fields.resolutiondate else None,
                labels=issue.fields.labels or [],
                assignee=issue.fields.assignee.displayName if issue.fields.assignee else None,
                reporter=issue.fields.reporter.displayName if issue.fields.reporter else None,
                description=issue.fields.description or "",
                url=f"{self.server}/browse/{issue.key}",
                components=[c.name for c in issue.fields.components] if issue.fields.components else [],
                fix_versions=[v.name for v in issue.fields.fixVersions] if issue.fields.fixVersions else []
            ))
        
        return issues
    
    def get_issues_by_fix_version(
        self,
        project: str,
        version: str,
        max_results: int = 100
    ) -> List[JiraIssue]:
        """
        Fetch issues for a specific fix version.
        
        Args:
            project: Jira project key
            version: Fix version name
            max_results: Maximum number of results
        
        Returns:
            List of JiraIssue objects
        """
        jql = f'project = {project} AND fixVersion = "{version}" ORDER BY created DESC'
        issues = []
        
        jira_issues = self.jira.search_issues(jql, maxResults=max_results)
        
        for issue in jira_issues:
            issues.append(JiraIssue(
                key=issue.key,
                summary=issue.fields.summary,
                status=issue.fields.status.name,
                issue_type=issue.fields.issuetype.name,
                priority=issue.fields.priority.name if issue.fields.priority else None,
                created=datetime.fromisoformat(issue.fields.created.replace('Z', '+00:00')),
                updated=datetime.fromisoformat(issue.fields.updated.replace('Z', '+00:00')),
                resolved=datetime.fromisoformat(issue.fields.resolutiondate.replace('Z', '+00:00')) if issue.fields.resolutiondate else None,
                labels=issue.fields.labels or [],
                assignee=issue.fields.assignee.displayName if issue.fields.assignee else None,
                reporter=issue.fields.reporter.displayName if issue.fields.reporter else None,
                description=issue.fields.description or "",
                url=f"{self.server}/browse/{issue.key}",
                components=[c.name for c in issue.fields.components] if issue.fields.components else [],
                fix_versions=[v.name for v in issue.fields.fixVersions] if issue.fields.fixVersions else []
            ))
        
        return issues
