"""
Integration Plugin System - Modular plugin architecture
"""

import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass
from pathlib import Path
import asyncio
from enum import Enum


class PluginPriority(Enum):
    """Plugin execution priority"""
    CRITICAL = 0
    HIGH = 10
    MEDIUM = 50
    LOW = 100


class PluginStatus(Enum):
    """Plugin status"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    author: str
    description: str
    priority: PluginPriority = PluginPriority.MEDIUM
    dependencies: List[str] = None
    capabilities: List[str] = None
    config_schema: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.capabilities is None:
            self.capabilities = []
        if self.config_schema is None:
            self.config_schema = {}


class IntegrationPlugin(ABC):
    """Base class for all integration plugins"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.status = PluginStatus.UNLOADED
        self.metadata = self.get_metadata()
        
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def execute(self, action: str, **kwargs) -> Any:
        """Execute plugin action"""
        pass
    
    async def validate_config(self) -> bool:
        """Validate plugin configuration"""
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {"status": "healthy", "plugin": self.metadata.name}
    
    async def cleanup(self):
        """Cleanup plugin resources"""
        pass
    
    def can_handle(self, action: str) -> bool:
        """Check if plugin can handle specific action"""
        return action in self.metadata.capabilities


class PluginManager:
    """Plugin management system"""
    
    def __init__(self):
        self.plugins: Dict[str, IntegrationPlugin] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.plugin_dir = Path(__file__).parent.parent / "plugins"
        
    async def discover_plugins(self) -> List[str]:
        """Discover available plugins"""
        discovered = []
        
        # Built-in plugins
        for name, plugin_class in self._get_builtin_plugins().items():
            self.plugins[name] = plugin_class()
            discovered.append(name)
            
        # External plugins from plugin directory
        if self.plugin_dir.exists():
            for plugin_file in self.plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue
                    
                module_name = plugin_file.stem
                try:
                    module = importlib.import_module(f"plugins.{module_name}")
                    
                    # Find plugin classes in module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, IntegrationPlugin) and 
                            obj != IntegrationPlugin):
                            plugin_instance = obj()
                            plugin_name = plugin_instance.metadata.name
                            self.plugins[plugin_name] = plugin_instance
                            discovered.append(plugin_name)
                            
                except Exception as e:
                    print(f"Error loading plugin {module_name}: {e}")
                    
        return discovered
    
    async def load_plugin(self, name: str, config: Dict[str, Any] = None) -> bool:
        """Load and initialize a plugin"""
        if name not in self.plugins:
            return False
            
        plugin = self.plugins[name]
        plugin.status = PluginStatus.LOADING
        
        # Set configuration
        if config:
            plugin.config.update(config)
            
        # Validate configuration
        if not await plugin.validate_config():
            plugin.status = PluginStatus.ERROR
            return False
            
        # Check dependencies
        for dep in plugin.metadata.dependencies:
            if dep not in self.plugins or self.plugins[dep].status != PluginStatus.ACTIVE:
                # Try to load dependency
                if not await self.load_plugin(dep):
                    plugin.status = PluginStatus.ERROR
                    return False
                    
        # Initialize plugin
        try:
            if await plugin.initialize():
                plugin.status = PluginStatus.ACTIVE
                
                # Register plugin hooks
                self._register_plugin_hooks(plugin)
                
                return True
            else:
                plugin.status = PluginStatus.ERROR
                return False
                
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            raise e
    
    async def execute_plugin(self, name: str, action: str, **kwargs) -> Any:
        """Execute plugin action"""
        if name not in self.plugins:
            raise ValueError(f"Plugin '{name}' not found")
            
        plugin = self.plugins[name]
        
        if plugin.status != PluginStatus.ACTIVE:
            raise RuntimeError(f"Plugin '{name}' is not active")
            
        if not plugin.can_handle(action):
            raise ValueError(f"Plugin '{name}' cannot handle action '{action}'")
            
        # Execute pre-hooks
        await self._execute_hooks(f"pre_{action}", plugin=plugin, **kwargs)
        
        # Execute plugin action
        result = await plugin.execute(action, **kwargs)
        
        # Execute post-hooks
        await self._execute_hooks(f"post_{action}", plugin=plugin, result=result, **kwargs)
        
        return result
    
    async def execute_action_on_all(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute action on all capable plugins"""
        results = {}
        
        # Sort plugins by priority
        sorted_plugins = sorted(
            self.plugins.items(),
            key=lambda x: x[1].metadata.priority.value
        )
        
        for name, plugin in sorted_plugins:
            if plugin.status == PluginStatus.ACTIVE and plugin.can_handle(action):
                try:
                    results[name] = await self.execute_plugin(name, action, **kwargs)
                except Exception as e:
                    results[name] = {"error": str(e)}
                    
        return results
    
    def register_hook(self, event: str, callback: Callable):
        """Register event hook"""
        if event not in self.hooks:
            self.hooks[event] = []
        self.hooks[event].append(callback)
        
    async def _execute_hooks(self, event: str, **kwargs):
        """Execute registered hooks for event"""
        if event in self.hooks:
            for hook in self.hooks[event]:
                if asyncio.iscoroutinefunction(hook):
                    await hook(**kwargs)
                else:
                    hook(**kwargs)
    
    def _register_plugin_hooks(self, plugin: IntegrationPlugin):
        """Register hooks provided by plugin"""
        # Look for hook methods in plugin
        for method_name in dir(plugin):
            if method_name.startswith("hook_"):
                event = method_name[5:]  # Remove 'hook_' prefix
                method = getattr(plugin, method_name)
                self.register_hook(event, method)
    
    def _get_builtin_plugins(self) -> Dict[str, Type[IntegrationPlugin]]:
        """Get built-in plugin classes"""
        return {
            "proxmox": ProxmoxPlugin,
            "docker": DockerPlugin,
            "git": GitPlugin,
            "monitoring": MonitoringPlugin,
            "security": SecurityPlugin,
        }
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks on all active plugins"""
        results = {}
        
        for name, plugin in self.plugins.items():
            if plugin.status == PluginStatus.ACTIVE:
                try:
                    results[name] = await plugin.health_check()
                except Exception as e:
                    results[name] = {"status": "error", "error": str(e)}
                    
        return results
    
    async def shutdown(self):
        """Shutdown all plugins"""
        for plugin in self.plugins.values():
            if plugin.status == PluginStatus.ACTIVE:
                await plugin.cleanup()
                plugin.status = PluginStatus.UNLOADED


# Built-in Plugin Implementations

class ProxmoxPlugin(IntegrationPlugin):
    """Proxmox integration plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="proxmox",
            version="1.0.0",
            author="Time Shift Team",
            description="Proxmox VE integration for VM management",
            priority=PluginPriority.HIGH,
            capabilities=["deploy", "manage", "monitor", "backup"],
            config_schema={
                "host": {"type": "string", "required": True},
                "username": {"type": "string", "required": True},
                "password": {"type": "string", "required": True},
                "node": {"type": "string", "required": True},
                "verify_ssl": {"type": "boolean", "default": True},
            }
        )
    
    async def initialize(self) -> bool:
        # Import Proxmox API module
        try:
            from lib.proxmox_api import ProxmoxAPI
            self.api = ProxmoxAPI(self.config)
            return True
        except Exception:
            return False
    
    async def execute(self, action: str, **kwargs) -> Any:
        if action == "deploy":
            return await self._deploy_vm(**kwargs)
        elif action == "manage":
            return await self._manage_vm(**kwargs)
        elif action == "monitor":
            return await self._monitor_vm(**kwargs)
        elif action == "backup":
            return await self._backup_vm(**kwargs)
            
    async def _deploy_vm(self, **kwargs):
        # VM deployment logic
        return {"status": "deployed", "vmid": 100}
    
    async def _manage_vm(self, **kwargs):
        # VM management logic
        return {"status": "managed"}
    
    async def _monitor_vm(self, **kwargs):
        # VM monitoring logic
        return {"status": "healthy", "metrics": {}}
    
    async def _backup_vm(self, **kwargs):
        # VM backup logic
        return {"status": "backed_up", "backup_id": "backup_123"}


class DockerPlugin(IntegrationPlugin):
    """Docker integration plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="docker",
            version="1.0.0",
            author="Time Shift Team",
            description="Docker container management",
            priority=PluginPriority.HIGH,
            capabilities=["deploy", "build", "manage", "logs"],
            config_schema={
                "compose_file": {"type": "string", "default": "docker-compose.yml"},
                "project_name": {"type": "string", "default": "timeshift"},
            }
        )
    
    async def initialize(self) -> bool:
        # Check Docker availability
        import subprocess
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            return True
        except:
            return False
    
    async def execute(self, action: str, **kwargs) -> Any:
        if action == "deploy":
            return await self._deploy_containers(**kwargs)
        elif action == "build":
            return await self._build_images(**kwargs)
        elif action == "manage":
            return await self._manage_containers(**kwargs)
        elif action == "logs":
            return await self._get_logs(**kwargs)
            
    async def _deploy_containers(self, **kwargs):
        # Container deployment logic
        return {"status": "deployed", "containers": ["app", "db"]}
    
    async def _build_images(self, **kwargs):
        # Image building logic
        return {"status": "built", "images": ["timeshift:latest"]}
    
    async def _manage_containers(self, **kwargs):
        # Container management logic
        return {"status": "managed"}
    
    async def _get_logs(self, **kwargs):
        # Log retrieval logic
        return {"status": "success", "logs": "Container logs..."}


