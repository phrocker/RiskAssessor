"""Tests for deployment configurations."""

import os
import yaml
import json
import pytest
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent


class TestDockerDeployment:
    """Test Docker deployment files."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        dockerfile = REPO_ROOT / "Dockerfile"
        assert dockerfile.exists()
    
    def test_dockerfile_has_workdir(self):
        """Test that Dockerfile sets a working directory."""
        dockerfile = REPO_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "WORKDIR" in content
    
    def test_dockerfile_installs_package(self):
        """Test that Dockerfile installs the package."""
        dockerfile = REPO_ROOT / "Dockerfile"
        content = dockerfile.read_text()
        assert "pip install" in content
    
    def test_dockerignore_exists(self):
        """Test that .dockerignore exists."""
        dockerignore = REPO_ROOT / ".dockerignore"
        assert dockerignore.exists()
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists."""
        compose_file = REPO_ROOT / "docker-compose.yml"
        assert compose_file.exists()
    
    def test_docker_compose_valid_yaml(self):
        """Test that docker-compose.yml is valid YAML."""
        compose_file = REPO_ROOT / "docker-compose.yml"
        with open(compose_file) as f:
            config = yaml.safe_load(f)
        
        assert "version" in config or "services" in config
        assert "services" in config
        assert "risk-assessor" in config["services"]


class TestKubernetesDeployment:
    """Test Kubernetes deployment files."""
    
    def test_k8s_directory_exists(self):
        """Test that kubernetes deployment directory exists."""
        k8s_dir = REPO_ROOT / "deployments" / "kubernetes"
        assert k8s_dir.exists()
        assert k8s_dir.is_dir()
    
    def test_namespace_yaml_exists(self):
        """Test that namespace.yaml exists."""
        namespace_file = REPO_ROOT / "deployments" / "kubernetes" / "namespace.yaml"
        assert namespace_file.exists()
    
    def test_namespace_yaml_valid(self):
        """Test that namespace.yaml is valid."""
        namespace_file = REPO_ROOT / "deployments" / "kubernetes" / "namespace.yaml"
        with open(namespace_file) as f:
            config = yaml.safe_load(f)
        
        assert config["kind"] == "Namespace"
        assert config["metadata"]["name"] == "risk-assessor"
    
    def test_deployment_yaml_exists(self):
        """Test that deployment.yaml exists."""
        deployment_file = REPO_ROOT / "deployments" / "kubernetes" / "deployment.yaml"
        assert deployment_file.exists()
    
    def test_deployment_yaml_valid(self):
        """Test that deployment.yaml is valid."""
        deployment_file = REPO_ROOT / "deployments" / "kubernetes" / "deployment.yaml"
        with open(deployment_file) as f:
            config = yaml.safe_load(f)
        
        assert config["kind"] == "Deployment"
        assert config["metadata"]["name"] == "risk-assessor"
        assert "spec" in config
        assert "template" in config["spec"]
    
    def test_service_yaml_exists(self):
        """Test that service.yaml exists."""
        service_file = REPO_ROOT / "deployments" / "kubernetes" / "service.yaml"
        assert service_file.exists()
    
    def test_service_yaml_valid(self):
        """Test that service.yaml is valid."""
        service_file = REPO_ROOT / "deployments" / "kubernetes" / "service.yaml"
        with open(service_file) as f:
            config = yaml.safe_load(f)
        
        assert config["kind"] == "Service"
        assert config["metadata"]["name"] == "risk-assessor"
    
    def test_configmap_yaml_exists(self):
        """Test that configmap.yaml exists."""
        configmap_file = REPO_ROOT / "deployments" / "kubernetes" / "configmap.yaml"
        assert configmap_file.exists()
    
    def test_configmap_yaml_valid(self):
        """Test that configmap.yaml is valid."""
        configmap_file = REPO_ROOT / "deployments" / "kubernetes" / "configmap.yaml"
        with open(configmap_file) as f:
            config = yaml.safe_load(f)
        
        assert config["kind"] == "ConfigMap"
        assert "data" in config
    
    def test_secret_yaml_exists(self):
        """Test that secret.yaml exists."""
        secret_file = REPO_ROOT / "deployments" / "kubernetes" / "secret.yaml"
        assert secret_file.exists()
    
    def test_cronjob_yaml_exists(self):
        """Test that cronjob.yaml exists."""
        cronjob_file = REPO_ROOT / "deployments" / "kubernetes" / "cronjob.yaml"
        assert cronjob_file.exists()
    
    def test_cronjob_yaml_valid(self):
        """Test that cronjob.yaml is valid."""
        cronjob_file = REPO_ROOT / "deployments" / "kubernetes" / "cronjob.yaml"
        with open(cronjob_file) as f:
            config = yaml.safe_load(f)
        
        assert config["kind"] == "CronJob"
        assert "spec" in config
        assert "schedule" in config["spec"]


