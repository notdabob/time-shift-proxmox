"""
Time Operations Module - Time manipulation functions
Handles system time manipulation for accessing systems with expired SSL certificates
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
import json
import shutil

class TimeOperations:
    """Handles system time manipulation operations"""
    
    def __init__(self):
        """Initialize TimeOperations"""
        self.logger = logging.getLogger(__name__)
        self.backup_file = "/tmp/original_time_backup.json"
        self.original_time = None
        
    def backup_current_time(self):
        """
        Backup current system time
        
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            # Get current system time
            result = subprocess.run(['date', '+%Y-%m-%d %H:%M:%S'], 
                                  capture_output=True, text=True, check=True)
            current_time = result.stdout.strip()
            
            # Get timezone
            result = subprocess.run(['timedatectl', 'show', '--property=Timezone'], 
                                  capture_output=True, text=True, check=True)
            timezone = result.stdout.strip().split('=')[1]
            
            # Get NTP status
            result = subprocess.run(['timedatectl', 'show', '--property=NTP'], 
                                  capture_output=True, text=True, check=True)
            ntp_enabled = result.stdout.strip().split('=')[1] == 'yes'
            
            backup_data = {
                'timestamp': current_time,
                'timezone': timezone,
                'ntp_enabled': ntp_enabled,
                'backup_created': datetime.now().isoformat()
            }
            
            with open(self.backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            self.original_time = backup_data
            self.logger.info(f"Current time backed up: {current_time}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to backup current time: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error backing up time: {e}")
            return False
    
    def shift_time(self, target_date):
        """
        Shift system time to target date
        
        Args:
            target_date (str): Target date in YYYY-MM-DD format
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First backup current time
            if not self.backup_current_time():
                return False
            
            # Disable NTP to prevent time sync
            self.logger.info("Disabling NTP synchronization")
            subprocess.run(['sudo', 'timedatectl', 'set-ntp', 'false'], 
                          check=True)
            
            # Parse target date and set to noon to avoid timezone issues
            target_datetime = f"{target_date} 12:00:00"
            
            # Set system time
            self.logger.info(f"Setting system time to: {target_datetime}")
            subprocess.run(['sudo', 'date', '-s', target_datetime], 
                          check=True)
            
            # Sync hardware clock
            subprocess.run(['sudo', 'hwclock', '--systohc'], 
                          check=True)
            
            self.logger.info(f"Successfully shifted time to {target_date}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to shift time: {e}")
            # Attempt to restore if shift failed
            self.restore_time()
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error shifting time: {e}")
            return False
    
    def restore_time(self):
        """
        Restore original system time from backup
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if backup exists
            if not os.path.exists(self.backup_file):
                self.logger.warning("No time backup found, enabling NTP sync")
                # Just enable NTP to sync with time servers
                subprocess.run(['sudo', 'timedatectl', 'set-ntp', 'true'], 
                              check=True)
                return True
            
            # Load backup data
            with open(self.backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Re-enable NTP if it was originally enabled
            if backup_data.get('ntp_enabled', True):
                self.logger.info("Re-enabling NTP synchronization")
                subprocess.run(['sudo', 'timedatectl', 'set-ntp', 'true'], 
                              check=True)
                # Wait a moment for NTP sync
                import time
                time.sleep(2)
            else:
                # Restore exact time if NTP was disabled
                original_time = backup_data['timestamp']
                self.logger.info(f"Restoring original time: {original_time}")
                subprocess.run(['sudo', 'date', '-s', original_time], 
                              check=True)
                subprocess.run(['sudo', 'hwclock', '--systohc'], 
                              check=True)
            
            # Clean up backup file
            os.remove(self.backup_file)
            
            self.logger.info("Successfully restored original time")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to restore time: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error restoring time: {e}")
            return False
    
    def get_current_time(self):
        """
        Get current system time
        
        Returns:
            str: Current time string or None if failed
        """
        try:
            result = subprocess.run(['date', '+%Y-%m-%d %H:%M:%S'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get current time: {e}")
            return None
    
    def validate_date_format(self, date_string):
        """
        Validate date format (YYYY-MM-DD)
        
        Args:
            date_string (str): Date string to validate
            
        Returns:
            bool: True if valid format, False otherwise
        """
        try:
            datetime.strptime(date_string, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def calculate_cert_valid_date(self, cert_expiry_date, days_before=30):
        """
        Calculate a suitable date before certificate expiry
        
        Args:
            cert_expiry_date (str): Certificate expiry date (YYYY-MM-DD)
            days_before (int): Days before expiry to target
            
        Returns:
            str: Target date string or None if invalid
        """
        try:
            expiry = datetime.strptime(cert_expiry_date, '%Y-%m-%d')
            target = expiry - timedelta(days=days_before)
            return target.strftime('%Y-%m-%d')
        except ValueError:
            self.logger.error(f"Invalid certificate expiry date: {cert_expiry_date}")
            return None
    
    def is_ntp_enabled(self):
        """
        Check if NTP synchronization is enabled
        
        Returns:
            bool: True if NTP enabled, False otherwise
        """
        try:
            result = subprocess.run(['timedatectl', 'show', '--property=NTP'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip().split('=')[1] == 'yes'
        except subprocess.CalledProcessError:
            return False
