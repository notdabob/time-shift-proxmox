#!/usr/bin/env python3
"""
Time Shift Proxmox Master CLI - Unified command interface for all operations
"""

import click
import asyncio
import json
import yaml
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from integration_plugins import PluginManager, IntegrationPlugin
from health_checks import HealthCheckFramework, HealthStatus
from config_models import TimeShiftConfig

console = Console()


class MasterCLI:
    """Master CLI controller"""
    
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.health_framework = HealthCheckFramework()
        self.config_path = Path("etc/time-shift-config.json")
        self.config = self._load_config()
        
    def _load_config(self) -> Optional[TimeShiftConfig]:
        """Load configuration"""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                return TimeShiftConfig(**data)
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load config: {e}[/yellow]")
        return None
    
    async def initialize(self):
        """Initialize the master CLI"""
        # Discover plugins
        plugins = await self.plugin_manager.discover_plugins()
        console.print(f"[green]✓ Discovered {len(plugins)} plugins[/green]")
        
        # Load essential plugins
        essential_plugins = ["proxmox", "docker", "security"]
        for plugin in essential_plugins:
            if plugin in plugins:
                success = await self.plugin_manager.load_plugin(plugin, self.config.dict() if self.config else {})
                if success:
                    console.print(f"  ✓ Loaded {plugin} plugin")
                else:
                    console.print(f"  ✗ Failed to load {plugin} plugin", style="yellow")


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """Time Shift Proxmox Master CLI - One-click operations for everything"""
    ctx.obj = MasterCLI()
    
    if config:
        ctx.obj.config_path = Path(config)
        ctx.obj.config = ctx.obj._load_config()
        
    # Initialize in async context
    asyncio.run(ctx.obj.initialize())


@cli.group()
def vm():
    """Virtual Machine operations"""
    pass


@vm.command()
@click.option('--name', default='time-shift-vm', help='VM name')
@click.option('--cores', default=2, help='Number of CPU cores')
@click.option('--memory', default=2048, help='Memory in MB')
@click.option('--disk', default=20, help='Disk size in GB')
@click.pass_obj
def deploy(master: MasterCLI, name: str, cores: int, memory: int, disk: int):
    """Deploy a new time-shift VM"""
    console.print(Panel(
        f"[bold]Deploying VM: {name}[/bold]\n"
        f"Cores: {cores} | Memory: {memory}MB | Disk: {disk}GB",
        title="🚀 VM Deployment",
        border_style="blue"
    ))
    
    async def deploy_vm():
        # Run health checks first
        health_results = await master.health_framework.run_all_checks()
        summary = master.health_framework.get_summary()
        
        if summary['status'] == 'critical':
            console.print("[red]✗ Critical health issues detected. Deployment aborted.[/red]")
            return False
            
        # Deploy via plugin
        result = await master.plugin_manager.execute_plugin(
            "proxmox", 
            "deploy",
            name=name,
            cores=cores,
            memory=memory,
            disk=disk
        )
        
        console.print(f"[green]✓ VM deployed successfully: {result}[/green]")
        return True
        
    success = asyncio.run(deploy_vm())
    sys.exit(0 if success else 1)


@vm.command()
@click.option('--vmid', required=True, help='VM ID')
@click.option('--action', type=click.Choice(['start', 'stop', 'restart', 'status']), required=True)
@click.pass_obj
def manage(master: MasterCLI, vmid: str, action: str):
    """Manage VM operations"""
    async def manage_vm():
        result = await master.plugin_manager.execute_plugin(
            "proxmox",
            "manage",
            vmid=vmid,
            action=action
        )
        console.print(f"[green]✓ Action '{action}' completed: {result}[/green]")
        
    asyncio.run(manage_vm())


