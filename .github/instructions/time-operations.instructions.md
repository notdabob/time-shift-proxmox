---
applyTo: ["lib/time_ops.py", "**/time/**", "**/*time*", "time-shift-idrac.sh"]
---

# Time Operations Instructions

## Time Manipulation Framework

### Core Time Operations
```python
from datetime import datetime, timezone, timedelta
import subprocess
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

class TimeShiftManager:
    """Secure time manipulation with automatic restoration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_time: Optional[datetime] = None
        self.is_shifted = False
        
    async def get_current_system_time(self) -> datetime:
        """Get current system time"""
        return datetime.now(timezone.utc)
    
    async def backup_original_time(self) -> datetime:
        """Backup current system time before manipulation"""
        if self.original_time is None:
            self.original_time = await self.get_current_system_time()
            self.logger.info(f"Original time backed up: {self.original_time.isoformat()}")
        return self.original_time
    
    @asynccontextmanager
    async def temporary_time_shift(self, target_time: datetime, duration: int = 300):
        """Context manager for safe temporary time shifting"""
        await self.backup_original_time()
        
        try:
            # Shift to target time
            await self.shift_system_time(target_time)
            self.logger.warning(f"Time shifted to: {target_time.isoformat()}")
            
            yield target_time
            
        finally:
            # Always restore original time
            if self.original_time:
                await self.restore_original_time()
                self.logger.info("Time restored to original value")
    
    async def shift_system_time(self, target_time: datetime) -> bool:
        """Shift system time to target datetime"""
        if self.is_shifted:
            raise RuntimeError("Time is already shifted. Restore before shifting again.")
        
        try:
            # Format time for system command
            time_str = target_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Use timedatectl if available (systemd systems)
            result = await asyncio.create_subprocess_exec(
                'timedatectl', 'set-time', time_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self.is_shifted = True
                self.logger.warning(f"System time changed to: {time_str}")
                return True
            else:
                # Fallback to date command
                return await self._fallback_time_set(target_time)
                
        except Exception as e:
            self.logger.error(f"Failed to shift time: {e}")
            raise RuntimeError(f"Time shift failed: {e}")
    
    async def _fallback_time_set(self, target_time: datetime) -> bool:
        """Fallback time setting using date command"""
        try:
            time_str = target_time.strftime("%m%d%H%M%Y.%S")
            
            result = await asyncio.create_subprocess_exec(
                'date', time_str,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                self.is_shifted = True
                return True
            else:
                raise RuntimeError(f"Date command failed: {stderr.decode()}")
                
        except Exception as e:
            self.logger.error(f"Fallback time set failed: {e}")
            raise
    
    async def restore_original_time(self) -> bool:
        """Restore system time to original value"""
        if not self.original_time:
            raise RuntimeError("No original time backup found")
        
        try:
            # Calculate elapsed time since backup
            current_real_time = datetime.now(timezone.utc)
            elapsed = current_real_time - self.original_time
            
            # Restore to current real time (not backup time)
            await self.shift_system_time(current_real_time)
            
            self.is_shifted = False
            self.original_time = None
            
            self.logger.info(f"Time restored. Elapsed during shift: {elapsed}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore time: {e}")
            raise RuntimeError(f"Time restoration failed: {e}")
```

### SSL Certificate Time Bypass
```python
from datetime import datetime, timedelta
import ssl
import socket
from typing import Tuple, Optional

class SSLCertificateHandler:
    """Handle SSL certificates with time-based validity issues"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_certificate_validity(self, hostname: str, port: int = 443) -> Tuple[datetime, datetime]:
        """Get certificate validity period"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    
                    return not_before, not_after
                    
        except Exception as e:
            self.logger.error(f"Failed to get certificate for {hostname}:{port}: {e}")
            raise
    
    async def calculate_valid_time(self, hostname: str, port: int = 443) -> datetime:
        """Calculate a valid time within certificate validity period"""
        not_before, not_after = await self.get_certificate_validity(hostname, port)
        
        # Choose a time in the middle of the validity period
        validity_duration = not_after - not_before
        target_time = not_before + (validity_duration / 2)
        
        self.logger.info(f"Certificate valid from {not_before} to {not_after}")
        self.logger.info(f"Calculated target time: {target_time}")
        
        return target_time
    
    async def is_certificate_expired(self, hostname: str, port: int = 443) -> bool:
        """Check if certificate is currently expired"""
        try:
            _, not_after = await self.get_certificate_validity(hostname, port)
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            
            return current_time > not_after
        except Exception:
            return True  # Assume expired if we can't check
```

