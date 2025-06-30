#!/usr/bin/env python3

import os
import subprocess
import sys
import platform

# --- Helper for colored output ---
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_success(message):
    print(f"{bcolors.OKGREEN}{message}{bcolors.ENDC}")

def print_error(message):
    print(f"{bcolors.FAIL}{message}{bcolors.ENDC}")

def print_warning(message):
    print(f"{bcolors.WARNING}{message}{bcolors.ENDC}")

def print_info(message):
    print(f"{bcolors.OKCYAN}{message}{bcolors.ENDC}")

def print_header(message):
    print(f"{bcolors.HEADER}{bcolors.BOLD}{message}{bcolors.ENDC}")

def run_command(command, description, check=True):
    print_info(f"Running: {description}...")
    try:
        subprocess.run(command, check=check, shell=True, capture_output=True, text=True)
        print_success(f"Successfully {description.lower()}.")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error {description.lower()}: {e}")
        print_error(f"Stdout: {e.stdout}")
        print_error(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print_error(f"Error: Command not found. Please ensure '{command.split()[0]}' is in your PATH.")
        return False

def check_and_install_system_dependency(command_name, install_cmd_mac, install_cmd_linux, package_display_name):
    print_info(f"Checking for {package_display_name}...")
    if run_command(f"command -v {command_name}", f"checking for {command_name}", check=False):
        print_success(f"{package_display_name} is already installed.")
        return True
    else:
        print_warning(f"{package_display_name} not found. Attempting to install...")
        system = platform.system()
        if system == "Darwin": # macOS
            if run_command(install_cmd_mac, f"installing {package_display_name} on macOS"):
                return True
        elif system == "Linux": # Linux (assuming Debian/Ubuntu for apt)
            if run_command(install_cmd_linux, f"installing {package_display_name} on Linux"):
                return True
        else:
            print_error(f"Unsupported operating system: {system}. Please install {package_display_name} manually.")
        return False

def install_python_dependencies():
    print_header("Installing Python Dependencies...")
    if not check_and_install_system_dependency("python3", "brew install python", "sudo apt-get update && sudo apt-get install -y python3", "Python 3"):
        print_error("Python 3 is required but could not be installed. Please install it manually.")
        sys.exit(1)

    if not check_and_install_system_dependency("pip3", "brew install python", "sudo apt-get install -y python3-pip", "pip3"):
        print_warning("pip3 not found. Attempting to use python3 -m pip.")
        pip_command = "python3 -m pip"
    else:
        pip_command = "pip3"

    requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'requirements.txt')
    if not os.path.exists(requirements_file):
        print_error(f"Error: requirements.txt not found at {requirements_file}")
        sys.exit(1)

    if run_command(f"{pip_command} install -r {requirements_file}", "installing Python packages"):
        print_success("Python dependencies installed successfully.")
        return True
    else:
        print_error("Failed to install Python dependencies. Please check the errors above.")
        return False

def make_scripts_executable():
    print_header("Making scripts executable...")
    bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    success = True
    for filename in os.listdir(bin_dir):
        if filename.endswith(".py") or filename.endswith(".sh"):
            script_path = os.path.join(bin_dir, filename)
            if not run_command(f"chmod +x {script_path}", f"making {filename} executable"):
                success = False
    if success:
        print_success("All scripts in bin/ are now executable.")
    else:
        print_error("Some scripts could not be made executable.")
    return success

def main():
    print_header("Starting Time-Shift Proxmox Project Setup...")

    # Check and install system dependencies
    if not check_and_install_system_dependency("jq", "brew install jq", "sudo apt-get install -y jq", "jq"):
        print_error("jq is required for configuration parsing but could not be installed.")
        sys.exit(1)
    
    if not check_and_install_system_dependency("pandoc", "brew install pandoc", "sudo apt-get install -y pandoc", "pandoc"):
        print_error("pandoc is required for PDF generation but could not be installed.")
        sys.exit(1)

    # pdflatex is part of a LaTeX distribution
    if not check_and_install_system_dependency("pdflatex", "brew install --cask mactex-no-gui", "sudo apt-get install -y texlive-latex-base", "LaTeX (pdflatex)"):
        print_warning("LaTeX (pdflatex) is recommended for PDF generation but could not be installed. PDF generation might fail.")
    
    # Install Python dependencies
    if not install_python_dependencies():
        sys.exit(1)

    # Make scripts executable
    if not make_scripts_executable():
        sys.exit(1)

    print_success("\nTime-Shift Proxmox Project Setup Complete!")
    print_info("You can now run the configuration wizard: ./bin/vm-config-wizard.py")
    print_info("Or the main CLI: ./bin/time-shift-cli.py")

if __name__ == "__main__":
    main()
