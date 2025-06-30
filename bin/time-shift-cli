#!/usr/bin/env python3
"""
Time-Shift CLI - Main CLI interface
Main command-line interface for the Time-Shift Proxmox VM Solution
"""

import sys
import os
import argparse
import json
from datetime import datetime, timedelta

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from proxmox_api import ProxmoxAPI
from time_ops import TimeOperations
from network_tools import NetworkValidator

def main():
    parser = argparse.ArgumentParser(description='Time-Shift Proxmox VM Solution')
    parser.add_argument('--config', '-c', default='/etc/time-shift-config.json',
                       help='Configuration file path')
    parser.add_argument('--vm-id', type=int, help='Proxmox VM ID')
    parser.add_argument('--target-date', help='Target date (YYYY-MM-DD)')
    parser.add_argument('--idrac-ip', help='iDRAC IP address to access')
    parser.add_argument('--action', choices=['shift', 'restore', 'validate'],
                       default='shift', help='Action to perform')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file {args.config} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    
    # Initialize components
    proxmox = ProxmoxAPI(config.get('proxmox', {}))
    time_ops = TimeOperations()
    network = NetworkValidator()
    
    if args.action == 'shift':
        if not args.target_date:
            print("Error: --target-date is required for shift action")
            sys.exit(1)
        
        # Perform time shift operation
        result = time_ops.shift_time(args.target_date)
        if result:
            print(f"Successfully shifted time to {args.target_date}")
        else:
            print("Failed to shift time")
            sys.exit(1)
            
    elif args.action == 'restore':
        # Restore original time
        result = time_ops.restore_time()
        if result:
            print("Successfully restored original time")
        else:
            print("Failed to restore time")
            sys.exit(1)
            
    elif args.action == 'validate':
        if not args.idrac_ip:
            print("Error: --idrac-ip is required for validate action")
            sys.exit(1)
            
        # Validate network connectivity to iDRAC
        result = network.validate_idrac_connection(args.idrac_ip)
        if result:
            print(f"Successfully connected to iDRAC at {args.idrac_ip}")
        else:
            print(f"Failed to connect to iDRAC at {args.idrac_ip}")
            sys.exit(1)

if __name__ == '__main__':
    main()