### iDRAC Time Shift Integration
```python
class iDRACTimeShiftManager:
    """Specialized time shifting for Dell iDRAC access"""
    
    def __init__(self, time_manager: TimeShiftManager, ssl_handler: SSLCertificateHandler):
        self.time_manager = time_manager
        self.ssl_handler = ssl_handler
        self.logger = logging.getLogger(__name__)
    
    async def access_idrac_with_timeshift(self, idrac_host: str, username: str = "root", 
                                        password: str = "calvin", duration: int = 300) -> Dict[str, Any]:
        """Access iDRAC with automatic time shifting for expired certificates"""
        
        # Check if certificate is expired
        if not await self.ssl_handler.is_certificate_expired(idrac_host, 443):
            self.logger.info("Certificate is not expired, no time shift needed")
            return await self._access_idrac_direct(idrac_host, username, password)
        
        # Calculate valid time for certificate
        target_time = await self.ssl_handler.calculate_valid_time(idrac_host, 443)
        
        # Perform time-shifted access
        async with self.time_manager.temporary_time_shift(target_time, duration):
            self.logger.info(f"Accessing iDRAC {idrac_host} with time-shifted certificate validation")
            return await self._access_idrac_direct(idrac_host, username, password)
    
    async def _access_idrac_direct(self, host: str, username: str, password: str) -> Dict[str, Any]:
        """Direct iDRAC access (called within time-shift context)"""
        import aiohttp
        
        # Configure for iDRAC SSL (typically self-signed/expired)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        auth = aiohttp.BasicAuth(username, password)
        
        async with aiohttp.ClientSession(
            auth=auth,
            connector=aiohttp.TCPConnector(ssl=ssl_context),
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            # Get system information
            async with session.get(f"https://{host}/redfish/v1/Systems") as response:
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"Successfully connected to iDRAC {host}")
                    return data
                else:
                    raise RuntimeError(f"iDRAC access failed with status {response.status}")
```

### Time Validation and Safety
```python
class TimeValidator:
    """Validate time operations for safety"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.MAX_TIME_SHIFT_YEARS = 10  # Maximum years to shift
        self.MIN_SHIFT_DURATION = 60    # Minimum shift duration in seconds
        self.MAX_SHIFT_DURATION = 3600  # Maximum shift duration in seconds
    
    def validate_target_time(self, target_time: datetime) -> bool:
        """Validate that target time is reasonable"""
        current_time = datetime.now(timezone.utc)
        time_diff = abs((target_time - current_time).days / 365.25)
        
        if time_diff > self.MAX_TIME_SHIFT_YEARS:
            raise ValueError(f"Time shift too large: {time_diff:.1f} years")
        
        # Check for obviously invalid dates
        if target_time.year < 2000 or target_time.year > 2050:
            raise ValueError(f"Invalid target year: {target_time.year}")
        
        return True
    
    def validate_shift_duration(self, duration: int) -> bool:
        """Validate shift duration is within safe limits"""
        if duration < self.MIN_SHIFT_DURATION:
            raise ValueError(f"Shift duration too short: {duration}s (min: {self.MIN_SHIFT_DURATION}s)")
        
        if duration > self.MAX_SHIFT_DURATION:
            raise ValueError(f"Shift duration too long: {duration}s (max: {self.MAX_SHIFT_DURATION}s)")
        
        return True
    
    def validate_certificate_date_range(self, not_before: datetime, not_after: datetime) -> datetime:
        """Validate certificate dates and return safe target time"""
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Ensure certificate period is reasonable
        validity_period = (not_after - not_before).days
        if validity_period < 30:  # Less than 30 days
            self.logger.warning(f"Certificate has very short validity period: {validity_period} days")
        
        if validity_period > 3650:  # More than 10 years
            raise ValueError(f"Certificate validity period too long: {validity_period} days")
        
        # Choose target time (avoid edges of validity period)
        margin = timedelta(days=30)  # 30-day margin from edges
        safe_start = not_before + margin
        safe_end = not_after - margin
        
        if safe_start >= safe_end:
            # Very short certificate, use middle
            target_time = not_before + (not_after - not_before) / 2
        else:
            # Use middle of safe period
            target_time = safe_start + (safe_end - safe_start) / 2
        
        self.validate_target_time(target_time)
        return target_time
```