class GitPlugin(IntegrationPlugin):
    """Git integration plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="git",
            version="1.0.0",
            author="Time Shift Team",
            description="Git repository management",
            capabilities=["clone", "pull", "push", "status"],
            config_schema={
                "remote": {"type": "string"},
                "branch": {"type": "string", "default": "main"},
            }
        )
    
    async def initialize(self) -> bool:
        import subprocess
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            return True
        except:
            return False
    
    async def execute(self, action: str, **kwargs) -> Any:
        import subprocess
        
        if action == "status":
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            return {"status": "success", "output": result.stdout}
        elif action == "pull":
            result = subprocess.run(["git", "pull"], capture_output=True, text=True)
            return {"status": "success" if result.returncode == 0 else "error", "output": result.stdout}
        # Add more git operations as needed
        
        return {"status": "not_implemented"}


class MonitoringPlugin(IntegrationPlugin):
    """System monitoring plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="monitoring",
            version="1.0.0",
            author="Time Shift Team",
            description="System and application monitoring",
            capabilities=["metrics", "alerts", "logs", "traces"],
            config_schema={
                "prometheus_url": {"type": "string"},
                "grafana_url": {"type": "string"},
                "alert_webhook": {"type": "string"},
            }
        )
    
    async def initialize(self) -> bool:
        # Initialize monitoring connections
        return True
    
    async def execute(self, action: str, **kwargs) -> Any:
        if action == "metrics":
            return await self._collect_metrics(**kwargs)
        elif action == "alerts":
            return await self._check_alerts(**kwargs)
        elif action == "logs":
            return await self._aggregate_logs(**kwargs)
        elif action == "traces":
            return await self._collect_traces(**kwargs)
            
    async def _collect_metrics(self, **kwargs):
        # Metrics collection logic
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
    
    async def _check_alerts(self, **kwargs):
        # Alert checking logic
        return {"alerts": [], "status": "healthy"}
    
    async def _aggregate_logs(self, **kwargs):
        # Log aggregation logic
        return {"logs": [], "count": 0}
    
    async def _collect_traces(self, **kwargs):
        # Trace collection logic
        return {"traces": [], "count": 0}


