"""GitHub integration for fetching issues and pull requests."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from github import Github, Repository, Issue, PullRequest
from dataclasses import dataclass, asdict


@dataclass
class GitHubIssue:
    """Represents a GitHub issue."""
    
    number: int
    title: str
    state: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    labels: List[str]
    assignees: List[str]
    body: str
    url: str
    is_pull_request: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime objects to strings
        for key in ['created_at', 'updated_at', 'closed_at']:
            if data[key]:
                data[key] = data[key].isoformat()
        return data


@dataclass
class GitHubPullRequest:
    """Represents a GitHub pull request."""
    
    number: int
    title: str
    state: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    merged_at: Optional[datetime]
    labels: List[str]
    assignees: List[str]
    body: str
    url: str
    commits: int
    additions: int
    deletions: int
    changed_files: int
    base_ref: str
    head_ref: str
    merged: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime objects to strings
        for key in ['created_at', 'updated_at', 'closed_at', 'merged_at']:
            if data[key]:
                data[key] = data[key].isoformat()
        return data


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, token: str, repo_name: str):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
            repo_name: Repository name in format 'owner/repo'
        """
        self.github = Github(token)
        self.repo: Repository.Repository = self.github.get_repo(repo_name)
        self.repo_name = repo_name
    
    def get_issues(
        self,
        state: str = "all",
        labels: Optional[List[str]] = None,
        since: Optional[datetime] = None
    ) -> List[GitHubIssue]:
        """
        Fetch issues from GitHub repository.
        
        Args:
            state: Issue state ('open', 'closed', or 'all')
            labels: Filter by labels
            since: Only issues updated after this date
        
        Returns:
            List of GitHubIssue objects
        """
        issues = []
        
        github_issues = self.repo.get_issues(
            state=state,
            labels=labels or [],
            since=since
        )
        
        for issue in github_issues:
            # Skip pull requests when fetching issues
            if issue.pull_request:
                continue
            
            issues.append(GitHubIssue(
                number=issue.number,
                title=issue.title,
                state=issue.state,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
                closed_at=issue.closed_at,
                labels=[label.name for label in issue.labels],
                assignees=[assignee.login for assignee in issue.assignees],
                body=issue.body or "",
                url=issue.html_url,
                is_pull_request=False
            ))
        
        return issues
    
    def get_pull_requests(
        self,
        state: str = "all",
        base: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc"
    ) -> List[GitHubPullRequest]:
        """
        Fetch pull requests from GitHub repository.
        
        Args:
            state: PR state ('open', 'closed', or 'all')
            base: Base branch name
            sort: Sort field ('created', 'updated', 'popularity', 'long-running')
            direction: Sort direction ('asc' or 'desc')
        
        Returns:
            List of GitHubPullRequest objects
        """
        prs = []
        
        github_prs = self.repo.get_pulls(
            state=state,
            base=base,
            sort=sort,
            direction=direction
        )
        
        for pr in github_prs:
            prs.append(GitHubPullRequest(
                number=pr.number,
                title=pr.title,
                state=pr.state,
                created_at=pr.created_at,
                updated_at=pr.updated_at,
                closed_at=pr.closed_at,
                merged_at=pr.merged_at,
                labels=[label.name for label in pr.labels],
                assignees=[assignee.login for assignee in pr.assignees],
                body=pr.body or "",
                url=pr.html_url,
                commits=pr.commits,
                additions=pr.additions,
                deletions=pr.deletions,
                changed_files=pr.changed_files,
                base_ref=pr.base.ref,
                head_ref=pr.head.ref,
                merged=pr.merged
            ))
        
        return prs
    
    def get_commits_between_refs(
        self,
        base: str,
        head: str
    ) -> List[Dict[str, Any]]:
        """
        Get commits between two refs (branches, tags, or SHAs).
        
        Args:
            base: Base reference
            head: Head reference
        
        Returns:
            List of commit information dictionaries
        """
        commits = []
        
        try:
            comparison = self.repo.compare(base, head)
            
            for commit in comparison.commits:
                commits.append({
                    'sha': commit.sha,
                    'message': commit.commit.message,
                    'author': commit.commit.author.name,
                    'date': commit.commit.author.date.isoformat(),
                    'files_changed': [f.filename for f in commit.files] if commit.files else [],
                    'additions': sum(f.additions for f in commit.files) if commit.files else 0,
                    'deletions': sum(f.deletions for f in commit.files) if commit.files else 0,
                    'url': commit.html_url
                })
        except Exception as e:
            print(f"Error comparing {base}..{head}: {e}")
        
        return commits
    
    def get_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get files changed in a pull request.
        
        Args:
            pr_number: Pull request number
        
        Returns:
            List of file change information
        """
        pr = self.repo.get_pull(pr_number)
        files = []
        
        for file in pr.get_files():
            files.append({
                'filename': file.filename,
                'status': file.status,
                'additions': file.additions,
                'deletions': file.deletions,
                'changes': file.changes,
                'patch': file.patch if hasattr(file, 'patch') else None
            })
        
        return files