class TestServerlessDeployment:
    """Test serverless deployment files."""
    
    def test_serverless_directory_exists(self):
        """Test that serverless deployment directory exists."""
        serverless_dir = REPO_ROOT / "deployments" / "serverless"
        assert serverless_dir.exists()
        assert serverless_dir.is_dir()
    
    def test_aws_lambda_directory_exists(self):
        """Test that AWS Lambda deployment directory exists."""
        lambda_dir = REPO_ROOT / "deployments" / "serverless" / "aws-lambda"
        assert lambda_dir.exists()
        assert lambda_dir.is_dir()
    
    def test_lambda_handler_exists(self):
        """Test that Lambda handler exists."""
        handler_file = REPO_ROOT / "deployments" / "serverless" / "aws-lambda" / "handler.py"
        assert handler_file.exists()
    
    def test_lambda_handler_has_function(self):
        """Test that Lambda handler has lambda_handler function."""
        handler_file = REPO_ROOT / "deployments" / "serverless" / "aws-lambda" / "handler.py"
        content = handler_file.read_text()
        assert "def lambda_handler" in content
    
    def test_serverless_yml_exists(self):
        """Test that serverless.yml exists."""
        serverless_file = REPO_ROOT / "deployments" / "serverless" / "aws-lambda" / "serverless.yml"
        assert serverless_file.exists()
    
    def test_serverless_yml_valid(self):
        """Test that serverless.yml is valid."""
        serverless_file = REPO_ROOT / "deployments" / "serverless" / "aws-lambda" / "serverless.yml"
        with open(serverless_file) as f:
            config = yaml.safe_load(f)
        
        assert "service" in config
        assert "provider" in config
        assert "functions" in config
        assert config["provider"]["name"] == "aws"
    
    def test_gcp_functions_directory_exists(self):
        """Test that GCP Functions directory exists."""
        gcp_dir = REPO_ROOT / "deployments" / "serverless" / "google-cloud-functions"
        assert gcp_dir.exists()
    
    def test_gcp_main_exists(self):
        """Test that GCP Functions main.py exists."""
        main_file = REPO_ROOT / "deployments" / "serverless" / "google-cloud-functions" / "main.py"
        assert main_file.exists()
    
    def test_gcp_main_has_function(self):
        """Test that GCP Functions main.py has the function."""
        main_file = REPO_ROOT / "deployments" / "serverless" / "google-cloud-functions" / "main.py"
        content = main_file.read_text()
        assert "def risk_assessor" in content
    
    def test_azure_functions_directory_exists(self):
        """Test that Azure Functions directory exists."""
        azure_dir = REPO_ROOT / "deployments" / "serverless" / "azure-functions"
        assert azure_dir.exists()
    
    def test_azure_function_app_exists(self):
        """Test that Azure function_app.py exists."""
        function_file = REPO_ROOT / "deployments" / "serverless" / "azure-functions" / "function_app.py"
        assert function_file.exists()
    
    def test_azure_function_app_has_functions(self):
        """Test that Azure function_app.py has function definitions."""
        function_file = REPO_ROOT / "deployments" / "serverless" / "azure-functions" / "function_app.py"
        content = function_file.read_text()
        assert "def risk_assessor_http" in content
    
    def test_azure_host_json_exists(self):
        """Test that Azure host.json exists."""
        host_file = REPO_ROOT / "deployments" / "serverless" / "azure-functions" / "host.json"
        assert host_file.exists()
    
    def test_azure_host_json_valid(self):
        """Test that Azure host.json is valid JSON."""
        host_file = REPO_ROOT / "deployments" / "serverless" / "azure-functions" / "host.json"
        with open(host_file) as f:
            config = json.load(f)
        
        assert "version" in config


