"""Risk assessment engine that combines all analyzers."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from risk_assessor.core.issue_catalog import IssueCatalog, CatalogedIssue
from risk_assessor.core.feedback import FeedbackCatalog, FeedbackEntry
from risk_assessor.core.contracts import (
    RiskContract, RiskSummary, RiskFactor, 
    HistoricalContext, ModelDetails
)
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
        self.feedback = FeedbackCatalog()  # Uses default path
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
        
        # Calculate history-based risk score (now includes feedback)
        history_score = self._calculate_history_score(related_issues, files_changed)
        
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
        
        # Get feedback for these files
        related_feedback = self.feedback.search_by_files(files_changed)
        
        return {
            'title': title,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'complexity_analysis': complexity_analysis,
            'history_analysis': {
                'related_issues_count': len(related_issues),
                'related_issues': [issue.to_dict() for issue in related_issues[:5]],
                'related_feedback_count': len(related_feedback),
                'related_feedback': [fb.to_dict() for fb in related_feedback[:5]],
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
    
    def _calculate_history_score(
        self, 
        related_issues: List[CatalogedIssue],
        files_changed: List[str]
    ) -> float:
        """
        Calculate risk score based on historical issues and feedback.
        
        Args:
            related_issues: List of related issues
            files_changed: List of files being changed
        
        Returns:
            Risk score (0-1)
        """
        # Calculate traditional issue-based score
        issue_score = 0.0
        if related_issues:
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
            issue_score = min(1.0, total_weight / 10.0)
        
        # Calculate feedback-based score
        feedback_score = self.feedback.calculate_feedback_risk_score(files_changed)
        
        # Combine scores - feedback is weighted more heavily as it represents
        # actual incidents that occurred
        # 40% traditional issues, 60% feedback from actual incidents
        combined_score = (issue_score * 0.4) + (feedback_score * 0.6)
        
        return combined_score
    
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
    
    def assess_pull_request_contract(
        self, 
        pr_number: int,
        deployment_region: str = "unknown",
        branch: Optional[str] = None
    ) -> RiskContract:
        """
        Assess risk for a GitHub pull request and return a risk contract.
        
        Args:
            pr_number: Pull request number
            deployment_region: Target deployment region
            branch: Target branch (if None, will use PR branch)
        
        Returns:
            RiskContract object
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
        
        return self._generate_risk_contract(
            changeset_id=f"pr-{pr_number}",
            files_changed=file_paths,
            additions=pr.additions,
            deletions=pr.deletions,
            commits=pr.commits,
            title=pr.title,
            description=pr.body,
            repository=self.config.github.repo,
            branch=branch or pr.base.ref,
            deployment_region=deployment_region
        )
    
    def assess_commits_contract(
        self, 
        base_ref: str, 
        head_ref: str,
        deployment_region: str = "unknown"
    ) -> RiskContract:
        """
        Assess risk for commits between two refs and return a risk contract.
        
        Args:
            base_ref: Base reference (branch/tag/SHA)
            head_ref: Head reference (branch/tag/SHA)
            deployment_region: Target deployment region
        
        Returns:
            RiskContract object
        """
        if not self.github_client:
            raise ValueError("GitHub client not configured")
        
        # Get commits
        commits = self.github_client.get_commits_between_refs(base_ref, head_ref)
        
        if not commits:
            # Return a low-risk contract for no changes
            changeset_id = f"changeset-{uuid.uuid4().hex[:12]}"
            timestamp = datetime.now().isoformat()
            
            return RiskContract(
                id=changeset_id,
                timestamp=timestamp,
                repository=self.config.github.repo,
                branch=head_ref,
                deployment_region=deployment_region,
                risk_summary=RiskSummary(
                    risk_score=0.0,
                    risk_level="LOW",
                    confidence=1.0,
                    overall_assessment="No changes detected between refs."
                ),
                factors=[],
                recommendations=["No changes to deploy."],
                historical_context=HistoricalContext(
                    previous_similar_changes=0,
                    previous_incidents_in_region=0,
                    last_incident_cause=None,
                    time_since_last_outage_days=None
                ),
                model_details=ModelDetails(
                    model_version="2.0.0",
                    model_type="hybrid_rule_ml",
                    trained_on_releases=None,
                    last_updated=None
                ),
                text_summary="No changes detected between refs."
            )
        
        # Aggregate changes
        all_files = set()
        total_additions = 0
        total_deletions = 0
        
        for commit in commits:
            all_files.update(commit.get('files_changed', []))
            total_additions += commit.get('additions', 0)
            total_deletions += commit.get('deletions', 0)
        
        return self._generate_risk_contract(
            changeset_id=f"changeset-{uuid.uuid4().hex[:12]}",
            files_changed=list(all_files),
            additions=total_additions,
            deletions=total_deletions,
            commits=len(commits),
            title=f"Changes from {base_ref} to {head_ref}",
            description=f"Analyzing {len(commits)} commits",
            repository=self.config.github.repo,
            branch=head_ref,
            deployment_region=deployment_region
        )
    
    def _generate_risk_contract(
        self,
        changeset_id: str,
        files_changed: List[str],
        additions: int,
        deletions: int,
        commits: int,
        title: str,
        description: str,
        repository: str,
        branch: str,
        deployment_region: str
    ) -> RiskContract:
        """
        Generate a risk contract from change analysis.
        
        Args:
            changeset_id: Unique identifier for this changeset
            files_changed: List of changed files
            additions: Lines added
            deletions: Lines deleted
            commits: Number of commits
            title: Change title
            description: Change description
            repository: Repository name
            branch: Target branch
            deployment_region: Deployment region
        
        Returns:
            RiskContract object
        """
        # Perform analysis
        complexity_analysis = self.complexity_analyzer.analyze_changes(
            files_changed=files_changed,
            additions=additions,
            deletions=deletions,
            commits=commits
        )
        
        # Find related historical issues
        related_issues = self.catalog.search_by_files(files_changed)
        
        # Calculate history-based risk score (now includes feedback)
        history_score = self._calculate_history_score(related_issues, files_changed)
        
        # LLM analysis if available
        llm_analysis = None
        llm_score = 0.5  # Default medium risk
        llm_recommendations = []
        
        if self.llm_analyzer:
            llm_analysis = self.llm_analyzer.analyze_deployment_risk(
                changes_summary=complexity_analysis,
                historical_issues=[issue.to_dict() for issue in related_issues[:10]],
                deployment_context=None
            )
            llm_score = llm_analysis['risk_score']
            llm_recommendations = llm_analysis.get('recommendations', [])
        
        # Calculate overall risk score
        overall_score = (
            complexity_analysis['complexity_score'] * self.config.thresholds.complexity_weight +
            history_score * self.config.thresholds.history_weight +
            llm_score * self.config.thresholds.llm_weight
        )
        
        # Determine risk level using new thresholds
        # LOW: < 0.33, MEDIUM: 0.33-0.66, HIGH: > 0.66
        if overall_score < 0.33:
            risk_level = "LOW"
        elif overall_score < 0.66:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Calculate confidence (average of available analysis confidence)
        confidence = 0.85  # Base confidence
        if llm_analysis and 'confidence' in llm_analysis:
            confidence = llm_analysis['confidence']
        
        # Generate factors
        factors = self._generate_risk_factors(
            complexity_analysis=complexity_analysis,
            history_score=history_score,
            related_issues=related_issues,
            llm_score=llm_score,
            files_changed=files_changed
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level=risk_level,
            complexity_analysis=complexity_analysis,
            llm_recommendations=llm_recommendations,
            related_issues=related_issues
        )
        
        # Generate historical context
        historical_context = self._generate_historical_context(related_issues)
        
        # Generate overall assessment
        overall_assessment = self._generate_overall_assessment(
            risk_level=risk_level,
            overall_score=overall_score,
            factors=factors,
            deployment_region=deployment_region
        )
        
        # Generate text summary
        text_summary = self._generate_text_summary(
            risk_level=risk_level,
            overall_score=overall_score,
            deployment_region=deployment_region,
            factors=factors,
            recommendations=recommendations
        )
        
        return RiskContract(
            id=changeset_id,
            timestamp=datetime.now().isoformat(),
            repository=repository,
            branch=branch,
            deployment_region=deployment_region,
            risk_summary=RiskSummary(
                risk_score=round(overall_score, 2),
                risk_level=risk_level,
                confidence=round(confidence, 2),
                overall_assessment=overall_assessment
            ),
            factors=factors,
            recommendations=recommendations,
            historical_context=historical_context,
            model_details=ModelDetails(
                model_version="2.0.0",
                model_type="hybrid_rule_ml",
                trained_on_releases=len(self.catalog.issues) if self.catalog.issues else None,
                last_updated=datetime.now().strftime("%Y-%m-%d")
            ),
            text_summary=text_summary
        )
    
    def _generate_risk_factors(
        self,
        complexity_analysis: Dict[str, Any],
        history_score: float,
        related_issues: List[CatalogedIssue],
        llm_score: float,
        files_changed: List[str]
    ) -> List[RiskFactor]:
        """Generate risk factors from analysis results."""
        factors = []
        
        # Code complexity factor
        total_changes = complexity_analysis['total_changes']
        num_files = complexity_analysis['files_changed']
        
        code_weight = self.config.thresholds.complexity_weight * 0.6
        factors.append(RiskFactor(
            category="code",
            factor_name="Change Volume",
            impact_weight=round(code_weight, 2),
            observed_value=f"{total_changes} lines changed across {num_files} files",
            assessment=self._assess_change_volume(total_changes, num_files)
        ))
        
        # Configuration factor
        critical_files = complexity_analysis['critical_files']
        if critical_files:
            config_weight = self.config.thresholds.complexity_weight * 0.4
            factors.append(RiskFactor(
                category="configuration",
                factor_name="Critical Files Modified",
                impact_weight=round(config_weight, 2),
                observed_value=f"{len(critical_files)} critical files affected",
                assessment=f"Modified files include: {', '.join(critical_files[:3])}"
            ))
        
        # Feedback-based factor (new!)
        related_feedback = self.feedback.search_by_files(files_changed)
        if related_feedback:
            # Weight feedback heavily as it represents actual incidents
            feedback_weight = self.config.thresholds.history_weight * 0.6
            
            # Count by severity
            critical_count = sum(1 for fb in related_feedback if fb.severity.lower() == 'critical')
            high_count = sum(1 for fb in related_feedback if fb.severity.lower() == 'high')
            
            assessment_parts = []
            if critical_count > 0:
                assessment_parts.append(f"{critical_count} critical incident(s)")
            if high_count > 0:
                assessment_parts.append(f"{high_count} high-severity incident(s)")
            
            assessment = f"Similar changes caused {', '.join(assessment_parts) if assessment_parts else f'{len(related_feedback)} incident(s)'} previously"
            
            factors.append(RiskFactor(
                category="operational",
                factor_name="Incident History (Feedback)",
                impact_weight=round(feedback_weight, 2),
                observed_value=f"{len(related_feedback)} related incidents in feedback",
                assessment=assessment
            ))
        
        # Historical issues factor
        if related_issues:
            history_weight = self.config.thresholds.history_weight * 0.4
            factors.append(RiskFactor(
                category="operational",
                factor_name="Historical Issues",
                impact_weight=round(history_weight, 2),
                observed_value=f"{len(related_issues)} related issues found",
                assessment=f"Similar changes have caused {len(related_issues)} issues in the past"
            ))
        
        # Testing/ownership factor (based on commits)
        commits = complexity_analysis.get('commits', 1)
        if commits > 0:
            ownership_weight = self.config.thresholds.llm_weight * 0.3
            factors.append(RiskFactor(
                category="ownership",
                factor_name="Change Distribution",
                impact_weight=round(ownership_weight, 2),
                observed_value=f"{commits} commits",
                assessment=self._assess_commit_distribution(commits, total_changes)
            ))
        
        return factors
    
    def _assess_change_volume(self, total_changes: int, files_changed: int) -> str:
        """Assess the volume of changes."""
        if total_changes > 1000 or files_changed > 15:
            return "Large changeset; above 90th percentile for this repository"
        elif total_changes > 500 or files_changed > 8:
            return "Moderate changeset; within normal range but requires review"
        else:
            return "Small changeset; within typical change size"
    
    def _assess_commit_distribution(self, commits: int, total_changes: int) -> str:
        """Assess commit distribution."""
        if commits == 0:
            return "No commit data available"
        
        changes_per_commit = total_changes / commits
        if changes_per_commit > 200:
            return "Few large commits; may indicate bulk changes"
        elif changes_per_commit < 10:
            return "Many small commits; good incremental development"
        else:
            return "Normal commit distribution"
    
    def _generate_recommendations(
        self,
        risk_level: str,
        complexity_analysis: Dict[str, Any],
        llm_recommendations: List[str],
        related_issues: List[CatalogedIssue]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Add LLM recommendations first
        if llm_recommendations:
            recommendations.extend(llm_recommendations[:3])  # Top 3 LLM recommendations
        
        # Add rule-based recommendations
        if risk_level == "HIGH":
            recommendations.append("Perform a canary deployment before full rollout")
            recommendations.append("Enable feature flag rollback hooks")
        
        if complexity_analysis['critical_files']:
            recommendations.append("Run extended smoke tests on configuration initialization paths")
            recommendations.append("Ensure validation tests cover all modified configuration files")
        
        if related_issues:
            recommendations.append("Review related historical issues to avoid known pitfalls")
        
        if complexity_analysis['total_changes'] > 500:
            recommendations.append("Consider breaking this change into smaller, incremental deployments")
        
        # Return unique recommendations
        return list(dict.fromkeys(recommendations))[:6]  # Max 6 recommendations
    
    def _generate_historical_context(
        self,
        related_issues: List[CatalogedIssue]
    ) -> HistoricalContext:
        """Generate historical context from related issues."""
        # Find recent incidents
        recent_incidents = [
            issue for issue in related_issues
            if issue.severity and issue.severity.lower() in ['critical', 'high']
        ]
        
        # Get last incident cause
        last_incident_cause = None
        time_since_last_outage = None
        
        if recent_incidents:
            # Sort by created_at (most recent first)
            sorted_incidents = sorted(
                recent_incidents,
                key=lambda x: x.created_at,
                reverse=True
            )
            if sorted_incidents:
                last_incident = sorted_incidents[0]
                last_incident_cause = last_incident.title or "Unknown cause"
                
                # Calculate days since incident
                try:
                    incident_date = datetime.fromisoformat(last_incident.created_at.replace('Z', '+00:00'))
                    days_since = (datetime.now(incident_date.tzinfo) - incident_date).days
                    time_since_last_outage = max(0, days_since)
                except:
                    pass
        
        return HistoricalContext(
            previous_similar_changes=len(related_issues),
            previous_incidents_in_region=len(recent_incidents),
            last_incident_cause=last_incident_cause,
            time_since_last_outage_days=time_since_last_outage
        )
    
    def _generate_overall_assessment(
        self,
        risk_level: str,
        overall_score: float,
        factors: List[RiskFactor],
        deployment_region: str
    ) -> str:
        """Generate overall assessment text."""
        if risk_level == "HIGH":
            primary_factor = max(factors, key=lambda f: f.impact_weight) if factors else None
            driver = primary_factor.factor_name.lower() if primary_factor else "multiple factors"
            return f"High risk of outage due to {driver} and deployment to {deployment_region}."
        elif risk_level == "MEDIUM":
            return f"Moderate risk deployment with potential for service disruption in {deployment_region}."
        else:
            return f"Low risk deployment with standard monitoring recommended for {deployment_region}."
    
    def _generate_text_summary(
        self,
        risk_level: str,
        overall_score: float,
        deployment_region: str,
        factors: List[RiskFactor],
        recommendations: List[str]
    ) -> str:
        """Generate natural language summary."""
        score_pct = int(overall_score * 100)
        
        # Get primary drivers
        drivers = []
        for factor in sorted(factors, key=lambda f: f.impact_weight, reverse=True)[:3]:
            drivers.append(factor.factor_name.lower())
        
        driver_text = ", ".join(drivers) if drivers else "various factors"
        
        # Build summary
        summary = (
            f"Risk Assessor v2 detected a {risk_level} likelihood ({score_pct}%) that this "
            f"deployment could cause service instability in {deployment_region}. "
            f"The primary drivers are {driver_text}. "
        )
        
        # Add recommendation highlights
        if recommendations:
            top_rec = recommendations[0]
            summary += f"{top_rec.capitalize()} is strongly recommended."
        
        return summary
    
    def record_incident_feedback(
        self,
        incident_date: str,
        severity: str,
        incident_type: str,
        description: str,
        root_cause: str,
        affected_files: List[str],
        missed_indicators: List[str],
        resolution: str,
        lessons_learned: List[str],
        changeset_id: Optional[str] = None,
        pr_number: Optional[int] = None,
        commit_sha: Optional[str] = None,
        original_risk_score: Optional[float] = None,
        original_risk_level: Optional[str] = None,
        time_to_resolve_hours: Optional[float] = None
    ) -> FeedbackEntry:
        """
        Record feedback about an incident that occurred.
        
        This allows the system to learn from incidents that were not
        properly identified during risk assessment.
        
        Args:
            incident_date: When the incident occurred (ISO format)
            severity: Severity level (critical, high, medium, low)
            incident_type: Type of incident (outage, performance, security, etc.)
            description: What happened
            root_cause: What caused the incident
            affected_files: Files involved in the incident
            missed_indicators: What should have been caught
            resolution: How it was fixed
            lessons_learned: What to watch for next time
            changeset_id: ID of the assessment that missed this (optional)
            pr_number: PR number if applicable (optional)
            commit_sha: Commit SHA if applicable (optional)
            original_risk_score: What was the score given (optional)
            original_risk_level: What was the level given (optional)
            time_to_resolve_hours: How long to fix (optional)
        
        Returns:
            The created FeedbackEntry
        """
        # Generate unique ID
        feedback_id = f"feedback-{uuid.uuid4().hex[:12]}"
        
        # Create feedback entry
        entry = FeedbackEntry(
            id=feedback_id,
            timestamp=datetime.now().isoformat(),
            incident_date=incident_date,
            changeset_id=changeset_id,
            pr_number=pr_number,
            commit_sha=commit_sha,
            severity=severity,
            incident_type=incident_type,
            description=description,
            root_cause=root_cause,
            affected_files=affected_files,
            missed_indicators=missed_indicators,
            original_risk_score=original_risk_score,
            original_risk_level=original_risk_level,
            resolution=resolution,
            time_to_resolve_hours=time_to_resolve_hours,
            lessons_learned=lessons_learned
        )
        
        # Add to catalog and save
        self.feedback.add_feedback(entry)
        self.feedback.save()
        
        return entry
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about recorded incident feedback.
        
        Returns:
            Dictionary of statistics
        """
        return self.feedback.get_statistics()
