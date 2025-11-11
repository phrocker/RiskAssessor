# Risk Feedback Mechanism

The Risk Feedback Mechanism allows you to record incidents that occurred after deployment and use them to improve future risk assessments. This creates a feedback loop where the RiskAssessor learns from actual incidents, especially those that were initially missed or underestimated.

## Overview

When an incident occurs that wasn't properly identified during risk assessment, you can record detailed feedback about:
- What happened
- What files were involved
- What should have been caught
- How it was resolved
- Lessons learned

This feedback is then automatically incorporated into future risk assessments for similar file changes, helping prevent similar incidents.

## Recording Incident Feedback

### Using the CLI

Record an incident using the `record-incident` command:

```bash
risk-assessor record-incident \
  --incident-date "2025-11-10T15:30:00Z" \
  --severity critical \
  --incident-type outage \
  --description "Production API service went down due to memory leak" \
  --root-cause "Memory leak in connection pooling code" \
  --affected-files "src/api/server.py" \
  --affected-files "src/database/pool.py" \
  --missed-indicator "No memory profiling in CI" \
  --missed-indicator "Missing connection timeout configuration" \
  --resolution "Added connection timeout and fixed memory leak" \
  --lessons-learned "Always profile memory usage for connection pool changes" \
  --lessons-learned "Add automated memory leak detection" \
  --pr-number 123 \
  --original-risk-score 0.35 \
  --original-risk-level medium \
  --time-to-resolve 2.5
```

### Using the Python API

```python
from risk_assessor import RiskEngine
from risk_assessor.utils.config import Config

# Initialize
config = Config.from_env()
engine = RiskEngine(config)

# Record feedback
entry = engine.record_incident_feedback(
    incident_date="2025-11-10T15:30:00Z",
    severity="critical",
    incident_type="outage",
    description="Production API service went down due to memory leak",
    root_cause="Memory leak in connection pooling code",
    affected_files=["src/api/server.py", "src/database/pool.py"],
    missed_indicators=[
        "No memory profiling in CI",
        "Missing connection timeout configuration"
    ],
    resolution="Added connection timeout and fixed memory leak",
    lessons_learned=[
        "Always profile memory usage for connection pool changes",
        "Add automated memory leak detection"
    ],
    pr_number=123,
    original_risk_score=0.35,
    original_risk_level="medium",
    time_to_resolve_hours=2.5
)

print(f"Feedback recorded with ID: {entry.id}")
```

## Viewing Feedback

### View All Recent Feedback

```bash
# View feedback from the last 90 days (default)
risk-assessor view-feedback

# View feedback from the last 180 days
risk-assessor view-feedback --recent-days 180
```

### Filter by Severity

```bash
risk-assessor view-feedback --severity critical
```

### Filter by Incident Type

```bash
risk-assessor view-feedback --incident-type outage
```

## Feedback Statistics

View statistics about recorded incidents:

```bash
risk-assessor feedback-stats
```

This shows:
- Total number of incidents
- Breakdown by severity
- Breakdown by incident type
- Average resolution time

## How Feedback Improves Risk Assessment

### Automatic Integration

When you perform a risk assessment, the system automatically:

1. **Searches for Related Feedback**: Looks for incidents involving similar files
2. **Calculates Feedback Risk Score**: Weights incidents by severity and recency
3. **Adjusts Overall Risk**: Incorporates feedback into the history-based risk score

### Weighting

Feedback is weighted more heavily than traditional issue tracking:
- **60%** weight for actual incident feedback
- **40%** weight for traditional issue history

This is because feedback represents confirmed incidents that actually occurred, making it a more reliable indicator of risk.

### Severity Impact

Different severities have different impacts on risk scoring:
- **Critical**: 1.0 weight (maximum impact)
- **High**: 0.8 weight
- **Medium**: 0.5 weight
- **Low**: 0.3 weight

### Recency Decay

More recent incidents have a stronger impact on risk scores. The influence of an incident decreases over time, with a decay factor based on how many days ago it occurred.

## Risk Contract Integration

When using Risk Contracts (v2.0), feedback is included as a dedicated risk factor:

