#!/bin/bash

# Proxmox Docker VM Complete Setup Script
# Combines VM creation, Docker installation, Portainer deployment, and QEMU Guest Agent setup
# Author: Based on community-scripts/ProxmoxVE with enhancements
# Usage: Run this script as root on your Proxmox VE host

set -e

# Color codes for output
YW=$(echo "\033[33m")
BL=$(echo "\033[36m") 
RD=$(echo "\033[01;31m")
BGN=$(echo "\033[4;92m")
GN=$(echo "\033[1;92m")
DGN=$(echo "\033[32m")
CL=$(echo "\033[m")
BFR="\\r\\033[K"
HOLD=" "
TAB="  "

# Icons
CM="${TAB}✔️${TAB}${CL}"
CROSS="${TAB}✖️${TAB}${CL}"
INFO="${TAB}💡${TAB}${CL}"

# Configuration variables
VMID=""
VM_NAME="docker"
VM_MEMORY="4096"
VM_CORES="2"
VM_SOCKET="1"
STORAGE="local-lvm"
DISK_SIZE="20G"
OS_TYPE="l26"
BRIDGE="vmbr0"
GEN_MAC=02:$(openssl rand -hex 5 | awk '{print toupper($0)}' | sed 's/\(.*\)/\1:/g; s/.$//')
TEMP_DIR=$(mktemp -d)

# Function definitions
function header_info() {
    clear
    cat <<"EOF"
    ____             __                _    ____  __ 
   / __ \____  _____/ /_____  _____   | |  / /  |/  /
  / / / / __ \/ ___/ //_/ _ \/ ___/   | | / / /|_/ / 
 / /_/ / /_/ / /__/ ,< /  __/ /       | |/ / /  / /  
/____/\____/\___/_/|_|\___/_/        |___/_/  /_/   
                                                    
    Complete Docker VM Setup for Proxmox VE
EOF
    echo -e "\n${INFO}${YW}This script creates a complete Docker VM with Portainer and QEMU Guest Agent${CL}\n"
}

function msg_info() {
    local msg="$1"
    echo -ne "${TAB}${YW}${HOLD}${msg}${HOLD}"
}

function msg_ok() {
    local msg="$1" 
    echo -e "${BFR}${CM}${GN}${msg}${CL}"
}

function msg_error() {
    local msg="$1"
    echo -e "${BFR}${CROSS}${RD}${msg}${CL}"
}

function check_root() {
    if [[ "$(id -u)" -ne 0 || $(ps -o comm= -p $PPID) == "sudo" ]]; then
        clear
        msg_error "Please run this script as root."
        echo -e "\nExiting..."
        sleep 2
        exit 1
    fi
}

function pve_check() {
    if ! pveversion | grep -Eq "pve-manager/[7-8]\.[0-9]"; then
        msg_error "This version of Proxmox Virtual Environment is not supported"
        echo -e "Requires Proxmox Virtual Environment Version 7.0 or later."
        echo -e "Exiting..."
        sleep 2
        exit 1
    fi
}

function get_valid_nextid() {
    local try_id
    try_id=$(pvesh get /cluster/nextid)
    while true; do
        if [ -f "/etc/pve/qemu-server/${try_id}.conf" ] || [ -f "/etc/pve/lxc/${try_id}.conf" ]; then
            try_id=$((try_id + 1))
            continue
        fi
        if lvs --noheadings -o lv_name | grep -qE "(^|[-_])${try_id}($|[-_])"; then
            try_id=$((try_id + 1))
            continue
        fi
        break
    done
    echo "$try_id"
}

function cleanup() {
    rm -rf $TEMP_DIR
}

function cleanup_vmid() {
    if qm status $VMID &>/dev/null; then
        qm stop $VMID &>/dev/null
        qm destroy $VMID &>/dev/null
    fi
}

function error_handler() {
    local exit_code="$?"
    local line_number="$1"
    local command="$2"
    local error_message="${RD}[ERROR]${CL} in line ${RD}$line_number${CL}: exit code ${RD}$exit_code${CL}: while executing command ${YW}$command${CL}"
    echo -e "\n$error_message\n"
    cleanup_vmid
    cleanup
    exit $exit_code
}

trap 'error_handler $LINENO "$BASH_COMMAND"' ERR
trap cleanup EXIT