### Time Synchronization Management
```python
class TimeSyncManager:
    """Manage time synchronization services during time shifts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ntp_was_active = False
        self.timesyncd_was_active = False
    
    async def disable_time_sync(self) -> None:
        """Disable automatic time synchronization"""
        try:
            # Check and disable systemd-timesyncd
            result = await asyncio.create_subprocess_exec(
                'systemctl', 'is-active', 'systemd-timesyncd',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                self.timesyncd_was_active = True
                await asyncio.create_subprocess_exec('systemctl', 'stop', 'systemd-timesyncd')
                self.logger.info("Disabled systemd-timesyncd")
            
            # Check and disable NTP
            result = await asyncio.create_subprocess_exec(
                'systemctl', 'is-active', 'ntp',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await result.communicate()
            
            if result.returncode == 0:
                self.ntp_was_active = True
                await asyncio.create_subprocess_exec('systemctl', 'stop', 'ntp')
                self.logger.info("Disabled NTP")
                
        except Exception as e:
            self.logger.warning(f"Failed to disable time sync: {e}")
    
    async def restore_time_sync(self) -> None:
        """Restore automatic time synchronization"""
        try:
            if self.timesyncd_was_active:
                await asyncio.create_subprocess_exec('systemctl', 'start', 'systemd-timesyncd')
                self.logger.info("Re-enabled systemd-timesyncd")
                self.timesyncd_was_active = False
            
            if self.ntp_was_active:
                await asyncio.create_subprocess_exec('systemctl', 'start', 'ntp')
                self.logger.info("Re-enabled NTP")
                self.ntp_was_active = False
                
        except Exception as e:
            self.logger.warning(f"Failed to restore time sync: {e}")
```

## Best Practices

### 1. Safety First
- **ALWAYS** backup original time before shifting
- Implement automatic restoration mechanisms
- Validate time values before system changes
- Use context managers for guaranteed cleanup

### 2. Monitoring & Logging
- Log all time manipulation operations
- Monitor for drift during time shifts
- Track duration of time-shifted operations
- Audit time-related security events

### 3. System Integration
- Disable NTP/timesyncd during time shifts
- Handle systemd-timesyncd and chrony
- Manage hardware clock synchronization
- Consider timezone implications

### 4. Error Recovery
- Implement robust restoration mechanisms
- Handle partial failures gracefully
- Provide manual recovery procedures
- Test restoration in various failure scenarios

### 5. Security Considerations
- Log all time changes for audit
- Validate certificate dates before shifting
- Limit maximum time shift duration
- Monitor for unauthorized time changes

### Common Pitfalls to Avoid

1. **Forgetting to restore time**: Always use context managers
2. **Large time shifts**: Validate reasonable time ranges
3. **NTP conflicts**: Disable time sync during operations
4. **Timezone confusion**: Work in UTC internally
5. **Certificate edge cases**: Add margins to validity periods
6. **Concurrent time operations**: Prevent multiple simultaneous shifts
7. **System clock drift**: Monitor and compensate for drift