class TestDeploymentDocumentation:
    """Test deployment documentation."""
    
    def test_deployment_md_exists(self):
        """Test that DEPLOYMENT.md exists."""
        deployment_doc = REPO_ROOT / "DEPLOYMENT.md"
        assert deployment_doc.exists()
    
    def test_deployment_md_has_content(self):
        """Test that DEPLOYMENT.md has substantial content."""
        deployment_doc = REPO_ROOT / "DEPLOYMENT.md"
        content = deployment_doc.read_text()
        assert len(content) > 1000
        assert "Kubernetes" in content
        assert "Docker" in content
        assert "Serverless" in content
    
    def test_k8s_readme_exists(self):
        """Test that Kubernetes README exists."""
        k8s_readme = REPO_ROOT / "deployments" / "kubernetes" / "README.md"
        assert k8s_readme.exists()
    
    def test_lambda_readme_exists(self):
        """Test that AWS Lambda README exists."""
        lambda_readme = REPO_ROOT / "deployments" / "serverless" / "aws-lambda" / "README.md"
        assert lambda_readme.exists()
    
    def test_gcp_readme_exists(self):
        """Test that GCP Functions README exists."""
        gcp_readme = REPO_ROOT / "deployments" / "serverless" / "google-cloud-functions" / "README.md"
        assert gcp_readme.exists()
    
    def test_azure_readme_exists(self):
        """Test that Azure Functions README exists."""
        azure_readme = REPO_ROOT / "deployments" / "serverless" / "azure-functions" / "README.md"
        assert azure_readme.exists()


class TestDeploymentScripts:
    """Test deployment helper scripts."""
    
    def test_scripts_directory_exists(self):
        """Test that scripts directory exists."""
        scripts_dir = REPO_ROOT / "scripts"
        assert scripts_dir.exists()
        assert scripts_dir.is_dir()
    
    def test_build_docker_script_exists(self):
        """Test that build-docker.sh exists."""
        script = REPO_ROOT / "scripts" / "build-docker.sh"
        assert script.exists()
    
    def test_build_docker_script_executable(self):
        """Test that build-docker.sh is executable."""
        script = REPO_ROOT / "scripts" / "build-docker.sh"
        assert os.access(script, os.X_OK)
    
    def test_deploy_k8s_script_exists(self):
        """Test that deploy-k8s.sh exists."""
        script = REPO_ROOT / "scripts" / "deploy-k8s.sh"
        assert script.exists()
    
    def test_deploy_k8s_script_executable(self):
        """Test that deploy-k8s.sh is executable."""
        script = REPO_ROOT / "scripts" / "deploy-k8s.sh"
        assert os.access(script, os.X_OK)
    
    def test_deploy_lambda_script_exists(self):
        """Test that deploy-lambda.sh exists."""
        script = REPO_ROOT / "scripts" / "deploy-lambda.sh"
        assert script.exists()
    
    def test_deploy_lambda_script_executable(self):
        """Test that deploy-lambda.sh is executable."""
        script = REPO_ROOT / "scripts" / "deploy-lambda.sh"
        assert os.access(script, os.X_OK)
