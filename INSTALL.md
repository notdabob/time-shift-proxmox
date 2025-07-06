# Installation Guide for Time-Shift Proxmox

## Method 1: Direct Download and Run

```bash
# Download the setup script first
wget https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/setup.sh
# OR use curl
curl -o setup.sh https://raw.githubusercontent.com/notdabob/time-shift-proxmox/main/setup.sh

# Make it executable and run
chmod +x setup.sh
sudo ./setup.sh
```

## Method 2: Git Clone and Setup

```bash
# Clone the repository
git clone https://github.com/notdabob/time-shift-proxmox.git
cd time-shift-proxmox

# Run the setup
sudo ./setup.sh
```

## Method 3: Manual Installation

```bash
# Clone repository
git clone https://github.com/notdabob/time-shift-proxmox.git
cd time-shift-proxmox

# Install dependencies
apt-get update
apt-get install -y python3 python3-pip python3-venv ntp ntpdate curl jq git

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x bin/*.py
chmod +x *.sh

# Run configuration wizard
./bin/vm-config-wizard.py
```

## Troubleshooting

If you get a 404 error with curl, try:

1. Check your internet connection
2. Try using wget instead of curl
3. Manually navigate to https://github.com/notdabob/time-shift-proxmox and download the setup.sh file
4. Check if your Proxmox host has any proxy settings that might be interfering

## Quick Test

After installation, test with:

```bash
# From the installation directory
./time-shift-idrac.sh 192.168.1.100
```

Replace 192.168.1.100 with your actual iDRAC IP address.