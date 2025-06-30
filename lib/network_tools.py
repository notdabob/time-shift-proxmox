"""
Network Tools Module - Network validation utilities
Provides network connectivity testing and SSL certificate validation
"""

import socket
import ssl
import subprocess
import logging
import requests
import urllib3
from datetime import datetime
import json

# Disable SSL warnings for connections to systems with expired certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NetworkValidator:
    """Network connectivity and SSL certificate validation utilities"""
    
    def __init__(self):
        """Initialize NetworkValidator"""
        self.logger = logging.getLogger(__name__)
        self.timeout = 10
    
    def ping_host(self, host, count=4):
        """
        Ping a host to test basic connectivity
        
        Args:
            host (str): Hostname or IP address
            count (int): Number of ping packets
            
        Returns:
            bool: True if ping successful, False otherwise
        """
        try:
            result = subprocess.run(
                ['ping', '-c', str(count), host],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Ping to {host} successful")
                return True
            else:
                self.logger.warning(f"Ping to {host} failed")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Ping to {host} timed out")
            return False
        except Exception as e:
            self.logger.error(f"Ping error: {e}")
            return False
    
    def check_port_open(self, host, port):
        """
        Check if a specific port is open on a host
        
        Args:
            host (str): Hostname or IP address
            port (int): Port number
            
        Returns:
            bool: True if port is open, False otherwise
        """
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                self.logger.info(f"Port {port} is open on {host}")
                return True
        except (socket.timeout, socket.error) as e:
            self.logger.warning(f"Port {port} is closed on {host}: {e}")
            return False
    
    def get_ssl_certificate_info(self, host, port=443):
        """
        Get SSL certificate information from a host
        
        Args:
            host (str): Hostname or IP address
            port (int): Port number (default 443)
            
        Returns:
            dict: Certificate information or None if failed
        """
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    
                    cert_info = {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert['version'],
                        'serial_number': cert['serialNumber'],
                        'not_before': cert['notBefore'],
                        'not_after': cert['notAfter'],
                        'expired': datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z') < datetime.now()
                    }
                    
                    self.logger.info(f"Retrieved SSL certificate for {host}")
                    return cert_info
                    
        except Exception as e:
            self.logger.error(f"Failed to get SSL certificate info: {e}")
            return None
    
    def validate_idrac_connection(self, idrac_ip, username=None, password=None):
        """
        Validate connection to Dell iDRAC interface
        
        Args:
            idrac_ip (str): iDRAC IP address
            username (str): Optional username (default: root)
            password (str): Optional password (default: calvin)
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        # Test basic connectivity first
        if not self.ping_host(idrac_ip, count=2):
            self.logger.error(f"Cannot ping iDRAC at {idrac_ip}")
            return False
        
        # Test HTTPS port
        if not self.check_port_open(idrac_ip, 443):
            self.logger.error(f"HTTPS port 443 not accessible on {idrac_ip}")
            return False
        
        # Try to access iDRAC web interface
        try:
            url = f"https://{idrac_ip}"
            response = requests.get(
                url,
                timeout=self.timeout,
                verify=False  # Ignore SSL certificate issues
            )
            
            if response.status_code in [200, 401, 403]:
                self.logger.info(f"iDRAC web interface accessible at {idrac_ip}")
                
                # Get certificate info
                cert_info = self.get_ssl_certificate_info(idrac_ip)
                if cert_info:
                    if cert_info['expired']:
                        self.logger.warning(f"iDRAC SSL certificate is expired")
                    else:
                        self.logger.info(f"iDRAC SSL certificate is valid")
                
                return True
            else:
                self.logger.error(f"Unexpected HTTP status: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to connect to iDRAC web interface: {e}")
            return False
    
    def test_connectivity_suite(self, targets):
        """
        Run comprehensive connectivity tests against multiple targets
        
        Args:
            targets (list): List of target dictionaries with 'host' and optional 'port'
            
        Returns:
            dict: Test results for each target
        """
        results = {}
        
        for target in targets:
            host = target['host']
            port = target.get('port', 443)
            
            self.logger.info(f"Testing connectivity to {host}:{port}")
            
            results[host] = {
                'ping': self.ping_host(host),
                'port_open': self.check_port_open(host, port),
                'ssl_cert': self.get_ssl_certificate_info(host, port),
                'timestamp': datetime.now().isoformat()
            }
            
            # Special handling for iDRAC interfaces
            if target.get('type') == 'idrac':
                results[host]['idrac_accessible'] = self.validate_idrac_connection(host)
        
        return results
    
    def generate_connectivity_report(self, results, output_file=None):
        """
        Generate a human-readable connectivity report
        
        Args:
            results (dict): Results from test_connectivity_suite
            output_file (str): Optional file path to save report
            
        Returns:
            str: Formatted report
        """
        report_lines = []
        report_lines.append("Network Connectivity Report")
        report_lines.append("=" * 40)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        for host, tests in results.items():
            report_lines.append(f"Target: {host}")
            report_lines.append("-" * 20)
            
            report_lines.append(f"  Ping: {'✓' if tests['ping'] else '✗'}")
            report_lines.append(f"  Port Open: {'✓' if tests['port_open'] else '✗'}")
            
            if tests.get('ssl_cert'):
                cert = tests['ssl_cert']
                status = "EXPIRED" if cert['expired'] else "VALID"
                report_lines.append(f"  SSL Certificate: {status}")
                report_lines.append(f"    Expires: {cert['not_after']}")
            else:
                report_lines.append(f"  SSL Certificate: Not Available")
            
            if tests.get('idrac_accessible') is not None:
                report_lines.append(f"  iDRAC Access: {'✓' if tests['idrac_accessible'] else '✗'}")
            
            report_lines.append("")
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            self.logger.info(f"Connectivity report saved to {output_file}")
        
        return report
    
    def dns_lookup(self, hostname):
        """
        Perform DNS lookup for hostname
        
        Args:
            hostname (str): Hostname to resolve
            
        Returns:
            str: IP address or None if failed
        """
        try:
            ip = socket.gethostbyname(hostname)
            self.logger.info(f"DNS lookup for {hostname}: {ip}")
            return ip
        except socket.gaierror as e:
            self.logger.error(f"DNS lookup failed for {hostname}: {e}")
            return None
