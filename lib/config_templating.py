"""
Configuration Templating System - Dynamic configuration management
"""

import json
import yaml
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
import click
from dataclasses import dataclass, asdict
from enum import Enum


class ConfigFormat(Enum):
    """Supported configuration formats"""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    INI = "ini"
    TOML = "toml"


@dataclass
class ConfigTemplate:
    """Configuration template definition"""
    name: str
    description: str
    format: ConfigFormat
    template_path: Optional[Path] = None
    template_string: Optional[str] = None
    variables: Dict[str, Any] = None
    defaults: Dict[str, Any] = None
    validators: Dict[str, callable] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.defaults is None:
            self.defaults = {}
        if self.validators is None:
            self.validators = {}


class ConfigTemplateEngine:
    """Configuration template processing engine"""
    
    def __init__(self, template_dir: Path = None):
        self.template_dir = template_dir or Path("templates")
        self.template_dir.mkdir(exist_ok=True)
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['jsonify'] = json.dumps
        self.env.filters['yamlify'] = yaml.dump
        self.env.filters['env_var'] = lambda x: f"${{{x.upper()}}}"
        
        # Template registry
        self.templates: Dict[str, ConfigTemplate] = {}
        
        # Load built-in templates
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in configuration templates"""
        
        # Proxmox configuration template
        proxmox_template = ConfigTemplate(
            name="proxmox",
            description="Proxmox VE connection configuration",
            format=ConfigFormat.JSON,
            template_string="""
{
  "proxmox": {
    "host": "{{ proxmox_host }}",
    "username": "{{ proxmox_username }}",
    "password": "{{ proxmox_password }}",
    "node": "{{ proxmox_node }}",
    "verify_ssl": {{ verify_ssl | lower }},
    "timeout": {{ timeout }}
  },
  "vm_defaults": {
    "cores": {{ vm_cores }},
    "memory": {{ vm_memory }},
    "disk_size": {{ vm_disk_size }},
    "network": {
      "bridge": "{{ network_bridge }}",
      "model": "{{ network_model }}"
    }
  }
}
""",
            defaults={
                "proxmox_host": "192.168.1.100",
                "proxmox_username": "root@pam",
                "proxmox_node": "pve",
                "verify_ssl": False,
                "timeout": 30,
                "vm_cores": 2,
                "vm_memory": 2048,
                "vm_disk_size": 20,
                "network_bridge": "vmbr0",
                "network_model": "virtio"
            },
            validators={
                "vm_cores": lambda x: 1 <= x <= 128,
                "vm_memory": lambda x: 512 <= x <= 262144,
                "vm_disk_size": lambda x: 1 <= x <= 1000
            }
        )
        self.register_template(proxmox_template)
        
        # Docker Compose template
        docker_template = ConfigTemplate(
            name="docker-compose",
            description="Docker Compose configuration",
            format=ConfigFormat.YAML,
            template_string="""
version: '3.8'

services:
  timeshift:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ container_name }}
    {% if build_context %}
    build:
      context: {{ build_context }}
      dockerfile: {{ dockerfile }}
    {% endif %}
    environment:
      - PROXMOX_HOST={{ proxmox_host }}
      - PROXMOX_USER={{ proxmox_username }}
      {% for key, value in extra_env.items() %}
      - {{ key }}={{ value }}
      {% endfor %}
    volumes:
      - ./etc:/app/etc:ro
      - ./logs:/app/logs
      {% for volume in extra_volumes %}
      - {{ volume }}
      {% endfor %}
    ports:
      {% for port in ports %}
      - "{{ port }}"
      {% endfor %}
    restart: {{ restart_policy }}
    {% if networks %}
    networks:
      {% for network in networks %}
      - {{ network }}
      {% endfor %}
    {% endif %}

{% if networks %}
networks:
  {% for network in networks %}
  {{ network }}:
    driver: bridge
  {% endfor %}
{% endif %}
""",
            defaults={
                "docker_image": "timeshift/proxmox",
                "docker_tag": "latest",
                "container_name": "timeshift",
                "build_context": ".",
                "dockerfile": "Dockerfile",
                "restart_policy": "unless-stopped",
                "ports": ["8080:8080"],
                "networks": ["timeshift-net"],
                "extra_env": {},
                "extra_volumes": []
            }
        )
        self.register_template(docker_template)
        
        # Environment variables template
        env_template = ConfigTemplate(
            name="environment",
            description="Environment variables configuration",
            format=ConfigFormat.ENV,
            template_string="""
# Time Shift Proxmox Environment Configuration
# Generated on {{ timestamp }}

