#!/usr/bin/env python3
"""
Time Shift Proxmox - One-Click Integration Master Script
Holistic integration framework for seamless deployment and management
"""

import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import yaml

console = Console()


class IntegrationType(Enum):
    """Types of integrations supported"""
    DEPLOY = "deploy"
    CONFIGURE = "configure"
    TEST = "test"
    MONITOR = "monitor"
    BACKUP = "backup"
    RESTORE = "restore"
    UPDATE = "update"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class IntegrationManifest:
    """Integration manifest definition"""
    name: str
    version: str
    description: str
    type: IntegrationType
    requirements: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    config_template: Dict[str, Any] = field(default_factory=dict)
    commands: Dict[str, str] = field(default_factory=dict)
    health_checks: List[str] = field(default_factory=list)
    pre_hooks: List[str] = field(default_factory=list)
    post_hooks: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    platforms: List[str] = field(default_factory=lambda: ["linux", "darwin"])
    tags: List[str] = field(default_factory=list)


class IntegrationFramework:
    """Core integration framework"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.integrations_dir = self.root_dir / "integrations"
        self.config_dir = self.root_dir / "etc"
        self.cache_dir = self.root_dir / ".integration_cache"
        self.manifests: Dict[str, IntegrationManifest] = {}
        self.plugins: Dict[str, Any] = {}
        
        # Create necessary directories
        self.integrations_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
    async def discover_integrations(self) -> Dict[str, IntegrationManifest]:
        """Auto-discover available integrations"""
        console.print("[bold blue]🔍 Discovering integrations...[/bold blue]")
        
        # Scan integrations directory
        for manifest_file in self.integrations_dir.glob("*/manifest.yaml"):
            try:
                with open(manifest_file) as f:
                    data = yaml.safe_load(f)
                manifest = IntegrationManifest(**data)
                self.manifests[manifest.name] = manifest
                console.print(f"  ✓ Found: {manifest.name} v{manifest.version}")
            except Exception as e:
                console.print(f"  ✗ Error loading {manifest_file}: {e}", style="red")
                
        # Built-in integrations
        self._register_builtin_integrations()
        
        return self.manifests
    
    def _register_builtin_integrations(self):
        """Register built-in integrations"""
        builtin = [
            IntegrationManifest(
                name="proxmox-deploy",
                version="1.0.0",
                description="Deploy time-shift VM to Proxmox",
                type=IntegrationType.DEPLOY,
                requirements=["proxmoxer", "requests"],
                commands={
                    "deploy": "python bin/time-shift-cli.py deploy",
                    "validate": "python bin/time-shift-cli.py validate",
                },
                health_checks=["check_proxmox_connection", "verify_vm_template"],
            ),
            IntegrationManifest(
                name="docker-compose",
                version="1.0.0",
                description="Docker Compose deployment",
                type=IntegrationType.DEPLOY,
                requirements=["docker", "docker-compose"],
                commands={
                    "up": "docker-compose up -d",
                    "down": "docker-compose down",
                    "logs": "docker-compose logs -f",
                },
                health_checks=["check_docker_daemon", "verify_compose_file"],
            ),
            IntegrationManifest(
                name="security-scan",
                version="1.0.0",
                description="Comprehensive security scanning",
                type=IntegrationType.SECURITY,
                requirements=["bandit", "safety", "semgrep"],
                commands={
                    "scan": "python -m bandit -r lib/",
                    "audit": "safety check",
                    "secrets": "semgrep --config=auto",
                },
            ),
            IntegrationManifest(
                name="performance-monitor",
                version="1.0.0",
                description="Performance monitoring and optimization",
                type=IntegrationType.PERFORMANCE,
                requirements=["py-spy", "memory_profiler"],
                commands={
                    "profile": "py-spy record -o profile.svg -- python bin/time-shift-cli.py",
                    "memory": "mprof run bin/time-shift-cli.py",
                },
            ),
        ]
        
        for manifest in builtin:
            self.manifests[manifest.name] = manifest
    
    async def run_integration(
        self, 
        name: str, 
        command: str = "default",
        config: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ) -> bool:
        """Execute a specific integration"""
        if name not in self.manifests:
            console.print(f"[red]Integration '{name}' not found[/red]")
            return False
            
        manifest = self.manifests[name]
        console.print(Panel(
            f"[bold]{manifest.description}[/bold]\n"
            f"Version: {manifest.version}\n"
            f"Type: {manifest.type.value}",
            title=f"🚀 Running {name}",
            border_style="blue"
        ))
        
        # Check requirements
        if not await self._check_requirements(manifest):
            return False
            
        # Run pre-hooks
        if manifest.pre_hooks and not dry_run:
            for hook in manifest.pre_hooks:
                await self._run_hook(hook, "pre")
                
        # Execute command
        success = True
        if command in manifest.commands:
            cmd = manifest.commands[command]
            if dry_run:
                console.print(f"[yellow]DRY RUN:[/yellow] Would execute: {cmd}")
            else:
                success = await self._execute_command(cmd, manifest.environment)
        else:
            console.print(f"[red]Command '{command}' not found in integration[/red]")
            success = False
            
        # Run post-hooks
        if manifest.post_hooks and not dry_run and success:
            for hook in manifest.post_hooks:
                await self._run_hook(hook, "post")
                
        # Run health checks
        if manifest.health_checks and success:
            await self._run_health_checks(manifest)
            
        return success
    
    async def _check_requirements(self, manifest: IntegrationManifest) -> bool:
        """Check if requirements are met"""
        console.print("📋 Checking requirements...")
        
        # Platform check
        import platform
        current_platform = platform.system().lower()
        if current_platform not in manifest.platforms:
            console.print(f"[red]Platform {current_platform} not supported[/red]")
            return False
            
        # Python package requirements
        for req in manifest.requirements:
            try:
                __import__(req.split("==")[0])
                console.print(f"  ✓ {req}")
            except ImportError:
                console.print(f"  ✗ {req} not installed", style="red")
                return False
                
        return True
    
    async def _execute_command(self, cmd: str, env: Dict[str, str]) -> bool:
        """Execute a shell command"""
        console.print(f"🔧 Executing: {cmd}")
        
        # Merge environment variables
        cmd_env = os.environ.copy()
        cmd_env.update(env)
        
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=cmd_env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                console.print("[green]✓ Command completed successfully[/green]")
                if stdout:
                    console.print(stdout.decode())
                return True
            else:
                console.print(f"[red]✗ Command failed with code {process.returncode}[/red]")
                if stderr:
                    console.print(stderr.decode(), style="red")
                return False
                
        except Exception as e:
            console.print(f"[red]✗ Error executing command: {e}[/red]")
            return False
    
    async def _run_hook(self, hook: str, hook_type: str):
        """Run integration hook"""
        console.print(f"🪝 Running {hook_type}-hook: {hook}")
        await self._execute_command(hook, {})
    
    async def _run_health_checks(self, manifest: IntegrationManifest):
        """Run health checks for integration"""
        console.print("🏥 Running health checks...")
        
        for check in manifest.health_checks:
            # Look for check function in plugins or execute as command
            if check in self.plugins:
                result = await self.plugins[check]()
                status = "✓" if result else "✗"
                style = "green" if result else "red"
            else:
                # Execute as shell command
                result = await self._execute_command(f"python -c 'from lib.health_checks import {check}; exit(0 if {check}() else 1)'", {})
                status = "✓" if result else "✗"
                style = "green" if result else "red"
                
            console.print(f"  {status} {check}", style=style)
    
    def list_integrations(self):
        """List all available integrations"""
        table = Table(title="Available Integrations", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="magenta")
        table.add_column("Type", style="green")
        table.add_column("Description", style="white")
        table.add_column("Tags", style="yellow")
        
        for name, manifest in sorted(self.manifests.items()):
            table.add_row(
                name,
                manifest.version,
                manifest.type.value,
                manifest.description,
                ", ".join(manifest.tags)
            )
            
        console.print(table)
    
    def show_integration_details(self, name: str):
        """Show detailed information about an integration"""
        if name not in self.manifests:
            console.print(f"[red]Integration '{name}' not found[/red]")
            return
            
        manifest = self.manifests[name]
        
        # Basic info panel
        info = f"""
