"""Configuration management for RiskAssessor."""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import yaml
from pathlib import Path


@dataclass
class GitHubConfig:
    """GitHub configuration."""
    
    token: Optional[str] = None
    repo: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "GitHubConfig":
        """Load GitHub config from environment variables."""
        return cls(
            token=os.getenv("GITHUB_TOKEN"),
            repo=os.getenv("GITHUB_REPO")
        )


@dataclass
class JiraConfig:
    """Jira configuration."""
    
    server: Optional[str] = None
    username: Optional[str] = None
    token: Optional[str] = None
    project: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "JiraConfig":
        """Load Jira config from environment variables."""
        return cls(
            server=os.getenv("JIRA_SERVER"),
            username=os.getenv("JIRA_USERNAME"),
            token=os.getenv("JIRA_TOKEN"),
            project=os.getenv("JIRA_PROJECT")
        )


@dataclass
class LLMConfig:
    """LLM configuration."""
    
    api_key: Optional[str] = None
    model: str = "gpt-4"
    api_base: Optional[str] = None
    temperature: float = 0.7
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load LLM config from environment variables."""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL", "gpt-4"),
            api_base=os.getenv("LLM_API_BASE"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
        )


@dataclass
class RiskThresholds:
    """Risk assessment thresholds."""
    
    low_threshold: float = 0.3
    medium_threshold: float = 0.6
    high_threshold: float = 0.8
    
    complexity_weight: float = 0.3
    history_weight: float = 0.3
    llm_weight: float = 0.4


@dataclass
class Config:
    """Main configuration for RiskAssessor."""
    
    github: GitHubConfig = field(default_factory=GitHubConfig)
    jira: JiraConfig = field(default_factory=JiraConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    thresholds: RiskThresholds = field(default_factory=RiskThresholds)
    catalog_path: str = ".risk_assessor/catalog.json"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            github=GitHubConfig.from_env(),
            jira=JiraConfig.from_env(),
            llm=LLMConfig.from_env(),
            catalog_path=os.getenv("RISK_CATALOG_PATH", ".risk_assessor/catalog.json")
        )
    
    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            return cls.from_env()
        
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        
        if not data:
            return cls.from_env()
        
        config = cls()
        
        # Load GitHub config
        if "github" in data:
            gh = data["github"]
            config.github = GitHubConfig(
                token=gh.get("token") or os.getenv("GITHUB_TOKEN"),
                repo=gh.get("repo") or os.getenv("GITHUB_REPO")
            )
        
        # Load Jira config
        if "jira" in data:
            jira = data["jira"]
            config.jira = JiraConfig(
                server=jira.get("server") or os.getenv("JIRA_SERVER"),
                username=jira.get("username") or os.getenv("JIRA_USERNAME"),
                token=jira.get("token") or os.getenv("JIRA_TOKEN"),
                project=jira.get("project") or os.getenv("JIRA_PROJECT")
            )
        
        # Load LLM config
        if "llm" in data:
            llm = data["llm"]
            config.llm = LLMConfig(
                api_key=llm.get("api_key") or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"),
                model=llm.get("model", "gpt-4"),
                api_base=llm.get("api_base") or os.getenv("LLM_API_BASE"),
                temperature=llm.get("temperature", 0.7)
            )
        
        # Load thresholds
        if "thresholds" in data:
            th = data["thresholds"]
            config.thresholds = RiskThresholds(
                low_threshold=th.get("low", 0.3),
                medium_threshold=th.get("medium", 0.6),
                high_threshold=th.get("high", 0.8),
                complexity_weight=th.get("complexity_weight", 0.3),
                history_weight=th.get("history_weight", 0.3),
                llm_weight=th.get("llm_weight", 0.4)
            )
        
        if "catalog_path" in data:
            config.catalog_path = data["catalog_path"]
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "github": {
                "repo": self.github.repo
            },
            "jira": {
                "server": self.jira.server,
                "username": self.jira.username,
                "project": self.jira.project
            },
            "llm": {
                "model": self.llm.model,
                "api_base": self.llm.api_base,
                "temperature": self.llm.temperature
            },
            "thresholds": {
                "low": self.thresholds.low_threshold,
                "medium": self.thresholds.medium_threshold,
                "high": self.thresholds.high_threshold,
                "complexity_weight": self.thresholds.complexity_weight,
                "history_weight": self.thresholds.history_weight,
                "llm_weight": self.thresholds.llm_weight
            },
            "catalog_path": self.catalog_path
        }
