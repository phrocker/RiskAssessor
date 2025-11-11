"""Command-line interface for RiskAssessor."""

import click
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from risk_assessor.core.risk_engine import RiskEngine
from risk_assessor.utils.config import Config


console = Console()


def print_risk_assessment(assessment: dict):
    """Print risk assessment in a formatted way."""
    # Overall risk
    risk_level = assessment['risk_level']
    risk_score = assessment['overall_risk_score']
    
    # Color based on risk level
    color_map = {
        'low': 'green',
        'medium': 'yellow',
        'high': 'orange',
        'critical': 'red'
    }
    color = color_map.get(risk_level, 'white')
    
    console.print(Panel(
        f"[bold {color}]{risk_level.upper()} RISK[/bold {color}]\n"
        f"Overall Risk Score: {risk_score:.2f}",
        title="Risk Assessment",
        border_style=color
    ))
    
    # Complexity Analysis
    complexity = assessment['complexity_analysis']
    console.print("\n[bold]Complexity Analysis:[/bold]")
    console.print(f"  Files Changed: {complexity['files_changed']}")
    console.print(f"  Additions: {complexity['additions']}")
    console.print(f"  Deletions: {complexity['deletions']}")
    console.print(f"  Commits: {complexity['commits']}")
    console.print(f"  Complexity Score: {complexity['complexity_score']:.2f}")
    
    if complexity.get('critical_files'):
        console.print(f"\n  [bold red]Critical Files ({len(complexity['critical_files'])}):[/bold red]")
        for file in complexity['critical_files'][:5]:
            console.print(f"    • {file}")
        if len(complexity['critical_files']) > 5:
            console.print(f"    ... and {len(complexity['critical_files']) - 5} more")
    
    # History Analysis
    history = assessment['history_analysis']
    console.print(f"\n[bold]Historical Issues:[/bold]")
    console.print(f"  Related Issues: {history['related_issues_count']}")
    console.print(f"  History Risk Score: {history['history_risk_score']:.2f}")
    
    if history.get('related_issues'):
        console.print(f"\n  [bold]Recent Related Issues:[/bold]")
        for issue in history['related_issues'][:3]:
            console.print(f"    • [{issue['source']}] {issue['identifier']}: {issue['title']}")
    
    # LLM Analysis
    if assessment.get('llm_analysis'):
        llm = assessment['llm_analysis']
        console.print(f"\n[bold]LLM Analysis:[/bold]")
        console.print(f"  Risk Score: {llm['risk_score']:.2f}")
        console.print(f"  Confidence: {llm['confidence']:.2f}")
        
        if llm.get('key_concerns'):
            console.print(f"\n  [bold yellow]Key Concerns:[/bold yellow]")
            for concern in llm['key_concerns'][:5]:
                console.print(f"    • {concern}")
        
        if llm.get('recommendations'):
            console.print(f"\n  [bold green]Recommendations:[/bold green]")
            for rec in llm['recommendations'][:5]:
                console.print(f"    • {rec}")


