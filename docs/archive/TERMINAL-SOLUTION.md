# Direct Terminal Solution

Based on your terminal output, here's the exact solution:

## Step 1: Check your .pat file

```bash
cat .pat
```

If it shows "YOUR_GITHUB_TOKEN_HERE" or is empty, update it:

```bash
echo 'ghp_YourActualGitHubToken' > .pat
```

## Step 2: Clone the repository properly

```bash
# Read token from .pat file
TOKEN=$(cat .pat)

# Configure git
git config --global credential.helper store
echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# Clone fresh copy
rm -rf time-shift-proxmox
git clone https://github.com/notdabob/time-shift-proxmox.git
cd time-shift-proxmox

# Run setup
sudo ./setup.sh
```

## Step 3: Use the correct commands

After setup completes:

```bash
# The time-shift-cli is in the bin directory
./bin/time-shift-cli.py --help

# Or use the convenience script
./time-shift-idrac.sh 192.168.1.100

# Or use the global command
time-shift-idrac 192.168.1.100
```

## Complete One-Liner Fix

```bash
TOKEN=$(cat .pat) && git config --global credential.helper store && echo "https://notdabob:${TOKEN}@github.com" > ~/.git-credentials && rm -rf time-shift-proxmox && git clone https://github.com/notdabob/time-shift-proxmox.git && cd time-shift-proxmox && sudo ./setup.sh
```

## The Issue

Your installation at `/opt/time-shift-proxmox` seems incomplete. The fresh clone will give you the complete repository with all scripts in the correct locations.