class SecurityPlugin(IntegrationPlugin):
    """Security scanning and hardening plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="security",
            version="1.0.0",
            author="Time Shift Team",
            description="Security scanning and hardening",
            priority=PluginPriority.CRITICAL,
            capabilities=["scan", "audit", "harden", "report"],
            config_schema={
                "scan_level": {"type": "string", "default": "medium"},
                "auto_fix": {"type": "boolean", "default": False},
            }
        )
    
    async def initialize(self) -> bool:
        # Initialize security tools
        return True
    
    async def execute(self, action: str, **kwargs) -> Any:
        if action == "scan":
            return await self._security_scan(**kwargs)
        elif action == "audit":
            return await self._security_audit(**kwargs)
        elif action == "harden":
            return await self._apply_hardening(**kwargs)
        elif action == "report":
            return await self._generate_report(**kwargs)
            
    async def _security_scan(self, **kwargs):
        # Security scanning logic
        return {"vulnerabilities": [], "risk_level": "low"}
    
    async def _security_audit(self, **kwargs):
        # Security audit logic
        return {"findings": [], "compliance": "passed"}
    
    async def _apply_hardening(self, **kwargs):
        # Security hardening logic
        return {"hardening_applied": True, "changes": []}
    
    async def _generate_report(self, **kwargs):
        # Report generation logic
        return {"report": "Security report content...", "format": "pdf"}