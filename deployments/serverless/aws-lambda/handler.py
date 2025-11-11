"""AWS Lambda handler for RiskAssessor."""

import json
import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import RiskAssessor components
from risk_assessor.core.risk_engine import RiskEngine
from risk_assessor.utils.config import Config


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for RiskAssessor.
    
    Supported operations:
    - assess-pr: Assess a pull request
    - assess-commits: Assess commits between two refs
    - sync-github: Sync GitHub issues
    - sync-jira: Sync Jira issues
    - catalog-stats: Get catalog statistics
    
    Args:
        event: Lambda event data
        context: Lambda context
        
    Returns:
        Response with statusCode and body
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Load configuration from environment
        config = Config.from_env()
        engine = RiskEngine(config)
        
        # Parse operation from event
        operation = event.get('operation')
        params = event.get('params', {})
        
        if not operation:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing operation parameter',
                    'supported_operations': [
                        'assess-pr',
                        'assess-commits',
                        'sync-github',
                        'sync-jira',
                        'catalog-stats'
                    ]
                })
            }
        
        # Handle different operations
        result = None
        
        if operation == 'assess-pr':
            pr_number = params.get('pr_number')
            if not pr_number:
                return error_response('Missing pr_number parameter', 400)
            
            logger.info(f"Assessing PR #{pr_number}")
            result = engine.assess_pull_request(int(pr_number))
        
        elif operation == 'assess-commits':
            base = params.get('base')
            head = params.get('head')
            if not base or not head:
                return error_response('Missing base or head parameter', 400)
            
            logger.info(f"Assessing commits from {base} to {head}")
            result = engine.assess_commits(base, head)
        
        elif operation == 'sync-github':
            state = params.get('state', 'all')
            labels = params.get('labels', [])
            
            logger.info(f"Syncing GitHub issues (state={state})")
            count = engine.sync_github_issues(state=state, labels=labels)
            result = {'synced_count': count, 'source': 'github'}
        
        elif operation == 'sync-jira':
            project = params.get('project')
            if not project:
                return error_response('Missing project parameter', 400)
            
            logger.info(f"Syncing Jira issues for project {project}")
            count = engine.sync_jira_issues(project=project)
            result = {'synced_count': count, 'source': 'jira'}
        
        elif operation == 'catalog-stats':
            logger.info("Getting catalog statistics")
            result = engine.catalog.get_statistics()
        
        else:
            return error_response(f'Unknown operation: {operation}', 400)
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return error_response(f'Internal error: {str(e)}', 500)


def error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    """Create error response."""
    return {
        'statusCode': status_code,
        'body': json.dumps({'error': message}),
        'headers': {
            'Content-Type': 'application/json'
        }
    }


# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'operation': 'catalog-stats',
        'params': {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
