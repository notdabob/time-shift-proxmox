#!/usr/bin/env python3
"""
VM Configuration Wizard - Initial setup wizard
Interactive wizard for initial VM setup and configuration
"""

import sys
import os
import json
import getpass
from pathlib import Path

def welcome():
    print("=" * 60)
    print("Time-Shift Proxmox VM Configuration Wizard")
    print("=" * 60)
    print("This wizard will help you configure your Time-Shift VM solution.")
    print()

def get_proxmox_config():
    print("Proxmox Configuration:")
    print("-" * 20)
    
    host = input("Proxmox host (IP or hostname): ").strip()
    port = input("Proxmox port [8006]: ").strip() or "8006"
    username = input("Proxmox username: ").strip()
    password = getpass.getpass("Proxmox password: ")
    node = input("Proxmox node name: ").strip()
    
    return {
        "host": host,
        "port": int(port),
        "username": username,
        "password": password,
        "node": node,
        "verify_ssl": False
    }

def get_vm_config():
    print("\nVM Configuration:")
    print("-" * 16)
    
    vm_name = input("VM name [time-shift-vm]: ").strip() or "time-shift-vm"
    memory = input("Memory (MB) [2048]: ").strip() or "2048"
    cores = input("CPU cores [2]: ").strip() or "2"
    disk_size = input("Disk size (GB) [20]: ").strip() or "20"
    
    return {
        "name": vm_name,
        "memory": int(memory),
        "cores": int(cores),
        "disk_size": int(disk_size),
        "os_type": "l26",  # Linux 2.6+
        "template": "debian-12-standard"
    }

def get_network_config():
    print("\nNetwork Configuration:")
    print("-" * 21)
    
    bridge = input("Bridge interface [vmbr0]: ").strip() or "vmbr0"
    ip_config = input("IP configuration (dhcp/static) [dhcp]: ").strip() or "dhcp"
    
    config = {
        "bridge": bridge,
        "ip_config": ip_config
    }
    
    if ip_config.lower() == "static":
        config["ip"] = input("Static IP address: ").strip()
        config["netmask"] = input("Netmask [255.255.255.0]: ").strip() or "255.255.255.0"
        config["gateway"] = input("Gateway: ").strip()
        config["dns"] = input("DNS server: ").strip()
    
    return config

def get_time_config():
    print("\nTime Configuration:")
    print("-" * 18)
    
    timezone = input("Timezone [UTC]: ").strip() or "UTC"
    ntp_servers = input("NTP servers (comma-separated) [pool.ntp.org]: ").strip() or "pool.ntp.org"
    
    return {
        "timezone": timezone,
        "ntp_servers": [s.strip() for s in ntp_servers.split(",")]
    }

def save_config(config, config_path):
    config_dir = os.path.dirname(config_path)
    Path(config_dir).mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nConfiguration saved to: {config_path}")

def main():
    welcome()
    
    # Gather configuration
    proxmox_config = get_proxmox_config()
    vm_config = get_vm_config()
    network_config = get_network_config()
    time_config = get_time_config()
    
    # Combine all configuration
    full_config = {
        "proxmox": proxmox_config,
        "vm": vm_config,
        "network": network_config,
        "time": time_config,
        "logging": {
            "level": "INFO",
            "file": "/var/log/time-shift.log"
        }
    }
    
    # Save configuration
    config_path = "../etc/time-shift-config.json"
    save_config(full_config, config_path)
    
    print("\nConfiguration complete!")
    print("You can now use the time-shift-cli tool to manage your VM.")
    print(f"Example: ./time-shift-cli --config {config_path} --action shift --target-date 2020-01-01")

if __name__ == '__main__':
    main()
