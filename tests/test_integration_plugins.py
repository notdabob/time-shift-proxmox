"""
Test suite for integration plugin system
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from integration_plugins import (
    PluginManager, IntegrationPlugin, PluginMetadata,
    PluginStatus, PluginPriority, ProxmoxPlugin, DockerPlugin,
    GitPlugin, MonitoringPlugin, SecurityPlugin
)


class TestPluginMetadata:
    """Test PluginMetadata dataclass"""
    
    def test_plugin_metadata_creation(self):
        """Test creating plugin metadata"""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin"
        )
        
        assert metadata.name == "test-plugin"
        assert metadata.version == "1.0.0"
        assert metadata.priority == PluginPriority.MEDIUM
        assert metadata.dependencies == []
        assert metadata.capabilities == []
        assert metadata.config_schema == {}
    
    def test_plugin_metadata_with_full_options(self):
        """Test plugin metadata with all options"""
        metadata = PluginMetadata(
            name="test-plugin",
            version="1.0.0",
            author="Test Author",
            description="Test plugin",
            priority=PluginPriority.HIGH,
            dependencies=["dep1", "dep2"],
            capabilities=["cap1", "cap2"],
            config_schema={"key": "value"}
        )
        
        assert metadata.priority == PluginPriority.HIGH
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.capabilities == ["cap1", "cap2"]
        assert metadata.config_schema == {"key": "value"}


class TestPluginManager:
    """Test PluginManager functionality"""
    
    @pytest.fixture
    def plugin_manager(self):
        """Create a plugin manager instance"""
        return PluginManager()
    
    @pytest.mark.asyncio
    async def test_discover_builtin_plugins(self, plugin_manager):
        """Test discovering built-in plugins"""
        discovered = await plugin_manager.discover_plugins()
        
        # Should discover all built-in plugins
        assert "proxmox" in discovered
        assert "docker" in discovered
        assert "git" in discovered
        assert "monitoring" in discovered
        assert "security" in discovered
        assert len(discovered) >= 5
    
    @pytest.mark.asyncio
    async def test_load_plugin(self, plugin_manager):
        """Test loading a plugin"""
        await plugin_manager.discover_plugins()
        
        # Load git plugin
        success = await plugin_manager.load_plugin("git")
        assert success is True
        
        # Check plugin status
        assert plugin_manager.plugins["git"].status == PluginStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_execute_plugin_action(self, plugin_manager):
        """Test executing plugin action"""
        await plugin_manager.discover_plugins()
        await plugin_manager.load_plugin("monitoring")
        
        # Execute metrics action
        result = await plugin_manager.execute_plugin("monitoring", "metrics")
        
        assert "cpu_percent" in result
        assert "memory_percent" in result
        assert "disk_usage" in result
    
    @pytest.mark.asyncio
    async def test_plugin_not_found(self, plugin_manager):
        """Test executing action on non-existent plugin"""
        with pytest.raises(ValueError, match="Plugin 'nonexistent' not found"):
            await plugin_manager.execute_plugin("nonexistent", "action")
    
    @pytest.mark.asyncio
    async def test_plugin_not_active(self, plugin_manager):
        """Test executing action on inactive plugin"""
        await plugin_manager.discover_plugins()
        
        # Don't load the plugin
        with pytest.raises(RuntimeError, match="Plugin 'git' is not active"):
            await plugin_manager.execute_plugin("git", "status")
    
    @pytest.mark.asyncio
    async def test_invalid_action(self, plugin_manager):
        """Test executing invalid action"""
        await plugin_manager.discover_plugins()
        await plugin_manager.load_plugin("git")
        
        with pytest.raises(ValueError, match="cannot handle action 'invalid'"):
            await plugin_manager.execute_plugin("git", "invalid")
    
    @pytest.mark.asyncio
    async def test_execute_action_on_all(self, plugin_manager):
        """Test executing action on all capable plugins"""
        await plugin_manager.discover_plugins()
        
        # Create a custom test plugin that can handle "test" action
        class TestPlugin(IntegrationPlugin):
            def get_metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="test",
                    version="1.0.0",
                    author="Test",
                    description="Test",
                    capabilities=["test"]
                )
            
            async def initialize(self) -> bool:
                return True
            
            async def execute(self, action: str, **kwargs):
                return {"result": "test"}
        
        # Add test plugin
        plugin_manager.plugins["test"] = TestPlugin()
        await plugin_manager.load_plugin("test")
        
        # Execute on all
        results = await plugin_manager.execute_action_on_all("test")
        
        assert "test" in results
        assert results["test"]["result"] == "test"
    
    @pytest.mark.asyncio
    async def test_health_check_all(self, plugin_manager):
        """Test health checking all plugins"""
        await plugin_manager.discover_plugins()
        await plugin_manager.load_plugin("git")
        await plugin_manager.load_plugin("monitoring")
        
        results = await plugin_manager.health_check_all()
        
        assert "git" in results
        assert "monitoring" in results
        assert results["git"]["status"] == "healthy"
        assert results["monitoring"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_shutdown(self, plugin_manager):
        """Test shutting down all plugins"""
        await plugin_manager.discover_plugins()
        await plugin_manager.load_plugin("git")
        
        await plugin_manager.shutdown()
        
        assert plugin_manager.plugins["git"].status == PluginStatus.UNLOADED


class TestGitPlugin:
    """Test GitPlugin functionality"""
    
    @pytest.fixture
    def git_plugin(self):
        """Create a git plugin instance"""
        return GitPlugin()
    
    def test_git_metadata(self, git_plugin):
        """Test git plugin metadata"""
        metadata = git_plugin.get_metadata()
        
        assert metadata.name == "git"
        assert "status" in metadata.capabilities
        assert "pull" in metadata.capabilities
        assert "push" in metadata.capabilities
        assert "commit" in metadata.capabilities
    
    @pytest.mark.asyncio
    async def test_git_initialize(self, git_plugin):
        """Test git plugin initialization"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = await git_plugin.initialize()
            assert result is True
            
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == ["git", "--version"]
    
    @pytest.mark.asyncio
    async def test_git_status(self, git_plugin):
        """Test git status command"""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"M file.txt\n", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            
            result = await git_plugin.execute("status")
            
            assert result["status"] == "success"
            assert "M file.txt" in result["output"]
            mock_exec.assert_called_with(
                "git", "status", "--porcelain",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
    
    @pytest.mark.asyncio
    async def test_git_commit(self, git_plugin):
        """Test git commit command"""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"1 file changed", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process
            
            result = await git_plugin.execute("commit", message="Test commit")
            
            assert result["status"] == "success"
            mock_exec.assert_called_with(
                "git", "commit", "-m", "Test commit",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
    
    @pytest.mark.asyncio
    async def test_git_commit_no_message(self, git_plugin):
        """Test git commit without message"""
        result = await git_plugin.execute("commit")
        
        assert result["status"] == "error"
        assert "Commit message required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_git_unknown_action(self, git_plugin):
        """Test unknown git action"""
        result = await git_plugin.execute("unknown_action")
        
        assert result["status"] == "error"
        assert "Unknown action: unknown_action" in result["error"]


class TestMonitoringPlugin:
    """Test MonitoringPlugin functionality"""
    
    @pytest.fixture
    def monitoring_plugin(self):
        """Create a monitoring plugin instance"""
        return MonitoringPlugin()
    
    def test_monitoring_metadata(self, monitoring_plugin):
        """Test monitoring plugin metadata"""
        metadata = monitoring_plugin.get_metadata()
        
        assert metadata.name == "monitoring"
        assert "metrics" in metadata.capabilities
        assert "alerts" in metadata.capabilities
        assert "logs" in metadata.capabilities
        assert "traces" in metadata.capabilities
    
    @pytest.mark.asyncio
    async def test_collect_metrics(self, monitoring_plugin):
        """Test metrics collection"""
        result = await monitoring_plugin.execute("metrics")
        
        assert isinstance(result["cpu_percent"], (int, float))
        assert isinstance(result["memory_percent"], (int, float))
        assert isinstance(result["disk_usage"], (int, float))
        assert 0 <= result["cpu_percent"] <= 100
        assert 0 <= result["memory_percent"] <= 100
        assert 0 <= result["disk_usage"] <= 100


class TestSecurityPlugin:
    """Test SecurityPlugin functionality"""
    
    @pytest.fixture
    def security_plugin(self):
        """Create a security plugin instance"""
        return SecurityPlugin()
    
    def test_security_metadata(self, security_plugin):
        """Test security plugin metadata"""
        metadata = security_plugin.get_metadata()
        
        assert metadata.name == "security"
        assert metadata.priority == PluginPriority.CRITICAL
        assert "scan" in metadata.capabilities
        assert "audit" in metadata.capabilities
        assert "harden" in metadata.capabilities
        assert "report" in metadata.capabilities
    
    @pytest.mark.asyncio
    async def test_security_scan(self, security_plugin):
        """Test security scanning"""
        result = await security_plugin.execute("scan")
        
        assert "vulnerabilities" in result
        assert "risk_level" in result
        assert isinstance(result["vulnerabilities"], list)
        assert result["risk_level"] in ["low", "medium", "high", "critical"]


class TestDockerPlugin:
    """Test DockerPlugin functionality"""
    
    @pytest.fixture
    def docker_plugin(self):
        """Create a docker plugin instance"""
        return DockerPlugin()
    
    def test_docker_metadata(self, docker_plugin):
        """Test docker plugin metadata"""
        metadata = docker_plugin.get_metadata()
        
        assert metadata.name == "docker"
        assert metadata.priority == PluginPriority.HIGH
        assert "deploy" in metadata.capabilities
        assert "build" in metadata.capabilities
        assert "manage" in metadata.capabilities
        assert "logs" in metadata.capabilities
    
    @pytest.mark.asyncio
    async def test_docker_initialize(self, docker_plugin):
        """Test docker plugin initialization"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = await docker_plugin.initialize()
            assert result is True
            
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == ["docker", "--version"]


class TestProxmoxPlugin:
    """Test ProxmoxPlugin functionality"""
    
    @pytest.fixture
    def proxmox_plugin(self):
        """Create a proxmox plugin instance"""
        config = {
            "host": "192.168.1.100",
            "username": "root@pam",
            "password": "password",
            "node": "node1"
        }
        return ProxmoxPlugin(config)
    
    def test_proxmox_metadata(self, proxmox_plugin):
        """Test proxmox plugin metadata"""
        metadata = proxmox_plugin.get_metadata()
        
        assert metadata.name == "proxmox"
        assert metadata.priority == PluginPriority.HIGH
        assert "deploy" in metadata.capabilities
        assert "manage" in metadata.capabilities
        assert "monitor" in metadata.capabilities
        assert "backup" in metadata.capabilities
    
    @pytest.mark.asyncio
    async def test_proxmox_deploy(self, proxmox_plugin):
        """Test VM deployment"""
        result = await proxmox_plugin.execute("deploy")
        
        assert result["status"] == "deployed"
        assert "vmid" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])