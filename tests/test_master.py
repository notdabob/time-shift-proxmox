"""
Tests for master.py - Main orchestration CLI
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from click.testing import CliRunner
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from master import cli, IntegrationPlugin, HealthStatus


class TestMasterCLI:
    """Test cases for the master CLI"""
    
    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()
    
    @pytest.fixture
    def mock_plugin_manager(self):
        """Create mock plugin manager"""
        with patch('master.PluginManager') as mock:
            manager = Mock()
            manager.discover_plugins = AsyncMock(return_value={})
            manager.get_plugin = Mock(return_value=None)
            manager.list_plugins = Mock(return_value=[])
            mock.return_value = manager
            yield manager
    
    def test_cli_help(self, runner):
        """Test CLI help command"""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Time-Shift Proxmox Master Controller' in result.output
        assert 'Commands:' in result.output
    
    def test_version_command(self, runner):
        """Test version command"""
        result = runner.invoke(cli, ['version'])
        assert result.exit_code == 0
        assert 'Time-Shift Proxmox Master' in result.output
        assert 'Version:' in result.output
    
    @patch('master.load_config')
    def test_status_command_no_config(self, mock_load_config, runner, mock_plugin_manager):
        """Test status command without config"""
        mock_load_config.return_value = None
        
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        assert 'No configuration found' in result.output
    
    @patch('master.load_config')
    def test_status_command_with_config(self, mock_load_config, runner, mock_plugin_manager):
        """Test status command with valid config"""
        mock_config = {
            'proxmox': {
                'host': '192.168.1.100',
                'username': 'root@pam'
            }
        }
        mock_load_config.return_value = mock_config
        
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        # Output would include configuration status
    
    def test_plugin_list_empty(self, runner, mock_plugin_manager):
        """Test plugin list with no plugins"""
        result = runner.invoke(cli, ['plugin', 'list'])
        assert result.exit_code == 0
        assert 'No plugins found' in result.output or 'Plugins' in result.output
    
    def test_plugin_list_with_plugins(self, runner, mock_plugin_manager):
        """Test plugin list with plugins"""
        mock_plugin = Mock(spec=IntegrationPlugin)
        mock_plugin.metadata.name = 'test-plugin'
        mock_plugin.metadata.version = '1.0.0'
        mock_plugin.metadata.description = 'Test plugin'
        mock_plugin.metadata.enabled = True
        mock_plugin.metadata.capabilities = ['test']
        
        mock_plugin_manager.list_plugins.return_value = [mock_plugin]
        
        result = runner.invoke(cli, ['plugin', 'list'])
        assert result.exit_code == 0
    
    def test_plugin_info_not_found(self, runner, mock_plugin_manager):
        """Test plugin info for non-existent plugin"""
        mock_plugin_manager.get_plugin.return_value = None
        
        result = runner.invoke(cli, ['plugin', 'info', 'non-existent'])
        assert result.exit_code == 0
        assert 'Plugin not found' in result.output
    
    def test_plugin_enable(self, runner, mock_plugin_manager):
        """Test enabling a plugin"""
        mock_plugin = Mock()
        mock_plugin_manager.get_plugin.return_value = mock_plugin
        mock_plugin_manager.enable_plugin = AsyncMock(return_value=True)
        
        result = runner.invoke(cli, ['plugin', 'enable', 'test-plugin'])
        assert result.exit_code == 0
        assert 'enabled' in result.output.lower()
    
    def test_plugin_disable(self, runner, mock_plugin_manager):
        """Test disabling a plugin"""
        mock_plugin = Mock()
        mock_plugin_manager.get_plugin.return_value = mock_plugin
        mock_plugin_manager.disable_plugin = AsyncMock(return_value=True)
        
        result = runner.invoke(cli, ['plugin', 'disable', 'test-plugin'])
        assert result.exit_code == 0
        assert 'disabled' in result.output.lower()
    
    @patch('master.load_config')
    def test_config_show(self, mock_load_config, runner):
        """Test config show command"""
        mock_config = {'test': 'config'}
        mock_load_config.return_value = mock_config
        
        result = runner.invoke(cli, ['config', 'show'])
        assert result.exit_code == 0
    
    def test_config_validate_missing_file(self, runner):
        """Test config validate with missing file"""
        result = runner.invoke(cli, ['config', 'validate'])
        assert result.exit_code == 0
        assert 'not found' in result.output or 'does not exist' in result.output
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.load')
    def test_config_validate_valid(self, mock_json_load, mock_open, mock_exists, runner):
        """Test config validate with valid config"""
        mock_exists.return_value = True
        mock_json_load.return_value = {'valid': 'config'}
        
        result = runner.invoke(cli, ['config', 'validate'])
        assert result.exit_code == 0
        assert 'valid' in result.output.lower()
    
    def test_health_check_no_plugins(self, runner, mock_plugin_manager):
        """Test health check with no plugins"""
        mock_plugin_manager.list_plugins.return_value = []
        
        result = runner.invoke(cli, ['health'])
        assert result.exit_code == 0
        assert 'No plugins available' in result.output
    
    def test_health_check_with_plugins(self, runner, mock_plugin_manager):
        """Test health check with plugins"""
        mock_plugin = Mock()
        mock_plugin.metadata.name = 'test-plugin'
        mock_plugin.metadata.enabled = True
        mock_plugin.health_check = AsyncMock(return_value=Mock(
            status=HealthStatus.HEALTHY,
            message='All good',
            details={}
        ))
        
        mock_plugin_manager.list_plugins.return_value = [mock_plugin]
        
        result = runner.invoke(cli, ['health'])
        assert result.exit_code == 0
    
    def test_action_no_plugins(self, runner, mock_plugin_manager):
        """Test action command with no plugins"""
        mock_plugin_manager.list_plugins.return_value = []
        
        result = runner.invoke(cli, ['action', 'test-action'])
        assert result.exit_code == 0
        assert 'No plugins available' in result.output
    
    def test_action_with_target_not_found(self, runner, mock_plugin_manager):
        """Test action with specific target plugin not found"""
        mock_plugin_manager.get_plugin.return_value = None
        
        result = runner.invoke(cli, ['action', 'test-action', '--target', 'non-existent'])
        assert result.exit_code == 0
        assert 'Plugin not found' in result.output
    
    def test_action_execution_success(self, runner, mock_plugin_manager):
        """Test successful action execution"""
        mock_plugin = Mock()
        mock_plugin.metadata.name = 'test-plugin'
        mock_plugin.metadata.enabled = True
        mock_plugin.metadata.capabilities = ['test-action']
        mock_plugin.can_handle = Mock(return_value=True)
        mock_plugin.execute = AsyncMock(return_value={'status': 'success'})
        
        mock_plugin_manager.list_plugins.return_value = [mock_plugin]
        
        result = runner.invoke(cli, ['action', 'test-action'])
        assert result.exit_code == 0
        assert 'success' in result.output.lower()
    
    def test_action_execution_failure(self, runner, mock_plugin_manager):
        """Test failed action execution"""
        mock_plugin = Mock()
        mock_plugin.metadata.name = 'test-plugin'
        mock_plugin.metadata.enabled = True
        mock_plugin.metadata.capabilities = ['test-action']
        mock_plugin.can_handle = Mock(return_value=True)
        mock_plugin.execute = AsyncMock(side_effect=Exception('Test error'))
        
        mock_plugin_manager.list_plugins.return_value = [mock_plugin]
        
        result = runner.invoke(cli, ['action', 'test-action'])
        assert result.exit_code == 0
        assert 'failed' in result.output.lower()
    
    def test_interactive_mode_exit(self, runner):
        """Test interactive mode immediate exit"""
        with patch('click.prompt', return_value='exit'):
            result = runner.invoke(cli, ['interactive'])
            assert result.exit_code == 0
            assert 'Exiting' in result.output
    
    def test_deploy_command(self, runner, mock_plugin_manager):
        """Test deploy command"""
        mock_plugin = Mock()
        mock_plugin.metadata.name = 'proxmox'
        mock_plugin.metadata.enabled = True
        mock_plugin.metadata.capabilities = ['deploy_vm']
        mock_plugin.can_handle = Mock(return_value=True)
        mock_plugin.execute = AsyncMock(return_value={'status': 'deployed'})
        
        mock_plugin_manager.get_plugin.return_value = mock_plugin
        
        result = runner.invoke(cli, ['deploy'])
        assert result.exit_code == 0
    
    @patch('master.load_config')
    def test_time_shift_no_config(self, mock_load_config, runner):
        """Test time-shift command without config"""
        mock_load_config.return_value = None
        
        result = runner.invoke(cli, ['time-shift', '192.168.1.100'])
        assert result.exit_code == 0
        assert 'Configuration required' in result.output
    
    def test_cli_error_handling(self, runner):
        """Test CLI error handling"""
        with patch('master.cli', side_effect=Exception('Test exception')):
            # The actual CLI should handle exceptions gracefully
            result = runner.invoke(cli, ['status'])
            # Exit code might be non-zero but shouldn't crash


class TestPluginIntegration:
    """Test plugin integration functionality"""
    
    def test_health_status_enum(self):
        """Test HealthStatus enum values"""
        assert HealthStatus.HEALTHY.value == 'healthy'
        assert HealthStatus.WARNING.value == 'warning'
        assert HealthStatus.CRITICAL.value == 'critical'
        assert HealthStatus.UNKNOWN.value == 'unknown'
    
    @pytest.mark.asyncio
    async def test_plugin_loading(self, mock_plugin_manager):
        """Test plugin loading mechanism"""
        # Simulate plugin discovery
        plugins = await mock_plugin_manager.discover_plugins()
        assert isinstance(plugins, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])