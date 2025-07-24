#!/bin/bash
# Time Shift Proxmox - One-Click Setup Script
# Holistic integration and deployment automation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON_MIN_VERSION="3.8"
LOG_FILE="${SCRIPT_DIR}/setup.log"

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

print_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     ████████╗██╗███╗   ███╗███████╗    ███████╗██╗  ██╗██╗██╗ ████████╗║
║     ╚══██╔══╝██║████╗ ████║██╔════╝    ██╔════╝██║  ██║██║██║ ╚══██╔══╝║
║        ██║   ██║██╔████╔██║█████╗      ███████╗███████║██║█████╗  ██║   ║
║        ██║   ██║██║╚██╔╝██║██╔══╝      ╚════██║██╔══██║██║██╔══╝  ██║   ║
║        ██║   ██║██║ ╚═╝ ██║███████╗    ███████║██║  ██║██║██║     ██║   ║
║        ╚═╝   ╚═╝╚═╝     ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝   ║
║                                                                ║
║                  One-Click Integration Master                  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Check functions
check_python() {
    log "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$PYTHON_MIN_VERSION" ]; then
            echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
            return 0
        else
            echo -e "${RED}✗${NC} Python $PYTHON_VERSION found, but $PYTHON_MIN_VERSION or higher required"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Python not found"
        return 1
    fi
}

check_docker() {
    log "Checking Docker installation..."
    
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,$//')
            echo -e "${GREEN}✓${NC} Docker $DOCKER_VERSION found and running"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} Docker found but daemon not running"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} Docker not found (optional)"
        return 1
    fi
}

check_git() {
    log "Checking Git installation..."
    
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | awk '{print $3}')
        echo -e "${GREEN}✓${NC} Git $GIT_VERSION found"
        return 0
    else
        echo -e "${RED}✗${NC} Git not found"
        return 1
    fi
}

install_dependencies() {
    log "Installing Python dependencies..."
    
    # Check for pip
    if ! python3 -m pip --version &> /dev/null; then
        echo -e "${YELLOW}⚠${NC} pip not found, installing..."
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python3 get-pip.py
        rm get-pip.py
    fi
    
    # Install Poetry if not present
    if ! command -v poetry &> /dev/null; then
        echo -e "${BLUE}→${NC} Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Install dependencies
    echo -e "${BLUE}→${NC} Installing project dependencies..."
    
    if [ -f "pyproject.toml" ]; then
        poetry install --no-interaction --verbose
    elif [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
    else
        echo -e "${YELLOW}⚠${NC} No dependency file found, installing core requirements..."
        python3 -m pip install click rich pyyaml jinja2 requests aiohttp pydantic
    fi
    
    echo -e "${GREEN}✓${NC} Dependencies installed"
}

setup_configuration() {
    log "Setting up configuration..."
    
    # Create directory structure
    mkdir -p etc integrations plugins hooks templates logs .integration_cache
    
    # Check if configuration exists
    if [ ! -f "etc/time-shift-config.json" ]; then
        echo -e "${BLUE}→${NC} No configuration found. Running setup wizard..."
        python3 master.py wizard
    else
        echo -e "${GREEN}✓${NC} Configuration found"
    fi
}

initialize_integrations() {
    log "Initializing integration framework..."
    
    # Initialize integration system
    python3 integrate.py init
    
    # Discover available integrations
    echo -e "${BLUE}→${NC} Discovering integrations..."
    python3 integrate.py list
}

run_health_checks() {
    log "Running system health checks..."
    
    python3 master.py health --full
}

quick_start_menu() {
    echo -e "\n${PURPLE}Quick Start Options:${NC}"
    echo "1) Deploy Time-Shift VM to Proxmox"
    echo "2) Setup Docker containers"
    echo "3) Run integration wizard"
    echo "4) Configure templates"
    echo "5) Run security scan"
    echo "6) View system status"
    echo "7) Exit"
    
    read -p "Select an option (1-7): " choice
    
    case $choice in
        1)
            echo -e "${BLUE}→${NC} Starting Proxmox VM deployment..."
            python3 master.py vm deploy
            ;;
        2)
            echo -e "${BLUE}→${NC} Setting up Docker containers..."
            python3 master.py docker up --build
            ;;
        3)
            echo -e "${BLUE}→${NC} Running integration wizard..."
            python3 integrate.py wizard
            ;;
        4)
            echo -e "${BLUE}→${NC} Configuring templates..."
            python3 scripts/template-manager.py
            ;;
        5)
            echo -e "${BLUE}→${NC} Running security scan..."
            python3 master.py security --level full
            ;;
        6)
            echo -e "${BLUE}→${NC} System status..."
            python3 master.py status
            ;;
        7)
            echo -e "${GREEN}✓${NC} Setup complete!"
            exit 0
            ;;
        *)
            echo -e "${RED}✗${NC} Invalid option"
            quick_start_menu
            ;;
    esac
}

# Main setup flow
main() {
    print_banner
    
    echo -e "${BLUE}Starting one-click setup...${NC}\n"
    
    # Create log file
    touch "$LOG_FILE"
    log "Starting Time Shift Proxmox setup"
    
    # System checks
    echo -e "${PURPLE}=== System Requirements ===${NC}"
    
    PYTHON_OK=false
    DOCKER_OK=false
    GIT_OK=false
    
    check_python && PYTHON_OK=true
    check_docker && DOCKER_OK=true
    check_git && GIT_OK=true
    
    if [ "$PYTHON_OK" = false ]; then
        echo -e "\n${RED}✗ Python $PYTHON_MIN_VERSION+ is required${NC}"
        echo "Please install Python from https://www.python.org/"
        exit 1
    fi
    
    # Install dependencies
    echo -e "\n${PURPLE}=== Installing Dependencies ===${NC}"
    install_dependencies
    
    # Setup configuration
    echo -e "\n${PURPLE}=== Configuration ===${NC}"
    setup_configuration
    
    # Initialize integrations
    echo -e "\n${PURPLE}=== Integration Framework ===${NC}"
    initialize_integrations
    
    # Run health checks
    echo -e "\n${PURPLE}=== Health Checks ===${NC}"
    run_health_checks
    
    # Success message
    echo -e "\n${GREEN}✨ Setup completed successfully!${NC}\n"
    
    # Show available commands
    echo -e "${PURPLE}Available Commands:${NC}"
    echo -e "  ${CYAN}./master.py${NC}      - Main CLI interface"
    echo -e "  ${CYAN}./integrate.py${NC}   - Integration management"
    echo -e "  ${CYAN}./one-click-setup.sh${NC} - This setup script"
    
    echo -e "\n${PURPLE}Quick Start:${NC}"
    echo -e "  ${CYAN}./master.py wizard${NC}     - Interactive setup wizard"
    echo -e "  ${CYAN}./master.py vm deploy${NC}  - Deploy VM to Proxmox"
    echo -e "  ${CYAN}./master.py health${NC}     - Check system health"
    echo -e "  ${CYAN}./integrate.py list${NC}    - List integrations"
    
    # Interactive menu
    echo
    read -p "Would you like to open the quick start menu? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        quick_start_menu
    fi
    
    log "Setup completed"
}

# Trap errors
trap 'echo -e "\n${RED}✗ Setup failed. Check $LOG_FILE for details.${NC}"; exit 1' ERR

# Run main function
main "$@"