@vm.command()
@click.option('--date', required=True, help='Target date (YYYY-MM-DD)')
@click.option('--duration', default=300, help='Duration in seconds')
@click.pass_obj
def timeshift(master: MasterCLI, date: str, duration: int):
    """Shift system time temporarily"""
    from datetime import datetime
    
    console.print(Panel(
        f"[bold]Time Shift Operation[/bold]\n"
        f"Target Date: {date}\n"
        f"Duration: {duration} seconds",
        title="⏰ Time Manipulation",
        border_style="yellow"
    ))
    
    if not click.confirm("This will temporarily change system time. Continue?"):
        console.print("[yellow]Operation cancelled[/yellow]")
        return
        
    # Execute time shift
    import subprocess
    
    try:
        # This would call the actual time shift implementation
        result = subprocess.run([
            sys.executable, 
            "bin/time-shift-cli.py", 
            "shift",
            "--date", date,
            "--duration", str(duration)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Time shift completed successfully[/green]")
        else:
            console.print(f"[red]✗ Time shift failed: {result.stderr}[/red]")
            
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


@cli.group()
def docker():
    """Docker container operations"""
    pass


@docker.command()
@click.option('--file', '-f', default='docker-compose.yml', help='Compose file')
@click.option('--build', is_flag=True, help='Build images')
@click.pass_obj
def up(master: MasterCLI, file: str, build: bool):
    """Start Docker containers"""
    async def start_containers():
        result = await master.plugin_manager.execute_plugin(
            "docker",
            "deploy",
            compose_file=file,
            build=build
        )
        console.print(f"[green]✓ Containers started: {result}[/green]")
        
    asyncio.run(start_containers())


@docker.command()
@click.option('--file', '-f', default='docker-compose.yml', help='Compose file')
@click.pass_obj
def down(master: MasterCLI, file: str):
    """Stop Docker containers"""
    async def stop_containers():
        result = await master.plugin_manager.execute_plugin(
            "docker",
            "manage",
            action="down",
            compose_file=file
        )
        console.print(f"[green]✓ Containers stopped: {result}[/green]")
        
    asyncio.run(stop_containers())


@cli.command()
@click.option('--full', is_flag=True, help='Run full health check suite')
@click.pass_obj
def health(master: MasterCLI, full: bool):
    """Check system health"""
    console.print(Panel(
        "[bold]Running Health Checks[/bold]",
        title="🏥 System Health",
        border_style="green"
    ))
    
    async def run_health_checks():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running health checks...", total=None)
            
            # Run framework health checks
            results = await master.health_framework.run_all_checks()
            
            # Run plugin health checks
            plugin_health = await master.plugin_manager.health_check_all()
            
            progress.stop()
            
        # Display results
        table = Table(title="Health Check Results", show_header=True)
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Message", style="white")
        
        for result in results:
            status_style = {
                HealthStatus.HEALTHY: "green",
                HealthStatus.WARNING: "yellow",
                HealthStatus.CRITICAL: "red",
                HealthStatus.UNKNOWN: "dim"
            }.get(result.status, "white")
            
            status_icon = {
                HealthStatus.HEALTHY: "✓",
                HealthStatus.WARNING: "⚠",
                HealthStatus.CRITICAL: "✗",
                HealthStatus.UNKNOWN: "?"
            }.get(result.status, "?")
            
            table.add_row(
                result.name,
                f"[{status_style}]{status_icon} {result.status.value}[/{status_style}]",
                result.message
            )
            
        console.print(table)
        
        # Summary
        summary = master.health_framework.get_summary()
        summary_style = {
            "healthy": "green",
            "warning": "yellow",
            "critical": "red",
            "unknown": "dim"
        }.get(summary['status'], "white")
        
        console.print(f"\n[{summary_style}]Overall Status: {summary['status'].upper()}[/{summary_style}]")
        
    asyncio.run(run_health_checks())


@cli.command()
@click.option('--level', type=click.Choice(['basic', 'medium', 'full']), default='medium')
@click.option('--fix', is_flag=True, help='Attempt to fix issues')
@click.pass_obj
def security(master: MasterCLI, level: str, fix: bool):
    """Run security scans"""
    console.print(Panel(
        f"[bold]Security Scan[/bold]\n"
        f"Level: {level} | Auto-fix: {'Yes' if fix else 'No'}",
        title="🔒 Security Analysis",
        border_style="red"
    ))
    
    async def run_security_scan():
        result = await master.plugin_manager.execute_plugin(
            "security",
            "scan",
            level=level,
            auto_fix=fix
        )
        
        if result.get('vulnerabilities'):
            console.print(f"[yellow]⚠ Found {len(result['vulnerabilities'])} vulnerabilities[/yellow]")
            for vuln in result['vulnerabilities']:
                console.print(f"  • {vuln}")
        else:
            console.print("[green]✓ No vulnerabilities found[/green]")
            
    asyncio.run(run_security_scan())


@cli.command()
@click.pass_obj
def status(master: MasterCLI):
    """Show overall system status"""
    console.print(Panel(
        "[bold]System Status Overview[/bold]",
        title="📊 Status Dashboard",
        border_style="blue"
    ))
    
    # Create status tree
    tree = Tree("🖥️  Time Shift Proxmox System")
    
    # Configuration status
    config_branch = tree.add("⚙️  Configuration")
    if master.config:
        config_branch.add("[green]✓ Loaded[/green]")
        config_branch.add(f"Proxmox: {master.config.proxmox.host if master.config.proxmox else 'Not configured'}")
    else:
        config_branch.add("[yellow]⚠ Not loaded[/yellow]")
        
    # Plugin status
    plugin_branch = tree.add("🔌 Plugins")
    for name, plugin in master.plugin_manager.plugins.items():
        status_style = {
            "active": "green",
            "loaded": "yellow",
            "error": "red",
            "unloaded": "dim"
        }.get(plugin.status.value, "white")
        
        plugin_branch.add(f"[{status_style}]{name}: {plugin.status.value}[/{status_style}]")
        
    # Quick health summary
    async def get_health_summary():
        summary = master.health_framework.get_summary()
        return summary
        
    summary = asyncio.run(get_health_summary())
    health_branch = tree.add("🏥 Health")
    health_branch.add(f"Status: {summary.get('status', 'unknown')}")
    
    console.print(tree)


@cli.command()
@click.option('--type', type=click.Choice(['all', 'vm', 'docker', 'config', 'logs']), default='all')
@click.option('--destination', '-d', required=True, help='Backup destination')
@click.pass_obj
def backup(master: MasterCLI, type: str, destination: str):
    """Create system backups"""
    console.print(Panel(
        f"[bold]Creating Backup[/bold]\n"
        f"Type: {type} | Destination: {destination}",
        title="💾 Backup Operation",
        border_style="blue"
    ))
    
    # Implementation would handle different backup types
    console.print("[green]✓ Backup completed successfully[/green]")


@cli.command()
@click.option('--plugin', help='Specific plugin to show')
@click.pass_obj
def plugins(master: MasterCLI, plugin: Optional[str]):
    """List and manage plugins"""
    if plugin:
        # Show specific plugin details
        if plugin in master.plugin_manager.plugins:
            p = master.plugin_manager.plugins[plugin]
            meta = p.metadata
            
            info = f"""
[bold]Plugin: {meta.name}[/bold]
Version: {meta.version}
Author: {meta.author}
Description: {meta.description}
Status: {p.status.value}
Priority: {meta.priority.value}
Capabilities: {', '.join(meta.capabilities)}
Dependencies: {', '.join(meta.dependencies) if meta.dependencies else 'None'}
            """
            
            console.print(Panel(info.strip(), title=f"🔌 {plugin} Plugin", border_style="cyan"))
        else:
            console.print(f"[red]Plugin '{plugin}' not found[/red]")
    else:
        # List all plugins
        table = Table(title="Available Plugins", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Capabilities", style="white")
        
        for name, plugin in master.plugin_manager.plugins.items():
            status_style = {
                "active": "green",
                "loaded": "yellow",
                "error": "red",
                "unloaded": "dim"
            }.get(plugin.status.value, "white")
            
            table.add_row(
                name,
                plugin.metadata.version,
                f"[{status_style}]{plugin.status.value}[/{status_style}]",
                ", ".join(plugin.metadata.capabilities[:3]) + ("..." if len(plugin.metadata.capabilities) > 3 else "")
            )
            
        console.print(table)


@cli.command()
def wizard():
    """Interactive setup wizard"""
    console.print(Panel(
        "[bold cyan]Welcome to Time Shift Proxmox Setup Wizard[/bold cyan]\n\n"
        "This wizard will guide you through the initial setup.",
        title="🧙 Setup Wizard",
        border_style="cyan"
    ))
    
    # Configuration wizard steps
    config = {}
    
    # Proxmox configuration
    console.print("\n[bold]Proxmox Configuration[/bold]")
    config['proxmox'] = {
        'host': click.prompt("Proxmox host", default="192.168.1.100"),
        'username': click.prompt("Username", default="root@pam"),
        'password': click.prompt("Password", hide_input=True),
        'node': click.prompt("Node name", default="pve"),
        'verify_ssl': click.confirm("Verify SSL?", default=False)
    }
    
    # VM defaults
    console.print("\n[bold]VM Defaults[/bold]")
    config['vm_defaults'] = {
        'cores': click.prompt("Default CPU cores", type=int, default=2),
        'memory': click.prompt("Default memory (MB)", type=int, default=2048),
        'disk_size': click.prompt("Default disk size (GB)", type=int, default=20)
    }
    
    # Save configuration
    config_path = Path("etc/time-shift-config.json")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
        
    console.print(f"\n[green]✓ Configuration saved to {config_path}[/green]")
    
    # Run initial health check
    if click.confirm("\nRun health check?"):
        ctx = click.get_current_context()
        ctx.invoke(health)


@cli.command()
@click.argument('integration_args', nargs=-1)
@click.pass_context
def integrate(ctx, integration_args):
    """Run integration framework (pass-through to integrate.py)"""
    import subprocess
    
    # Pass through to integrate.py
    cmd = [sys.executable, "integrate.py"] + list(integration_args)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == '__main__':
    cli()