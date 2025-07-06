"""
Test suite for time operations module
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock, call
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from time_ops import TimeOperations


class TestTimeOperations:
    """Test TimeOperations functionality"""
    
    @pytest.fixture
    def time_ops(self):
        """Create a TimeOperations instance"""
        return TimeOperations()
    
    def test_get_current_time(self, time_ops):
        """Test getting current system time"""
        current_time = time_ops.get_current_time()
        
        assert isinstance(current_time, datetime)
        # Time should be close to now (within 1 second)
        time_diff = abs((datetime.now() - current_time).total_seconds())
        assert time_diff < 1
    
    @pytest.mark.asyncio
    async def test_backup_time(self, time_ops):
        """Test backing up current time"""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            current_time = datetime.now()
            with patch.object(time_ops, 'get_current_time', return_value=current_time):
                result = await time_ops.backup_time()
            
            assert result is True
            mock_open.assert_called_once_with('/tmp/time_shift_backup.txt', 'w')
            mock_file.write.assert_called_once()
            written_content = mock_file.write.call_args[0][0]
            assert current_time.isoformat() in written_content
    
    @pytest.mark.asyncio
    async def test_restore_time(self, time_ops):
        """Test restoring backed up time"""
        backup_time = datetime(2024, 1, 1, 12, 0, 0)
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = backup_time.isoformat()
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                
                result = await time_ops.restore_time()
                
                assert result is True
                mock_run.assert_called()
                # Check that date command was called with correct format
                date_cmd = mock_run.call_args[0][0]
                assert date_cmd[0] == 'date'
                assert date_cmd[1] == '-s'
    
    @pytest.mark.asyncio
    async def test_restore_time_no_backup(self, time_ops):
        """Test restoring time when no backup exists"""
        with patch('os.path.exists', return_value=False):
            result = await time_ops.restore_time()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_set_time(self, time_ops):
        """Test setting system time"""
        target_time = datetime(2023, 1, 1, 12, 0, 0)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = await time_ops.set_time(target_time)
            
            assert result is True
            mock_run.assert_called_once()
            date_cmd = mock_run.call_args[0][0]
            assert date_cmd[0] == 'date'
            assert date_cmd[1] == '-s'
            assert '2023-01-01' in date_cmd[2]
    
    @pytest.mark.asyncio
    async def test_set_time_failure(self, time_ops):
        """Test handling set time failure"""
        target_time = datetime(2023, 1, 1, 12, 0, 0)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr='Permission denied')
            
            result = await time_ops.set_time(target_time)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_shift_time(self, time_ops):
        """Test shifting time by delta"""
        # Test shift backward
        with patch.object(time_ops, 'set_time', new_callable=AsyncMock) as mock_set:
            mock_set.return_value = True
            
            result = await time_ops.shift_time(days=-365)
            
            assert result is True
            mock_set.assert_called_once()
            set_time_arg = mock_set.call_args[0][0]
            # Should be approximately 365 days ago
            time_diff = (datetime.now() - set_time_arg).days
            assert 364 <= time_diff <= 366
    
    @pytest.mark.asyncio
    async def test_sync_with_ntp(self, time_ops):
        """Test NTP synchronization"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),  # Stop ntp
                MagicMock(returncode=0),  # ntpdate
                MagicMock(returncode=0)   # Start ntp
            ]
            
            result = await time_ops.sync_with_ntp(['pool.ntp.org'])
            
            assert result is True
            assert mock_run.call_count == 3
            
            # Verify commands
            calls = mock_run.call_args_list
            assert 'systemctl' in calls[0][0][0][0]
            assert 'stop' in calls[0][0][0]
            assert 'ntpdate' in calls[1][0][0][0]
            assert 'pool.ntp.org' in calls[1][0][0]
            assert 'systemctl' in calls[2][0][0][0]
            assert 'start' in calls[2][0][0]
    
    @pytest.mark.asyncio
    async def test_sync_with_ntp_no_servers(self, time_ops):
        """Test NTP sync with no servers"""
        result = await time_ops.sync_with_ntp([])
        assert result is False
    
    def test_calculate_cert_validity_window(self, time_ops):
        """Test calculating certificate validity window"""
        cert_expiry = datetime(2020, 1, 1, 12, 0, 0)
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            window_start, window_end = time_ops.calculate_cert_validity_window(cert_expiry)
            
            # Should be 30 days before expiry
            assert window_start < cert_expiry
            assert (cert_expiry - window_start).days == 30
            
            # Should be 1 day before expiry
            assert window_end < cert_expiry
            assert (cert_expiry - window_end).days == 1
    
    @pytest.mark.asyncio
    async def test_temporary_time_shift_context(self, time_ops):
        """Test temporary time shift context manager"""
        target_time = datetime(2020, 1, 1, 12, 0, 0)
        
        with patch.object(time_ops, 'backup_time', new_callable=AsyncMock) as mock_backup:
            with patch.object(time_ops, 'set_time', new_callable=AsyncMock) as mock_set:
                with patch.object(time_ops, 'restore_time', new_callable=AsyncMock) as mock_restore:
                    mock_backup.return_value = True
                    mock_set.return_value = True
                    mock_restore.return_value = True
                    
                    async with time_ops.temporary_time_shift(target_time) as success:
                        assert success is True
                        mock_backup.assert_called_once()
                        mock_set.assert_called_once_with(target_time)
                    
                    # Restore should be called after context
                    mock_restore.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_temporary_time_shift_failure(self, time_ops):
        """Test temporary time shift with failure"""
        target_time = datetime(2020, 1, 1, 12, 0, 0)
        
        with patch.object(time_ops, 'backup_time', new_callable=AsyncMock) as mock_backup:
            with patch.object(time_ops, 'set_time', new_callable=AsyncMock) as mock_set:
                with patch.object(time_ops, 'restore_time', new_callable=AsyncMock) as mock_restore:
                    mock_backup.return_value = True
                    mock_set.return_value = False  # Fail to set time
                    mock_restore.return_value = True
                    
                    async with time_ops.temporary_time_shift(target_time) as success:
                        assert success is False
                    
                    # Restore should still be called
                    mock_restore.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_temporary_time_shift_exception(self, time_ops):
        """Test temporary time shift with exception during operation"""
        target_time = datetime(2020, 1, 1, 12, 0, 0)
        
        with patch.object(time_ops, 'backup_time', new_callable=AsyncMock) as mock_backup:
            with patch.object(time_ops, 'set_time', new_callable=AsyncMock) as mock_set:
                with patch.object(time_ops, 'restore_time', new_callable=AsyncMock) as mock_restore:
                    mock_backup.return_value = True
                    mock_set.return_value = True
                    mock_restore.return_value = True
                    
                    with pytest.raises(ValueError):
                        async with time_ops.temporary_time_shift(target_time):
                            raise ValueError("Test exception")
                    
                    # Restore should still be called even with exception
                    mock_restore.assert_called_once()
    
    def test_validate_time_permissions(self, time_ops):
        """Test validating time modification permissions"""
        with patch('os.geteuid', return_value=0):  # Root user
            assert time_ops.validate_time_permissions() is True
        
        with patch('os.geteuid', return_value=1000):  # Non-root user
            assert time_ops.validate_time_permissions() is False
    
    @pytest.mark.asyncio
    async def test_get_system_timezone(self, time_ops):
        """Test getting system timezone"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='America/New_York\n'
            )
            
            tz = await time_ops.get_system_timezone()
            
            assert tz == 'America/New_York'
            mock_run.assert_called_once()
            assert 'timedatectl' in mock_run.call_args[0][0][0]
    
    @pytest.mark.asyncio
    async def test_set_system_timezone(self, time_ops):
        """Test setting system timezone"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = await time_ops.set_system_timezone('UTC')
            
            assert result is True
            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert 'timedatectl' in cmd[0]
            assert 'set-timezone' in cmd
            assert 'UTC' in cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])