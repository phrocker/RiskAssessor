"""Google Cloud Functions handler for RiskAssessor."""

import json
import os
import logging
from typing import Any

import functions_framework
from flask import Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import RiskAssessor components
from risk_assessor.core.risk_engine import RiskEngine
from risk_assessor.utils.config import Config


@functions_framework.http
def risk_assessor(request: Request) -> tuple[str, int, dict]:
    """
    Google Cloud Function HTTP handler for RiskAssessor.
    
    Supported operations via POST JSON:
    - assess-pr: Assess a pull request
    - assess-commits: Assess commits between two refs
    - sync-github: Sync GitHub issues
    - sync-jira: Sync Jira issues
    - catalog-stats: Get catalog statistics
    
    Args:
        request: Flask request object
        
    Returns:
        Tuple of (response_body, status_code, headers)
    """
    # Set CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return '', 204, headers
    
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        if not request_json:
            return json.dumps({'error': 'Invalid JSON'}), 400, headers
        
        logger.info(f"Received request: {json.dumps(request_json)}")
        
        # Load configuration from environment
        config = Config.from_env()
        engine = RiskEngine(config)
        
        # Parse operation
        operation = request_json.get('operation')
        params = request_json.get('params', {})
        
        if not operation:
            return json.dumps({
                'error': 'Missing operation parameter',
                'supported_operations': [
                    'assess-pr',
                    'assess-commits',
                    'sync-github',
                    'sync-jira',
                    'catalog-stats'
                ]
            }), 400, headers
        
        # Handle different operations
        result = None
        
        if operation == 'assess-pr':
            pr_number = params.get('pr_number')
            if not pr_number:
                return json.dumps({'error': 'Missing pr_number parameter'}), 400, headers
            
            logger.info(f"Assessing PR #{pr_number}")
            result = engine.assess_pull_request(int(pr_number))
        
        elif operation == 'assess-commits':
            base = params.get('base')
            head = params.get('head')
            if not base or not head:
                return json.dumps({'error': 'Missing base or head parameter'}), 400, headers
            
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
                return json.dumps({'error': 'Missing project parameter'}), 400, headers
            
            logger.info(f"Syncing Jira issues for project {project}")
            count = engine.sync_jira_issues(project=project)
            result = {'synced_count': count, 'source': 'jira'}
        
        elif operation == 'catalog-stats':
            logger.info("Getting catalog statistics")
            result = engine.catalog.get_statistics()
        
        else:
            return json.dumps({'error': f'Unknown operation: {operation}'}), 400, headers
        
        # Return success response
        return json.dumps(result), 200, headers
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return json.dumps({'error': f'Internal error: {str(e)}'}), 500, headers


@functions_framework.cloud_event
def risk_assessor_scheduler(cloud_event: Any) -> None:
    """
    Google Cloud Scheduler event handler.
    
    Triggered by Cloud Scheduler to perform periodic syncing.
    
    Args:
        cloud_event: CloudEvent object
    """
    try:
        logger.info(f"Scheduler triggered: {cloud_event}")
        
        # Load configuration
        config = Config.from_env()
        engine = RiskEngine(config)
        
        # Sync GitHub issues
        logger.info("Starting scheduled GitHub sync")
        count = engine.sync_github_issues(state='all')
        logger.info(f"Synced {count} GitHub issues")
        
    except Exception as e:
        logger.error(f"Error in scheduled sync: {str(e)}", exc_info=True)
        raise


# For local testing
if __name__ == '__main__':
    from flask import Flask
    
    app = Flask(__name__)
    
    @app.route('/', methods=['POST', 'GET', 'OPTIONS'])
    def local_test():
        from flask import request
        return risk_assessor(request)
    
    app.run(host='0.0.0.0', port=8080, debug=True)