[bold]Description:[/bold] {manifest.description}
[bold]Version:[/bold] {manifest.version}
[bold]Type:[/bold] {manifest.type.value}
[bold]Platforms:[/bold] {', '.join(manifest.platforms)}
[bold]Tags:[/bold] {', '.join(manifest.tags)}
        """
        console.print(Panel(info.strip(), title=f"📦 {name}", border_style="blue"))
        
        # Requirements
        if manifest.requirements:
            console.print("\n[bold]Requirements:[/bold]")
            for req in manifest.requirements:
                console.print(f"  • {req}")
                
        # Commands
        if manifest.commands:
            console.print("\n[bold]Available Commands:[/bold]")
            for cmd, command in manifest.commands.items():
                console.print(f"  • [cyan]{cmd}[/cyan]: {command}")
                
        # Health checks
        if manifest.health_checks:
            console.print("\n[bold]Health Checks:[/bold]")
            for check in manifest.health_checks:
                console.print(f"  • {check}")


@click.group()
@click.pass_context
def cli(ctx):
    """Time Shift Proxmox - One-Click Integration Master"""
    ctx.obj = IntegrationFramework()


@cli.command()
@click.pass_obj
def list(framework: IntegrationFramework):
    """List all available integrations"""
    asyncio.run(framework.discover_integrations())
    framework.list_integrations()


@cli.command()
@click.argument('name')
@click.pass_obj
def info(framework: IntegrationFramework, name: str):
    """Show detailed information about an integration"""
    asyncio.run(framework.discover_integrations())
    framework.show_integration_details(name)


@cli.command()
@click.argument('name')
@click.option('--command', '-c', default='default', help='Command to execute')
@click.option('--dry-run', is_flag=True, help='Show what would be executed')
@click.option('--config', '-f', type=click.Path(exists=True), help='Configuration file')
@click.pass_obj
def run(framework: IntegrationFramework, name: str, command: str, dry_run: bool, config: Optional[str]):
    """Run a specific integration"""
    asyncio.run(framework.discover_integrations())
    
    config_data = {}
    if config:
        with open(config) as f:
            config_data = json.load(f) if config.endswith('.json') else yaml.safe_load(f)
            
    success = asyncio.run(framework.run_integration(name, command, config_data, dry_run))
    sys.exit(0 if success else 1)


@cli.command()
@click.option('--type', '-t', type=click.Choice([t.value for t in IntegrationType]), help='Filter by type')
@click.option('--sequential', is_flag=True, help='Run sequentially instead of parallel')
@click.pass_obj
def deploy(framework: IntegrationFramework, type: Optional[str], sequential: bool):
    """Deploy all integrations (or filtered by type)"""
    asyncio.run(framework.discover_integrations())
    
    # Filter integrations
    to_deploy = []
    for name, manifest in framework.manifests.items():
        if not type or manifest.type.value == type:
            to_deploy.append(name)
            
    console.print(f"[bold]Deploying {len(to_deploy)} integrations...[/bold]")
    
    async def deploy_all():
        if sequential:
            for name in to_deploy:
                await framework.run_integration(name, 'deploy')
        else:
            tasks = [framework.run_integration(name, 'deploy') for name in to_deploy]
            await asyncio.gather(*tasks)
            
    asyncio.run(deploy_all())


@cli.command()
@click.pass_obj
def wizard(framework: IntegrationFramework):
    """Interactive integration wizard"""
    asyncio.run(framework.discover_integrations())
    
    console.print(Panel(
        "[bold cyan]Welcome to Time Shift Proxmox Integration Wizard[/bold cyan]\n\n"
        "This wizard will guide you through setting up your integrations.",
        title="🧙 Integration Wizard",
        border_style="cyan"
    ))
    
    # Select integration type
    types = [t.value for t in IntegrationType]
    console.print("\n[bold]What would you like to do?[/bold]")
    for i, t in enumerate(types, 1):
        console.print(f"  {i}. {t.capitalize()}")
        
    choice = click.prompt("Select option", type=click.IntRange(1, len(types)))
    selected_type = types[choice - 1]
    
    # Filter integrations by type
    matching = [
        (name, manifest) 
        for name, manifest in framework.manifests.items() 
        if manifest.type.value == selected_type
    ]
    
    if not matching:
        console.print(f"[yellow]No integrations found for type '{selected_type}'[/yellow]")
        return
        
    # Select specific integration
    console.print(f"\n[bold]Available {selected_type} integrations:[/bold]")
    for i, (name, manifest) in enumerate(matching, 1):
        console.print(f"  {i}. {name} - {manifest.description}")
        
    choice = click.prompt("Select integration", type=click.IntRange(1, len(matching)))
    selected_name, selected_manifest = matching[choice - 1]
    
    # Configure and run
    console.print(f"\n[bold]Configuring {selected_name}...[/bold]")
    
    config = {}
    if selected_manifest.config_template:
        for key, default in selected_manifest.config_template.items():
            value = click.prompt(f"{key}", default=default)
            config[key] = value
            
    # Run the integration
    if click.confirm("\nProceed with integration?"):
        asyncio.run(framework.run_integration(selected_name, 'default', config))
    else:
        console.print("[yellow]Integration cancelled[/yellow]")


@cli.command()
def init():
    """Initialize integration framework in current project"""
    console.print("[bold]Initializing Time Shift Proxmox Integration Framework...[/bold]")
    
    # Create directory structure
    dirs = ['integrations', 'etc', 'hooks', 'templates']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        console.print(f"  ✓ Created {dir_name}/")
        
    # Create example integration manifest
    example_manifest = {
        'name': 'example-integration',
        'version': '1.0.0',
        'description': 'Example integration template',
        'type': 'deploy',
        'requirements': ['requests'],
        'commands': {
            'default': 'echo "Hello from example integration!"',
            'test': 'python -m pytest tests/',
        },
        'health_checks': ['check_connectivity'],
        'tags': ['example', 'template']
    }
    
    example_dir = Path('integrations/example-integration')
    example_dir.mkdir(exist_ok=True)
    
    with open(example_dir / 'manifest.yaml', 'w') as f:
        yaml.dump(example_manifest, f, default_flow_style=False)
        
    console.print("  ✓ Created example integration manifest")
    
    # Create hooks directory with examples
    hook_examples = {
        'pre-deploy.sh': '#!/bin/bash\necho "Preparing deployment..."',
        'post-deploy.sh': '#!/bin/bash\necho "Deployment completed!"',
        'health-check.py': '#!/usr/bin/env python3\ndef check_connectivity():\n    return True',
    }
    
    for filename, content in hook_examples.items():
        hook_file = Path('hooks') / filename
        hook_file.write_text(content)
        hook_file.chmod(0o755)
        
    console.print("  ✓ Created example hooks")
    
    console.print("\n[green]✨ Integration framework initialized successfully![/green]")
    console.print("\nNext steps:")
    console.print("  1. Run 'python integrate.py list' to see available integrations")
    console.print("  2. Create new integrations in the 'integrations/' directory")
    console.print("  3. Run 'python integrate.py wizard' for guided setup")


if __name__ == '__main__':
    cli()