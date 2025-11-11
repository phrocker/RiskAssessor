"""Azure Functions handler for RiskAssessor."""

import json
import logging
from typing import Optional

import azure.functions as func

# Import RiskAssessor components
from risk_assessor.core.risk_engine import RiskEngine
from risk_assessor.utils.config import Config

# Configure logging
logger = logging.getLogger(__name__)


# Create function app
app = func.FunctionApp()


@app.function_name(name="RiskAssessorHttp")
@app.route(route="assess", methods=["POST", "GET"], auth_level=func.AuthLevel.FUNCTION)
def risk_assessor_http(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function HTTP trigger for RiskAssessor.
    
    Supported operations via POST JSON:
    - assess-pr: Assess a pull request
    - assess-commits: Assess commits between two refs
    - sync-github: Sync GitHub issues
    - sync-jira: Sync Jira issues
    - catalog-stats: Get catalog statistics
    """
    logger.info('RiskAssessor HTTP trigger function processed a request.')
    
    try:
        # Parse request
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({'error': 'Invalid JSON'}),
                status_code=400,
                mimetype='application/json'
            )
        
        logger.info(f"Received request: {json.dumps(req_body)}")
        
        # Load configuration from environment
        config = Config.from_env()
        engine = RiskEngine(config)
        
        # Parse operation
        operation = req_body.get('operation')
        params = req_body.get('params', {})
        
        if not operation:
            return func.HttpResponse(
                json.dumps({
                    'error': 'Missing operation parameter',
                    'supported_operations': [
                        'assess-pr',
                        'assess-commits',
                        'sync-github',
                        'sync-jira',
                        'catalog-stats'
                    ]
                }),
                status_code=400,
                mimetype='application/json'
            )
        
        # Handle different operations
        result = None
        
        if operation == 'assess-pr':
            pr_number = params.get('pr_number')
            if not pr_number:
                return func.HttpResponse(
                    json.dumps({'error': 'Missing pr_number parameter'}),
                    status_code=400,
                    mimetype='application/json'
                )
            
            logger.info(f"Assessing PR #{pr_number}")
            result = engine.assess_pull_request(int(pr_number))
        
        elif operation == 'assess-commits':
            base = params.get('base')
            head = params.get('head')
            if not base or not head:
                return func.HttpResponse(
                    json.dumps({'error': 'Missing base or head parameter'}),
                    status_code=400,
                    mimetype='application/json'
                )
            
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
                return func.HttpResponse(
                    json.dumps({'error': 'Missing project parameter'}),
                    status_code=400,
                    mimetype='application/json'
                )
            
            logger.info(f"Syncing Jira issues for project {project}")
            count = engine.sync_jira_issues(project=project)
            result = {'synced_count': count, 'source': 'jira'}
        
        elif operation == 'catalog-stats':
            logger.info("Getting catalog statistics")
            result = engine.catalog.get_statistics()
        
        else:
            return func.HttpResponse(
                json.dumps({'error': f'Unknown operation: {operation}'}),
                status_code=400,
                mimetype='application/json'
            )
        
        # Return success response
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype='application/json'
        )
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return func.HttpResponse(
            json.dumps({'error': f'Internal error: {str(e)}'}),
            status_code=500,
            mimetype='application/json'
        )


@app.function_name(name="RiskAssessorTimer")
@app.schedule(schedule="0 0 2 * * *", arg_name="timer", run_on_startup=False)
def risk_assessor_timer(timer: func.TimerRequest) -> None:
    """
    Azure Function Timer trigger for scheduled syncing.
    
    Runs daily at 2 AM UTC to sync GitHub issues.
    """
    logger.info('RiskAssessor Timer trigger function started.')
    
    try:
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
    
    logger.info('RiskAssessor Timer trigger function completed.')


@app.function_name(name="RiskAssessorQueue")
@app.queue_trigger(arg_name="msg", queue_name="risk-assessor-queue", connection="AzureWebJobsStorage")
def risk_assessor_queue(msg: func.QueueMessage) -> None:
    """
    Azure Function Queue trigger for async processing.
    
    Process assessment requests from Azure Storage Queue.
    """
    logger.info('RiskAssessor Queue trigger function started.')
    
    try:
        # Parse message
        message = json.loads(msg.get_body().decode('utf-8'))
        logger.info(f"Processing queue message: {message}")
        
        # Load configuration
        config = Config.from_env()
        engine = RiskEngine(config)
        
        # Parse operation
        operation = message.get('operation')
        params = message.get('params', {})
        
        if operation == 'assess-pr':
            pr_number = params.get('pr_number')
            result = engine.assess_pull_request(int(pr_number))
            logger.info(f"Assessment result for PR #{pr_number}: {result.get('risk_level')}")
        
        elif operation == 'assess-commits':
            base = params.get('base')
            head = params.get('head')
            result = engine.assess_commits(base, head)
            logger.info(f"Assessment result for {base}..{head}: {result.get('risk_level')}")
        
        logger.info('Queue message processed successfully.')
        
    except Exception as e:
        logger.error(f"Error processing queue message: {str(e)}", exc_info=True)
        raise