```json
{
  "factors": [
    {
      "category": "operational",
      "factor_name": "Incident History (Feedback)",
      "impact_weight": 0.18,
      "observed_value": "2 related incidents in feedback",
      "assessment": "Similar changes caused 1 critical incident(s), 1 high-severity incident(s) previously"
    }
  ]
}
```

## Example Workflow

### 1. Initial Assessment

```bash
# Assess a PR
risk-assessor assess-pr-contract --pr 456 --deployment-region us-east-1 --output risk.json

# Review shows MEDIUM risk (0.45)
```

### 2. Deploy and Monitor

The deployment proceeds, but an incident occurs.

### 3. Record Feedback

```bash
risk-assessor record-incident \
  --incident-date "2025-11-11T14:00:00Z" \
  --severity high \
  --incident-type performance \
  --description "Database query timeout causing slow responses" \
  --root-cause "Missing index on new query pattern" \
  --affected-files "src/queries/user_search.py" \
  --missed-indicator "No query performance testing" \
  --resolution "Added database index" \
  --lessons-learned "Always test query performance with production-scale data" \
  --pr-number 456 \
  --original-risk-score 0.45 \
  --original-risk-level medium \
  --time-to-resolve 3.0
```

### 4. Future Assessments Benefit

Next time someone changes `src/queries/user_search.py` or similar query files:

```bash
risk-assessor assess-pr-contract --pr 500 --deployment-region us-east-1 --output risk2.json

# Now shows HIGH risk (0.72) due to feedback!
# Includes warning: "Similar changes caused 1 high-severity incident(s) previously"
```

## Storage

Feedback is stored in `.risk_assessor/feedback.json` in the repository root. This file contains all recorded incidents and can be:
- Committed to version control (recommended)
- Shared across team members
- Backed up separately
- Migrated between repositories

## Best Practices

1. **Record All Significant Incidents**: Even if they seem obvious in hindsight
2. **Be Specific About Files**: Include all files involved in the incident
3. **Document What Was Missed**: This helps improve detection patterns
4. **Include Lessons Learned**: Helps the team understand patterns
5. **Link to Original Assessments**: Use PR number or changeset ID when possible
6. **Track Resolution Time**: Helps understand incident impact
7. **Regular Review**: Periodically review feedback statistics to identify patterns

## Integration with CI/CD

You can integrate feedback into your CI/CD pipeline to automatically flag high-risk changes:

```yaml
- name: Assess Risk with Feedback
  run: |
    risk-assessor assess-pr-contract --pr ${{ github.event.pull_request.number }} \
      --deployment-region production --output risk.json
    
    # Check if feedback indicates high risk
    RISK_LEVEL=$(jq -r '.risk_summary.risk_level' risk.json)
    
    # Check for feedback-based factors
    FEEDBACK_FACTORS=$(jq '.factors[] | select(.factor_name == "Incident History (Feedback)")' risk.json)
    
    if [ ! -z "$FEEDBACK_FACTORS" ]; then
      echo "⚠️  Warning: Similar changes have caused incidents in the past"
      echo "$FEEDBACK_FACTORS"
    fi
    
    if [ "$RISK_LEVEL" = "HIGH" ]; then
      echo "::warning::High risk deployment - requires additional review"
    fi
```

## Privacy and Sensitivity

When recording incidents:
- Avoid including sensitive data (credentials, PII, etc.) in descriptions
- Focus on technical details and patterns
- Consider sanitizing production data references
- Review feedback before committing to version control

## Troubleshooting

### Feedback Not Appearing in Assessments

1. Check that feedback files match the changed files (exact or partial match)
2. Verify feedback is within the recency window (default 180 days)
3. Ensure feedback was saved properly: `risk-assessor view-feedback`

### Feedback File Location

The default location is `.risk_assessor/feedback.json`. If you need a different location, you can modify the `FeedbackCatalog` initialization in your code.

### Migrating Feedback Between Repositories

Simply copy the `.risk_assessor/feedback.json` file to the new repository. Ensure file paths are updated if the repository structure is different.
