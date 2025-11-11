"""Risk assessment engine that combines all analyzers."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from risk_assessor.core.issue_catalog import IssueCatalog, CatalogedIssue
from risk_assessor.analyzers.complexity import ComplexityAnalyzer
from risk_assessor.analyzers.llm_analyzer import LLMAnalyzer
from risk_assessor.integrations.github_client import GitHubClient, GitHubIssue, GitHubPullRequest
from risk_assessor.integrations.jira_client import JiraClient, JiraIssue
from risk_assessor.utils.config import Config


class RiskEngine:
    """Main engine for risk assessment."""
    
    def __init__(self, config: Config):
        """
        Initialize risk engine.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.catalog = IssueCatalog(config.catalog_path)
        self.complexity_analyzer = ComplexityAnalyzer()
        
        # Initialize LLM analyzer if configured
        self.llm_analyzer = None
        if config.llm.api_key:
            self.llm_analyzer = LLMAnalyzer(
                api_key=config.llm.api_key,
                model=config.llm.model,
                api_base=config.llm.api_base,
                temperature=config.llm.temperature
            )
        
        # Initialize GitHub client if configured
        self.github_client = None
        if config.github.token and config.github.repo:
            self.github_client = GitHubClient(
                token=config.github.token,
                repo_name=config.github.repo
            )
        
        # Initialize Jira client if configured
        self.jira_client = None
        if config.jira.server and config.jira.username and config.jira.token:
            self.jira_client = JiraClient(
                server=config.jira.server,
                username=config.jira.username,
                token=config.jira.token
            )
    
    def sync_github_issues(self, state: str = "all", labels: Optional[List[str]] = None):
        """
        Sync GitHub issues to catalog.
        
        Args:
            state: Issue state filter
            labels: Label filter
        """
        if not self.github_client:
            raise ValueError("GitHub client not configured")
        
        issues = self.github_client.get_issues(state=state, labels=labels)
        
        for issue in issues:
            cataloged = CatalogedIssue(
                source="github",
                identifier=str(issue.number),
                title=issue.title,
                status=issue.state,
                severity=self._extract_severity_from_labels(issue.labels),
                components=[],
                labels=issue.labels,
                created_at=issue.created_at.isoformat(),
                resolved_at=issue.closed_at.isoformat() if issue.closed_at else None,
                description=issue.body,
                related_files=[],
                url=issue.url
            )
            self.catalog.add_issue(cataloged)
        
        self.catalog.save()
        return len(issues)
    
    def sync_jira_issues(
        self,
        project: str,
        status: Optional[List[str]] = None,
        max_results: int = 100
    ):
        """
        Sync Jira issues to catalog.
        
        Args:
            project: Jira project key
            status: Status filter
            max_results: Maximum number of results
        """
        if not self.jira_client:
            raise ValueError("Jira client not configured")
        
        issues = self.jira_client.get_issues(
            project=project,
            status=status,
            max_results=max_results
        )
        
        for issue in issues:
            cataloged = CatalogedIssue(
                source="jira",
                identifier=issue.key,
                title=issue.summary,
                status=issue.status,
                severity=issue.priority,
                components=issue.components,
                labels=issue.labels,
                created_at=issue.created.isoformat(),
                resolved_at=issue.resolved.isoformat() if issue.resolved else None,
                description=issue.description,
                related_files=[],
                url=issue.url
            )
            self.catalog.add_issue(cataloged)
        
        self.catalog.save()
        return len(issues)
    
    def assess_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """
        Assess risk for a GitHub pull request.
        
        Args:
            pr_number: Pull request number
        
        Returns:
            Risk assessment results
        """
        if not self.github_client:
            raise ValueError("GitHub client not configured")
        
        # Get PR details
        prs = self.github_client.get_pull_requests(state="all")
        pr = None
        for p in prs:
            if p.number == pr_number:
                pr = p
                break
        
        if not pr:
            raise ValueError(f"Pull request #{pr_number} not found")
        
        # Get PR files
        files = self.github_client.get_pr_files(pr_number)
        file_paths = [f['filename'] for f in files]
        
        return self._assess_changes(
            files_changed=file_paths,
            additions=pr.additions,
            deletions=pr.deletions,
            commits=pr.commits,
            title=pr.title,
            description=pr.body
        )
    
    def assess_commits(self, base_ref: str, head_ref: str) -> Dict[str, Any]:
        """
        Assess risk for commits between two refs.
        
        Args:
            base_ref: Base reference (branch/tag/SHA)
            head_ref: Head reference (branch/tag/SHA)
        
        Returns:
            Risk assessment results
        """
        if not self.github_client:
            raise ValueError("GitHub client not configured")
        
        # Get commits
        commits = self.github_client.get_commits_between_refs(base_ref, head_ref)
        
        if not commits:
            return {
                'error': f'No commits found between {base_ref}..{head_ref}',
                'overall_risk_score': 0.0,
                'risk_level': 'low'
            }
        
        # Aggregate changes
        all_files = set()
        total_additions = 0
        total_deletions = 0
        
        for commit in commits:
            all_files.update(commit.get('files_changed', []))
            total_additions += commit.get('additions', 0)
            total_deletions += commit.get('deletions', 0)
        
        return self._assess_changes(
            files_changed=list(all_files),
            additions=total_additions,
            deletions=total_deletions,
            commits=len(commits),
            title=f"Changes from {base_ref} to {head_ref}",
            description=f"Analyzing {len(commits)} commits"
        )
    
    def _assess_changes(
        self,
        files_changed: List[str],
        additions: int,
        deletions: int,
        commits: int,
        title: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Internal method to assess changes.
        
        Args:
            files_changed: List of changed files
            additions: Lines added
            deletions: Lines deleted
            commits: Number of commits
            title: Change title
            description: Change description
        
        Returns:
            Complete risk assessment
        """
        # Analyze complexity
        complexity_analysis = self.complexity_analyzer.analyze_changes(
            files_changed=files_changed,
            additions=additions,
            deletions=deletions,
            commits=commits
        )
        
        # Find related historical issues
        related_issues = self.catalog.search_by_files(files_changed)
        
        # Calculate history-based risk score
        history_score = self._calculate_history_score(related_issues)
        
        # LLM analysis if available
        llm_analysis = None
        llm_score = 0.5  # Default medium risk
        
        if self.llm_analyzer:
            llm_analysis = self.llm_analyzer.analyze_deployment_risk(
                changes_summary=complexity_analysis,
                historical_issues=[issue.to_dict() for issue in related_issues[:10]],
                deployment_context=None
            )
            llm_score = llm_analysis['risk_score']
        
        # Calculate overall risk score
        overall_score = (
            complexity_analysis['complexity_score'] * self.config.thresholds.complexity_weight +
            history_score * self.config.thresholds.history_weight +
            llm_score * self.config.thresholds.llm_weight
        )
        
        # Determine risk level
        if overall_score < self.config.thresholds.low_threshold:
            risk_level = "low"
        elif overall_score < self.config.thresholds.medium_threshold:
            risk_level = "medium"
        elif overall_score < self.config.thresholds.high_threshold:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        return {
            'title': title,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'complexity_analysis': complexity_analysis,
            'history_analysis': {
                'related_issues_count': len(related_issues),
                'related_issues': [issue.to_dict() for issue in related_issues[:5]],
                'history_risk_score': history_score
            },
            'llm_analysis': llm_analysis,
            'overall_risk_score': overall_score,
            'risk_level': risk_level,
            'weights': {
                'complexity': self.config.thresholds.complexity_weight,
                'history': self.config.thresholds.history_weight,
                'llm': self.config.thresholds.llm_weight
            }
        }
    
    def _calculate_history_score(self, related_issues: List[CatalogedIssue]) -> float:
        """
        Calculate risk score based on historical issues.
        
        Args:
            related_issues: List of related issues
        
        Returns:
            Risk score (0-1)
        """
        if not related_issues:
            return 0.0
        
        # Count issues by severity
        severity_weights = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3,
            None: 0.4
        }
        
        total_weight = 0.0
        for issue in related_issues:
            severity = issue.severity.lower() if issue.severity else None
            weight = severity_weights.get(severity, 0.4)
            total_weight += weight
        
        # Normalize based on number of issues
        # More related issues = higher risk
        score = min(1.0, total_weight / 10.0)
        
        return score
    
    def _extract_severity_from_labels(self, labels: List[str]) -> Optional[str]:
        """Extract severity from labels."""
        severity_keywords = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
            'p0': 'critical',
            'p1': 'high',
            'p2': 'medium',
            'p3': 'low',
            'priority: critical': 'critical',
            'priority: high': 'high',
            'priority: medium': 'medium',
            'priority: low': 'low',
        }
        
        for label in labels:
            label_lower = label.lower()
            if label_lower in severity_keywords:
                return severity_keywords[label_lower]
        
        return None