function get_user_input() {
    echo -e "${INFO}${BL}VM Configuration${CL}"
    
    # Get VM ID
    read -p "Enter VM ID (press Enter for auto): " input_vmid
    if [ -z "$input_vmid" ]; then
        VMID=$(get_valid_nextid)
    else
        if qm status "$input_vmid" &>/dev/null || pct status "$input_vmid" &>/dev/null; then
            msg_error "VM ID $input_vmid is already in use"
            exit 1
        fi
        VMID="$input_vmid"
    fi
    
    # Get VM Name/Hostname
    read -p "Enter VM hostname (default: docker): " input_name
    VM_NAME=${input_name:-docker}
    
    # Get RAM
    read -p "Enter RAM in MB (default: 4096): " input_ram
    VM_MEMORY=${input_ram:-4096}
    
    # Get CPU cores
    read -p "Enter CPU cores (default: 2): " input_cores
    VM_CORES=${input_cores:-2}
    
    # Get disk size
    read -p "Enter disk size (default: 20G): " input_disk
    DISK_SIZE=${input_disk:-20G}
    
    # Get storage
    echo -e "\nAvailable storage:"
    pvesm status -content images | awk 'NR>1 {print "  " $1 " (" $2 ")"}'
    read -p "Enter storage name (default: local-lvm): " input_storage
    STORAGE=${input_storage:-local-lvm}
    
    # Validate storage
    if ! pvesm status -storage "$STORAGE" &>/dev/null; then
        msg_error "Storage '$STORAGE' not found"
        exit 1
    fi
    
    echo -e "\n${INFO}${GN}Configuration Summary:${CL}"
    echo -e "VM ID: ${BL}$VMID${CL}"
    echo -e "Hostname: ${BL}$VM_NAME${CL}" 
    echo -e "RAM: ${BL}${VM_MEMORY}MB${CL}"
    echo -e "CPU Cores: ${BL}$VM_CORES${CL}"
    echo -e "Disk Size: ${BL}$DISK_SIZE${CL}"
    echo -e "Storage: ${BL}$STORAGE${CL}"
    
    echo -e "\nPress Enter to continue or Ctrl+C to abort..."
    read
}

function download_debian_image() {
    msg_info "Downloading Debian 12 Cloud Image"
    pushd $TEMP_DIR >/dev/null
    
    local URL="https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-nocloud-$(dpkg --print-architecture).qcow2"
    local FILE=$(basename $URL)
    
    wget -q --show-progress "$URL" -O "$FILE"
    echo -en "\e[1A\e[0K"
    msg_ok "Downloaded ${FILE}"
    
    echo "$FILE"
}

function customize_image() {
    local FILE="$1"
    
    msg_info "Installing prerequisites on host"
    if ! command -v virt-customize &>/dev/null; then
        apt-get -qq update >/dev/null
        apt-get -qq install libguestfs-tools lsb-release -y >/dev/null
    fi
    msg_ok "Prerequisites installed"
    
    msg_info "Customizing Debian image with Docker, Portainer, and QEMU Guest Agent"
    
    # Install packages and Docker
    virt-customize -q -a "${FILE}" \
        --install qemu-guest-agent,apt-transport-https,ca-certificates,curl,gnupg,software-properties-common,lsb-release >/dev/null
    
    # Add Docker repository and install Docker
    virt-customize -q -a "${FILE}" \
        --run-command "mkdir -p /etc/apt/keyrings && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg" >/dev/null
    
    virt-customize -q -a "${FILE}" \
        --run-command "echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable' > /etc/apt/sources.list.d/docker.list" >/dev/null
    
    virt-customize -q -a "${FILE}" \
        --run-command "apt-get update -qq && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin" >/dev/null
    
    # Enable services and configure
    virt-customize -q -a "${FILE}" \
        --run-command "systemctl enable docker" >/dev/null
    
    virt-customize -q -a "${FILE}" \
        --run-command "systemctl enable qemu-guest-agent" >/dev/null
    
    # Set hostname
    virt-customize -q -a "${FILE}" \
        --hostname "${VM_NAME}" >/dev/null
    
    # Reset machine ID for template use
    virt-customize -q -a "${FILE}" \
        --run-command "echo -n > /etc/machine-id" >/dev/null
    
    # Create cloud-init script for Portainer auto-deployment
    cat > portainer_setup.sh << 'EOF'
#!/bin/bash
# Wait for Docker to be ready
sleep 30
while ! docker info >/dev/null 2>&1; do
    sleep 5
done

# Create Portainer volume
docker volume create portainer_data

# Deploy Portainer
docker run -d \
    -p 9443:9443 \
    -p 8000:8000 \
    --name=portainer \
    --restart=always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v portainer_data:/data \
    portainer/portainer-ce:latest

# Create a simple status check script
cat > /home/debian/docker_status.sh << 'DOCKEREOF'
#!/bin/bash
echo "=== Docker Status ==="
systemctl status docker --no-pager -l
echo -e "\n=== Docker Containers ==="
docker ps -a
echo -e "\n=== Portainer Access ==="
echo "Portainer Web UI: https://$(hostname -I | awk '{print $1}'):9443"
DOCKEREOF

chmod +x /home/debian/docker_status.sh
chown debian:debian /home/debian/docker_status.sh
EOF
    
    # Copy the script into the image
    virt-copy-in -a "${FILE}" portainer_setup.sh /usr/local/bin/
    virt-customize -q -a "${FILE}" \
        --run-command "chmod +x /usr/local/bin/portainer_setup.sh" >/dev/null
    
    # Create systemd service for Portainer auto-setup
    virt-customize -q -a "${FILE}" \
        --run-command "cat > /etc/systemd/system/portainer-setup.service << 'SERVICEEOF'
[Unit]
Description=Setup Portainer on first boot
After=docker.service
Wants=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/portainer_setup.sh
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
SERVICEEOF" >/dev/null
    
    virt-customize -q -a "${FILE}" \
        --run-command "systemctl enable portainer-setup.service" >/dev/null
    
    rm portainer_setup.sh
    msg_ok "Image customization completed"
}

