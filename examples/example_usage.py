#!/usr/bin/env python3
"""
Example script demonstrating RiskAssessor usage.

This script shows how to:
1. Configure RiskAssessor
2. Sync issues from GitHub
3. Assess a pull request
4. Get risk recommendations
"""

import os
from risk_assessor import RiskEngine
from risk_assessor.utils.config import Config


def main():
    """Main example function."""
    print("RiskAssessor Example\n" + "=" * 50)
    
    # Method 1: Load from environment variables
    print("\n1. Loading configuration from environment...")
    config = Config.from_env()
    
    # Method 2: Load from config file (commented out)
    # config = Config.from_file('examples/config.yaml')
    
    # Initialize the risk engine
    print("2. Initializing RiskEngine...")
    engine = RiskEngine(config)
    
    # Example: Sync GitHub issues (requires GITHUB_TOKEN and GITHUB_REPO)
    if config.github.token and config.github.repo:
        print("\n3. Syncing GitHub issues...")
        try:
            count = engine.sync_github_issues(state="closed")
            print(f"   ✓ Synced {count} issues")
        except Exception as e:
            print(f"   ✗ Error syncing: {e}")
    else:
        print("\n3. Skipping GitHub sync (no credentials)")
    
    # Example: Show catalog statistics
    print("\n4. Catalog statistics:")
    stats = engine.catalog.get_statistics()
    print(f"   Total issues: {stats['total_issues']}")
    if stats['by_source']:
        print("   By source:")
        for source, count in stats['by_source'].items():
            print(f"     - {source}: {count}")
    
    # Example: Assess a PR (requires GitHub configuration)
    if config.github.token and config.github.repo:
        print("\n5. Example: Assessing a pull request...")
        print("   Usage: engine.assess_pull_request(pr_number=123)")
        print("   (Skipping actual assessment in this example)")
        
        # Uncomment to assess a real PR:
        # try:
        #     assessment = engine.assess_pull_request(pr_number=1)
        #     print(f"\n   Risk Level: {assessment['risk_level']}")
        #     print(f"   Risk Score: {assessment['overall_risk_score']:.2f}")
        #     
        #     if assessment.get('llm_analysis'):
        #         print("\n   Recommendations:")
        #         for rec in assessment['llm_analysis']['recommendations'][:3]:
        #             print(f"     - {rec}")
        # except Exception as e:
        #     print(f"   Error: {e}")
    
    # Example: Assess commits between branches
    print("\n6. Example: Assessing commits between refs...")
    print("   Usage: engine.assess_commits(base='main', head='develop')")
    print("   (Skipping actual assessment in this example)")
    
    print("\n" + "=" * 50)
    print("Example complete!")
    print("\nNext steps:")
    print("  1. Set your API keys in environment variables")
    print("  2. Run: risk-assessor sync --source github")
    print("  3. Run: risk-assessor assess-pr --pr <number>")


if __name__ == "__main__":
    main()