# Proxmox Configuration
PROXMOX_HOST={{ proxmox_host }}
PROXMOX_USERNAME={{ proxmox_username }}
PROXMOX_PASSWORD={{ proxmox_password }}
PROXMOX_NODE={{ proxmox_node }}
PROXMOX_VERIFY_SSL={{ verify_ssl }}

# Application Settings
APP_ENV={{ app_env }}
APP_DEBUG={{ app_debug }}
LOG_LEVEL={{ log_level }}

# Database (if needed)
{% if database_url %}
DATABASE_URL={{ database_url }}
{% endif %}

# API Keys
{% for key, value in api_keys.items() %}
{{ key | upper }}_API_KEY={{ value }}
{% endfor %}

# Feature Flags
{% for feature, enabled in features.items() %}
FEATURE_{{ feature | upper }}={{ enabled }}
{% endfor %}
""",
            defaults={
                "app_env": "production",
                "app_debug": False,
                "log_level": "INFO",
                "api_keys": {},
                "features": {}
            }
        )
        self.register_template(env_template)
        
        # Kubernetes deployment template
        k8s_template = ConfigTemplate(
            name="kubernetes",
            description="Kubernetes deployment configuration",
            format=ConfigFormat.YAML,
            template_string="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app_name }}
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    version: {{ version }}
spec:
  replicas: {{ replicas }}
  selector:
    matchLabels:
      app: {{ app_name }}
  template:
    metadata:
      labels:
        app: {{ app_name }}
        version: {{ version }}
    spec:
      containers:
      - name: {{ container_name }}
        image: {{ image }}:{{ tag }}
        imagePullPolicy: {{ image_pull_policy }}
        ports:
        {% for port in ports %}
        - containerPort: {{ port.container }}
          name: {{ port.name }}
          protocol: {{ port.protocol | default('TCP') }}
        {% endfor %}
        env:
        {% for env in environment %}
        - name: {{ env.name }}
          value: "{{ env.value }}"
        {% endfor %}
        {% if config_map %}
        envFrom:
        - configMapRef:
            name: {{ config_map }}
        {% endif %}
        resources:
          requests:
            memory: "{{ resources.requests.memory }}"
            cpu: "{{ resources.requests.cpu }}"
          limits:
            memory: "{{ resources.limits.memory }}"
            cpu: "{{ resources.limits.cpu }}"
        {% if health_check %}
        livenessProbe:
          httpGet:
            path: {{ health_check.path }}
            port: {{ health_check.port }}
          initialDelaySeconds: {{ health_check.initial_delay }}
          periodSeconds: {{ health_check.period }}
        {% endif %}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ app_name }}-service
  namespace: {{ namespace }}
spec:
  selector:
    app: {{ app_name }}
  ports:
  {% for port in ports %}
  - port: {{ port.service | default(port.container) }}
    targetPort: {{ port.container }}
    name: {{ port.name }}
  {% endfor %}
  type: {{ service_type }}
""",
            defaults={
                "app_name": "timeshift",
                "namespace": "default",
                "version": "1.0.0",
                "replicas": 1,
                "container_name": "timeshift",
                "image": "timeshift/proxmox",
                "tag": "latest",
                "image_pull_policy": "IfNotPresent",
                "ports": [{"container": 8080, "name": "http"}],
                "environment": [],
                "resources": {
                    "requests": {"memory": "256Mi", "cpu": "250m"},
                    "limits": {"memory": "512Mi", "cpu": "500m"}
                },
                "service_type": "ClusterIP"
            }
        )
        self.register_template(k8s_template)
    
    def register_template(self, template: ConfigTemplate):
        """Register a configuration template"""
        self.templates[template.name] = template
        
        # Save template to file if string provided
        if template.template_string and not template.template_path:
            template_file = self.template_dir / f"{template.name}.{template.format.value}.j2"
            template_file.write_text(template.template_string)
            template.template_path = template_file
    
    def render_template(
        self, 
        name: str, 
        variables: Dict[str, Any], 
        validate: bool = True
    ) -> str:
        """Render a configuration template"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
            
        template = self.templates[name]
        
        # Merge with defaults
        context = template.defaults.copy()
        context.update(variables)
        
        # Add utility variables
        from datetime import datetime
        context['timestamp'] = datetime.now().isoformat()
        context['generated_by'] = 'Time Shift Proxmox Config Template Engine'
        
        # Validate variables
        if validate:
            for var_name, validator in template.validators.items():
                if var_name in context:
                    if not validator(context[var_name]):
                        raise ValueError(f"Validation failed for '{var_name}': {context[var_name]}")
        
        # Render template
        if template.template_string:
            jinja_template = Template(template.template_string)
        else:
            jinja_template = self.env.get_template(template.template_path.name)
            
        return jinja_template.render(**context)
    
    def render_to_file(
        self, 
        name: str, 
        variables: Dict[str, Any], 
        output_path: Path,
        validate: bool = True
    ):
        """Render template to file"""
        content = self.render_template(name, variables, validate)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        
        # Set appropriate permissions for sensitive files
        if name in ['environment', 'proxmox']:
            output_path.chmod(0o600)
    
    def interactive_render(self, name: str) -> Dict[str, Any]:
        """Interactively collect variables and render template"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
            
        template = self.templates[name]
        variables = {}
        
        click.echo(f"\n{template.description}")
        click.echo("=" * len(template.description))
        
        # Collect each variable
        for var_name, default in template.defaults.items():
            # Format variable name for display
            display_name = var_name.replace('_', ' ').title()
            
            # Determine input type
            if isinstance(default, bool):
                value = click.confirm(display_name, default=default)
            elif isinstance(default, int):
                value = click.prompt(display_name, type=int, default=default)
            elif isinstance(default, list):
                # For lists, collect comma-separated values
                default_str = ', '.join(map(str, default))
                value_str = click.prompt(f"{display_name} (comma-separated)", default=default_str)
                value = [v.strip() for v in value_str.split(',') if v.strip()]
            elif isinstance(default, dict):
                # For dicts, use JSON input
                default_json = json.dumps(default)
                value_str = click.prompt(f"{display_name} (JSON)", default=default_json)
                try:
                    value = json.loads(value_str)
                except json.JSONDecodeError:
                    click.echo(f"Invalid JSON, using default: {default}")
                    value = default
            else:
                # String input
                if 'password' in var_name.lower():
                    value = click.prompt(display_name, hide_input=True, default=default)
                else:
                    value = click.prompt(display_name, default=default)
                    
            variables[var_name] = value
            
        return variables
    
    def create_config_set(self, name: str, templates: List[str], variables: Dict[str, Any]):
        """Create a set of related configurations"""
        config_set_dir = Path("config_sets") / name
        config_set_dir.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "name": name,
            "templates": templates,
            "created_at": datetime.now().isoformat(),
            "files": []
        }
        
        for template_name in templates:
            if template_name not in self.templates:
                click.echo(f"Warning: Template '{template_name}' not found, skipping")
                continue
                
            template = self.templates[template_name]
            
            # Determine output filename
            ext_map = {
                ConfigFormat.JSON: "json",
                ConfigFormat.YAML: "yml",
                ConfigFormat.ENV: "env",
                ConfigFormat.INI: "ini",
                ConfigFormat.TOML: "toml"
            }
            
            filename = f"{template_name}.{ext_map[template.format]}"
            output_path = config_set_dir / filename
            
            # Render template
            self.render_to_file(template_name, variables, output_path)
            manifest["files"].append(filename)
            
            click.echo(f"✓ Created {output_path}")
        
        # Save manifest
        manifest_path = config_set_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        click.echo(f"\n✓ Configuration set '{name}' created in {config_set_dir}")
        
        return config_set_dir