def print_risk_contract(contract):
    """Print risk contract in a formatted way."""
    from risk_assessor.core.contracts import RiskContract
    
    # Convert to dict if it's a RiskContract object
    if isinstance(contract, RiskContract):
        contract_dict = contract.to_dict()
    else:
        contract_dict = contract
    
    # Overall risk summary
    summary = contract_dict['risk_summary']
    risk_level = summary['risk_level']
    risk_score = summary['risk_score']
    
    # Color based on risk level
    color_map = {
        'LOW': 'green',
        'MEDIUM': 'yellow',
        'HIGH': 'red'
    }
    color = color_map.get(risk_level, 'white')
    
    console.print(Panel(
        f"[bold {color}]{risk_level} RISK[/bold {color}]\n"
        f"Risk Score: {risk_score:.2f}\n"
        f"Confidence: {summary['confidence']:.2f}",
        title=f"Risk Assessment - {contract_dict['id']}",
        border_style=color
    ))
    
    # Print overall assessment
    console.print(f"\n[bold]Assessment:[/bold] {summary['overall_assessment']}")
    
    # Print text summary
    if contract_dict.get('text_summary'):
        console.print(f"\n{contract_dict['text_summary']}")
    
    # Risk Factors
    if contract_dict.get('factors'):
        console.print("\n[bold]Risk Factors:[/bold]")
        for factor in contract_dict['factors']:
            console.print(f"\n  [bold cyan]{factor['factor_name']}[/bold cyan] ({factor['category']})")
            console.print(f"  Weight: {factor['impact_weight']:.2f}")
            console.print(f"  Observed: {factor['observed_value']}")
            console.print(f"  Assessment: {factor['assessment']}")
    
    # Recommendations
    if contract_dict.get('recommendations'):
        console.print("\n[bold green]Recommendations:[/bold green]")
        for i, rec in enumerate(contract_dict['recommendations'], 1):
            console.print(f"  {i}. {rec}")
    
    # Historical Context
    if contract_dict.get('historical_context'):
        hc = contract_dict['historical_context']
        console.print("\n[bold]Historical Context:[/bold]")
        console.print(f"  Previous Similar Changes: {hc['previous_similar_changes']}")
        console.print(f"  Previous Incidents in Region: {hc['previous_incidents_in_region']}")
        if hc.get('last_incident_cause'):
            console.print(f"  Last Incident: {hc['last_incident_cause']}")
        if hc.get('time_since_last_outage_days') is not None:
            console.print(f"  Days Since Last Outage: {hc['time_since_last_outage_days']}")
    
    # Deployment info
    console.print("\n[bold]Deployment Info:[/bold]")
    console.print(f"  Repository: {contract_dict['repository']}")
    console.print(f"  Branch: {contract_dict['branch']}")
    console.print(f"  Region: {contract_dict['deployment_region']}")
    console.print(f"  Timestamp: {contract_dict['timestamp']}")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """RiskAssessor - Assess deployment risk for code changes."""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--source', '-s', type=click.Choice(['github', 'jira']), required=True, help='Issue source')
