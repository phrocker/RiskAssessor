#!/usr/bin/env python3
"""
Example demonstrating the incident feedback mechanism.

This example shows how to:
1. Record incident feedback
2. View feedback
3. See how feedback affects risk assessments
"""

from datetime import datetime, timedelta
import json

from risk_assessor import RiskEngine, FeedbackCatalog
from risk_assessor.utils.config import Config


def main():
    """Run feedback mechanism example."""
    
    print("=" * 70)
    print("RiskAssessor - Incident Feedback Mechanism Example")
    print("=" * 70)
    print()
    
    # Initialize (use environment variables or defaults)
    try:
        config = Config.from_env()
    except:
        # If no config, create a minimal one for demo
        config = Config.from_dict({
            'github': {'token': '', 'repo': 'demo/repo'},
            'jira': {'server': '', 'username': '', 'token': '', 'project': ''},
            'llm': {'api_key': '', 'model': 'gpt-4'},
            'thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8,
                'complexity_weight': 0.3,
                'history_weight': 0.3,
                'llm_weight': 0.4
            },
            'catalog_path': '.risk_assessor/catalog.json'
        })
    
    engine = RiskEngine(config)
    
    # Example 1: Record a critical incident
    print("Example 1: Recording a Critical Incident")
    print("-" * 70)
    
    incident_date = (datetime.now() - timedelta(days=5)).isoformat()
    
    entry1 = engine.record_incident_feedback(
        incident_date=incident_date,
        severity="critical",
        incident_type="outage",
        description="Production database connection pool exhausted, causing complete service outage",
        root_cause="Connection leak due to missing finally block in database wrapper",
        affected_files=[
            "src/database/connection.py",
            "src/database/pool.py"
        ],
        missed_indicators=[
            "No connection pool monitoring in place",
            "Missing connection timeout configuration",
            "No automated connection leak detection"
        ],
        resolution="Added finally blocks to ensure connections are released, added connection pool monitoring",
        lessons_learned=[
            "Always use context managers or try/finally for resource management",
            "Monitor connection pool metrics in production",
            "Add connection pool exhaustion alerts"
        ],
        pr_number=456,
        commit_sha="abc123def",
        original_risk_score=0.35,
        original_risk_level="medium",
        time_to_resolve_hours=3.5
    )
    
    print(f"✓ Recorded incident: {entry1.id}")
    print(f"  Severity: {entry1.severity}")
    print(f"  Type: {entry1.incident_type}")
    print(f"  Affected files: {len(entry1.affected_files)}")
    print(f"  Time to resolve: {entry1.time_to_resolve_hours} hours")
    print()
    
    # Example 2: Record a high severity performance issue
    print("Example 2: Recording a High Severity Performance Issue")
    print("-" * 70)
    
    incident_date2 = (datetime.now() - timedelta(days=15)).isoformat()
    
    entry2 = engine.record_incident_feedback(
        incident_date=incident_date2,
        severity="high",
        incident_type="performance",
        description="API response times degraded to 5+ seconds under load",
        root_cause="N+1 query problem in user search endpoint",
        affected_files=[
            "src/api/search.py",
            "src/database/queries.py"
        ],
        missed_indicators=[
            "No performance testing in CI",
            "Query count not monitored during code review"
        ],
        resolution="Optimized query to use joins instead of sequential queries",
        lessons_learned=[
            "Add query count assertions to tests",
            "Require performance testing for database-heavy endpoints"
        ],
        pr_number=423,
        original_risk_score=0.42,
        original_risk_level="medium",
        time_to_resolve_hours=6.0
    )
    
    print(f"✓ Recorded incident: {entry2.id}")
    print(f"  Severity: {entry2.severity}")
    print(f"  Type: {entry2.incident_type}")
    print()
    
    # Example 3: View feedback statistics
    print("Example 3: Viewing Feedback Statistics")
    print("-" * 70)
    
    stats = engine.get_feedback_statistics()
    print(f"Total incidents recorded: {stats['total_entries']}")
    print(f"\nBy Severity:")
    for severity, count in sorted(stats['by_severity'].items()):
        print(f"  {severity.capitalize()}: {count}")
    print(f"\nBy Type:")
    for inc_type, count in sorted(stats['by_incident_type'].items()):
        print(f"  {inc_type.capitalize()}: {count}")
    if stats['average_resolution_hours']:
        print(f"\nAverage Resolution Time: {stats['average_resolution_hours']:.1f} hours")
    print()
    
    # Example 4: Search for feedback by file
    print("Example 4: Searching for Feedback by File")
    print("-" * 70)
    
    related = engine.feedback.search_by_files(["src/database/connection.py"])
    print(f"Found {len(related)} incident(s) involving 'src/database/connection.py':")
    for fb in related:
        print(f"  - {fb.severity.upper()}: {fb.description[:60]}...")
    print()
    
    # Example 5: Calculate feedback risk score
    print("Example 5: Calculating Risk Score from Feedback")
    print("-" * 70)
    
    # For database files
    db_files = ["src/database/connection.py", "src/database/pool.py"]
    db_risk = engine.feedback.calculate_feedback_risk_score(db_files)
    print(f"Risk score for database files: {db_risk:.2f}")
    print(f"  (High score due to {len(related)} critical/high incidents)")
    
    # For unrelated files
    other_files = ["src/frontend/ui.js"]
    other_risk = engine.feedback.calculate_feedback_risk_score(other_files)
    print(f"Risk score for frontend files: {other_risk:.2f}")
    print(f"  (Low score - no incidents recorded)")
    print()
    
    # Example 6: Show how feedback affects assessments
    print("Example 6: Impact on Risk Assessments")
    print("-" * 70)
    print("When assessing changes to database files, the system will:")
    print("  1. Find related incidents automatically")
    print("  2. Weight them heavily (60% vs 40% for traditional issues)")
    print("  3. Add 'Incident History (Feedback)' as a risk factor")
    print("  4. Increase overall risk score")
    print()
    print("Example risk factor in contract:")
    print(json.dumps({
        "category": "operational",
        "factor_name": "Incident History (Feedback)",
        "impact_weight": 0.18,
        "observed_value": f"{len(related)} related incidents in feedback",
        "assessment": f"Similar changes caused {len(related)} critical incident(s) previously"
    }, indent=2))
    print()
    
    # Example 7: View recent feedback
    print("Example 7: Viewing Recent Feedback")
    print("-" * 70)
    
    recent = engine.feedback.get_recent_feedback(days=30)
    print(f"Incidents in the last 30 days: {len(recent)}")
    for fb in recent:
        print(f"  - [{fb.severity.upper()}] {fb.incident_date[:10]}: {fb.description[:50]}...")
    print()
    
    print("=" * 70)
    print("Feedback mechanism allows continuous learning from actual incidents!")
    print("This helps prevent similar issues in the future.")
    print("=" * 70)


if __name__ == '__main__':
    main()