# Utility functions for template management

def list_templates(engine: ConfigTemplateEngine):
    """List all available templates"""
    from rich.table import Table
    from rich.console import Console
    
    console = Console()
    table = Table(title="Available Configuration Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Format", style="magenta")
    table.add_column("Description", style="white")
    table.add_column("Variables", style="green")
    
    for name, template in engine.templates.items():
        table.add_row(
            name,
            template.format.value.upper(),
            template.description,
            str(len(template.defaults))
        )
        
    console.print(table)


def validate_config_file(file_path: Path, format: ConfigFormat) -> bool:
    """Validate a configuration file"""
    try:
        content = file_path.read_text()
        
        if format == ConfigFormat.JSON:
            json.loads(content)
        elif format == ConfigFormat.YAML:
            yaml.safe_load(content)
        elif format == ConfigFormat.ENV:
            # Basic env file validation
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' not in line:
                        return False
                        
        return True
    except Exception:
        return False


# Example usage function
def example_usage():
    """Example of using the configuration template system"""
    
    # Create engine
    engine = ConfigTemplateEngine()
    
    # Render a simple template
    proxmox_config = engine.render_template("proxmox", {
        "proxmox_host": "10.0.0.100",
        "proxmox_username": "admin@pve",
        "proxmox_password": "secret123",
        "vm_cores": 4,
        "vm_memory": 4096
    })
    
    print("Rendered Proxmox config:")
    print(proxmox_config)
    
    # Create a complete configuration set
    variables = {
        "proxmox_host": "10.0.0.100",
        "proxmox_username": "admin@pve",
        "proxmox_password": "secret123",
        "app_name": "timeshift-prod",
        "docker_image": "timeshift/proxmox",
        "docker_tag": "v1.0.0"
    }
    
    engine.create_config_set(
        "production",
        ["proxmox", "docker-compose", "environment"],
        variables
    )