@click.option('--state', default='all', help='Issue state filter (for GitHub)')
@click.option('--project', '-p', help='Jira project key (for Jira)')
@click.option('--labels', '-l', multiple=True, help='Filter by labels')
def sync(config, source, state, project, labels):
    """Sync issues from GitHub or Jira to the catalog."""
    # Load config
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config.from_env()
    
    # Initialize engine
    engine = RiskEngine(cfg)
    
    try:
        if source == 'github':
            console.print("[bold blue]Syncing GitHub issues...[/bold blue]")
            count = engine.sync_github_issues(state=state, labels=list(labels) if labels else None)
            console.print(f"[green]✓ Synced {count} GitHub issues to catalog[/green]")
        
        elif source == 'jira':
            if not project:
                console.print("[red]Error: --project is required for Jira[/red]")
                sys.exit(1)
            console.print(f"[bold blue]Syncing Jira issues from project {project}...[/bold blue]")
            count = engine.sync_jira_issues(project=project)
            console.print(f"[green]✓ Synced {count} Jira issues to catalog[/green]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--pr', type=int, required=True, help='Pull request number')
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
def assess_pr(config, pr, output):
    """Assess risk for a GitHub pull request."""
    # Load config
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config.from_env()
    
    # Initialize engine
    engine = RiskEngine(cfg)
    
    try:
        console.print(f"[bold blue]Assessing PR #{pr}...[/bold blue]")
        assessment = engine.assess_pull_request(pr)
        
        # Print assessment
        print_risk_assessment(assessment)
        
        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                json.dump(assessment, f, indent=2)
            console.print(f"\n[green]✓ Assessment saved to {output}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--base', required=True, help='Base reference (branch/tag/SHA)')
@click.option('--head', required=True, help='Head reference (branch/tag/SHA)')
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
def assess_commits(config, base, head, output):
    """Assess risk for commits between two references."""
    # Load config
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config.from_env()
    
    # Initialize engine
    engine = RiskEngine(cfg)
    
    try:
        console.print(f"[bold blue]Assessing changes from {base} to {head}...[/bold blue]")
        assessment = engine.assess_commits(base, head)
        
        if 'error' in assessment:
            console.print(f"[red]Error: {assessment['error']}[/red]")
            sys.exit(1)
        
        # Print assessment
        print_risk_assessment(assessment)
        
        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                json.dump(assessment, f, indent=2)
            console.print(f"\n[green]✓ Assessment saved to {output}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
def catalog_stats(config):
    """Show statistics about the issue catalog."""
    # Load config
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config.from_env()
    
    # Initialize engine
    engine = RiskEngine(cfg)
    
    stats = engine.catalog.get_statistics()
    
    console.print("\n[bold]Issue Catalog Statistics:[/bold]")
    console.print(f"  Total Issues: {stats['total_issues']}")
    
    if stats['by_source']:
        console.print("\n  [bold]By Source:[/bold]")
        for source, count in stats['by_source'].items():
            console.print(f"    {source}: {count}")
    
    if stats['by_status']:
        console.print("\n  [bold]By Status:[/bold]")
        for status, count in stats['by_status'].items():
            console.print(f"    {status}: {count}")


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--pr', type=int, required=True, help='Pull request number')
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
@click.option('--deployment-region', '-r', default='unknown', help='Target deployment region')
@click.option('--branch', '-b', help='Target branch (optional, uses PR branch if not specified)')
def assess_pr_contract(config, pr, output, deployment_region, branch):
    """Assess risk for a GitHub pull request and output as a contract."""
    # Load config
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config.from_env()
    
    # Initialize engine
    engine = RiskEngine(cfg)
    
    try:
        console.print(f"[bold blue]Assessing PR #{pr} with contract format...[/bold blue]")
        contract = engine.assess_pull_request_contract(
            pr_number=pr,
            deployment_region=deployment_region,
            branch=branch
        )
        
        # Print contract
        print_risk_contract(contract)
        
        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                json.dump(contract.to_dict(), f, indent=2)
            console.print(f"\n[green]✓ Risk contract saved to {output}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--base', required=True, help='Base reference (branch/tag/SHA)')
@click.option('--head', required=True, help='Head reference (branch/tag/SHA)')
@click.option('--output', '-o', type=click.Path(), help='Output JSON file')
@click.option('--deployment-region', '-r', default='unknown', help='Target deployment region')
def assess_commits_contract(config, base, head, output, deployment_region):
    """Assess risk for commits between two references and output as a contract."""
    # Load config
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config.from_env()
    
    # Initialize engine
    engine = RiskEngine(cfg)
    
    try:
        console.print(f"[bold blue]Assessing changes from {base} to {head} with contract format...[/bold blue]")
        contract = engine.assess_commits_contract(
            base_ref=base,
            head_ref=head,
            deployment_region=deployment_region
        )
        
        # Print contract
        print_risk_contract(contract)
        
        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                json.dump(contract.to_dict(), f, indent=2)
            console.print(f"\n[green]✓ Risk contract saved to {output}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), default='risk_assessor_config.yaml', help='Output config file path')
def init_config(output):
    """Initialize a configuration file template."""
    config_template = """# RiskAssessor Configuration

# GitHub Configuration
github:
  token: ${GITHUB_TOKEN}
  repo: owner/repository

# Jira Configuration (optional)
jira:
  server: https://your-company.atlassian.net
  username: ${JIRA_USERNAME}
  token: ${JIRA_TOKEN}
  project: PROJECT_KEY

# LLM Configuration
llm:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4
  # api_base: https://custom-api-endpoint.com  # Optional for custom endpoints
  temperature: 0.7

# Risk Thresholds
thresholds:
  low: 0.3
  medium: 0.6
  high: 0.8
  complexity_weight: 0.3
  history_weight: 0.3
  llm_weight: 0.4

# Catalog Path
catalog_path: .risk_assessor/catalog.json
"""
    
    with open(output, 'w') as f:
        f.write(config_template)
    
    console.print(f"[green]✓ Configuration template created at {output}[/green]")
    console.print("\nEdit the file and set your API keys and preferences.")
    console.print("You can use environment variables by keeping the ${VAR} syntax.")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