function expand_image() {
    local FILE="$1"
    
    msg_info "Expanding image to ${DISK_SIZE}"
    qemu-img create -f qcow2 expanded.qcow2 ${DISK_SIZE} >/dev/null 2>&1
    virt-resize --expand /dev/sda1 ${FILE} expanded.qcow2 >/dev/null 2>&1
    mv expanded.qcow2 ${FILE} >/dev/null 2>&1
    msg_ok "Image expanded to ${DISK_SIZE}"
}

function create_vm() {
    local FILE="$1"
    
    msg_info "Creating Docker VM"
    
    # Create the VM
    qm create $VMID \
        -agent 1 \
        -tablet 0 \
        -localtime 1 \
        -bios ovmf \
        -cores $VM_CORES \
        -memory $VM_MEMORY \
        -name $VM_NAME \
        -net0 virtio,bridge=$BRIDGE,macaddr=$GEN_MAC \
        -onboot 1 \
        -ostype $OS_TYPE \
        -scsihw virtio-scsi-pci >/dev/null
    
    # Allocate EFI disk
    pvesm alloc $STORAGE $VMID vm-$VMID-disk-0 4M 1>&/dev/null
    
    # Import the main disk
    qm importdisk $VMID ${FILE} $STORAGE -format qcow2 1>&/dev/null
    
    # Configure the disks
    qm set $VMID \
        -efidisk0 ${STORAGE}:vm-$VMID-disk-0,efitype=4m \
        -scsi0 ${STORAGE}:vm-$VMID-disk-1,size=${DISK_SIZE} \
        -boot order=scsi0 \
        -serial0 socket >/dev/null
    
    # Ensure guest agent is enabled
    qm set $VMID --agent enabled=1 >/dev/null
    
    # Set description
    local DESCRIPTION=$(cat <<EOF
Docker VM with Portainer
========================

This VM includes:
- Debian 12 (Bookworm)  
- Docker CE with Docker Compose
- Portainer Community Edition
- QEMU Guest Agent

Access:
- SSH: ssh debian@VM_IP
- Portainer: https://VM_IP:9443

Run 'docker_status.sh' for system status.

Created by Proxmox Docker VM Complete Setup Script
EOF
)
    
    qm set "$VMID" -description "$DESCRIPTION" >/dev/null
    msg_ok "VM created successfully"
}

function start_vm() {
    msg_info "Starting Docker VM"
    qm start $VMID >/dev/null
    msg_ok "VM started"
    
    msg_info "Waiting for VM to boot and services to initialize..."
    sleep 45
    
    # Try to get VM IP
    local VM_IP=""
    for i in {1..12}; do
        VM_IP=$(qm guest cmd $VMID network-get-interfaces 2>/dev/null | grep -Eo '"ip-address": "([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"' | grep -v '127.0.0.1' | head -n1 | cut -d'"' -f4)
        if [ -n "$VM_IP" ]; then
            break
        fi
        sleep 10
    done
    
    if [ -n "$VM_IP" ]; then
        msg_ok "VM is ready at IP: ${BL}$VM_IP${CL}"
        echo -e "\n${INFO}${GN}Access Information:${CL}"
        echo -e "VM IP: ${BL}$VM_IP${CL}"
        echo -e "SSH: ${BL}ssh debian@$VM_IP${CL}"
        echo -e "Portainer: ${BL}https://$VM_IP:9443${CL}"
        echo -e "Docker status: ${BL}ssh debian@$VM_IP 'bash docker_status.sh'${CL}"
    else
        msg_ok "VM started (IP detection failed - check Proxmox UI)"
    fi
}

function main() {
    header_info
    check_root
    pve_check
    
    get_user_input
    
    local FILE=$(download_debian_image)
    customize_image "$FILE"
    expand_image "$FILE"
    create_vm "$FILE"
    start_vm
    
    popd >/dev/null
    
    echo -e "\n${CM}${GN}Docker VM setup completed successfully!${CL}"
    echo -e "${INFO}${YW}The VM will automatically deploy Portainer on first boot.${CL}"
    echo -e "${INFO}${YW}Wait a few minutes after VM starts for all services to be ready.${CL}\n"
}

# Run the main function
main "$@"
