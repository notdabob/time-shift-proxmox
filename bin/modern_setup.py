#!/usr/bin/env python3
"""
Modern Setup Script for Time-Shift Proxmox
Demonstrates improved dependency management and installation process
"""

import os
import sys
import subprocess
import platform
import shutil
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging for setup process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/time-shift-setup.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SetupError(Exception):
    """Custom exception for setup-related errors"""
    pass


class DependencyManager:
    """Manages system and Python dependencies"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.package_managers = self._detect_package_managers()
        logger.info(f"Detected system: {self.system}")
        logger.info(f"Available package managers: {list(self.package_managers.keys())}")
    
    def _detect_package_managers(self) -> Dict[str, str]:
        """Detect available package managers"""
        managers = {}
        
        # Common package managers
        commands = {
            'apt': 'apt-get',
            'yum': 'yum',
            'dnf': 'dnf',
            'pacman': 'pacman',
            'brew': 'brew',
            'zypper': 'zypper'
        }
        
        for name, cmd in commands.items():
            if shutil.which(cmd):
                managers[name] = cmd
        
        return managers
    
    def _run_command(self, command: List[str], description: str, check: bool = True) -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            logger.info(f"Running: {description}")
            logger.debug(f"Command: {' '.join(command)}")
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=check,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description}")
                return True, result.stdout
            else:
                logger.error(f"❌ {description} failed")
                logger.error(f"Error: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {description} timed out")
            return False, "Command timed out"
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ {description} failed with exit code {e.returncode}")
            logger.error(f"Error: {e.stderr}")
            return False, e.stderr
        except Exception as e:
            logger.error(f"❌ Unexpected error during {description}: {e}")
            return False, str(e)
    
    def check_python_version(self) -> bool:
        """Check if Python version meets requirements"""
        version = sys.version_info
        required = (3, 8)
        
        if version >= required:
            logger.info(f"✅ Python {version.major}.{version.minor}.{version.micro} meets requirements")
            return True
        else:
            logger.error(f"❌ Python {version.major}.{version.minor} does not meet minimum requirement {required[0]}.{required[1]}")
            return False
    
    def install_system_dependencies(self) -> bool:
        """Install system-level dependencies"""
        dependencies = {
            'linux': {
                'apt': [
                    'python3-dev', 'python3-pip', 'python3-venv',
                    'jq', 'curl', 'wget', 'git',
                    'pandoc', 'texlive-latex-base',
                    'build-essential', 'libssl-dev', 'libffi-dev'
                ],
                'yum': [
                    'python3-devel', 'python3-pip',
                    'jq', 'curl', 'wget', 'git',
                    'pandoc', 'texlive-latex',
                    'gcc', 'openssl-devel', 'libffi-devel'
                ],
                'dnf': [
                    'python3-devel', 'python3-pip',
                    'jq', 'curl', 'wget', 'git',
                    'pandoc', 'texlive-latex',
                    'gcc', 'openssl-devel', 'libffi-devel'
                ]
            },
            'darwin': {
                'brew': [
                    'python@3.11', 'jq', 'pandoc',
                    'mactex-no-gui', 'openssl', 'libffi'
                ]
            }
        }
        
        system_deps = dependencies.get(self.system, {})
        
        for manager, cmd in self.package_managers.items():
            if manager in system_deps:
                packages = system_deps[manager]
                logger.info(f"Installing system dependencies using {manager}")
                
                # Update package database first
                if manager == 'apt':
                    success, _ = self._run_command(
                        ['sudo', cmd, 'update'], 
                        f"Updating {manager} package database"
                    )
                    if not success:
                        logger.warning(f"Failed to update {manager} database")
                
                # Install packages
                if manager == 'apt':
                    install_cmd = ['sudo', cmd, 'install', '-y'] + packages
                elif manager in ['yum', 'dnf']:
                    install_cmd = ['sudo', cmd, 'install', '-y'] + packages
                elif manager == 'brew':
                    install_cmd = [cmd, 'install'] + packages
                elif manager == 'pacman':
                    install_cmd = ['sudo', cmd, '-S', '--noconfirm'] + packages
                else:
                    continue
                
                success, output = self._run_command(
                    install_cmd,
                    f"Installing system dependencies with {manager}",
                    check=False
                )
                
                if success:
                    logger.info(f"✅ System dependencies installed successfully")
                    return True
                else:
                    logger.warning(f"Some packages may have failed to install")
        
        logger.warning("No suitable package manager found or installation failed")
        return False
    
    def setup_virtual_environment(self, project_dir: Path) -> bool:
        """Set up Python virtual environment"""
        venv_path = project_dir / '.venv'
        
        # Remove existing venv if present
        if venv_path.exists():
            logger.info("Removing existing virtual environment")
            shutil.rmtree(venv_path)
        
        # Create new virtual environment
        success, output = self._run_command(
            [sys.executable, '-m', 'venv', str(venv_path)],
            "Creating virtual environment"
        )
        
        if not success:
            logger.error("Failed to create virtual environment")
            return False
        
        # Activate venv and upgrade pip
        if self.system == 'windows':
            pip_path = venv_path / 'Scripts' / 'pip'
            python_path = venv_path / 'Scripts' / 'python'
        else:
            pip_path = venv_path / 'bin' / 'pip'
            python_path = venv_path / 'bin' / 'python'
        
        success, _ = self._run_command(
            [str(pip_path), 'install', '--upgrade', 'pip', 'setuptools', 'wheel'],
            "Upgrading pip and setuptools"
        )
        
        if success:
            logger.info(f"✅ Virtual environment created at {venv_path}")
            return True
        else:
            logger.error("Failed to upgrade pip in virtual environment")
            return False
    
    def install_python_dependencies(self, project_dir: Path, use_poetry: bool = False) -> bool:
        """Install Python dependencies using pip or poetry"""
        venv_path = project_dir / '.venv'
        
        if self.system == 'windows':
            pip_path = venv_path / 'Scripts' / 'pip'
            python_path = venv_path / 'Scripts' / 'python'
        else:
            pip_path = venv_path / 'bin' / 'pip'
            python_path = venv_path / 'bin' / 'python'
        
        if use_poetry and (project_dir / 'pyproject.toml').exists():
            # Check if poetry is installed
            if not shutil.which('poetry'):
                logger.info("Installing Poetry")
                success, _ = self._run_command(
                    [str(pip_path), 'install', 'poetry'],
                    "Installing Poetry"
                )
                if not success:
                    logger.warning("Failed to install Poetry, falling back to pip")
                    use_poetry = False
            
            if use_poetry:
                success, _ = self._run_command(
                    ['poetry', 'install'],
                    "Installing dependencies with Poetry",
                )
                
                if success:
                    logger.info("✅ Dependencies installed with Poetry")
                    return True
                else:
                    logger.warning("Poetry installation failed, falling back to pip")
        
        # Fallback to pip installation
        requirements_file = project_dir / 'requirements.txt'
        if requirements_file.exists():
            success, _ = self._run_command(
                [str(pip_path), 'install', '-r', str(requirements_file)],
                "Installing dependencies with pip"
            )
            
            if success:
                logger.info("✅ Dependencies installed with pip")
                return True
        
        logger.error("Failed to install Python dependencies")
        return False


class ProjectSetup:
    """Handles project-specific setup tasks"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.bin_dir = project_dir / 'bin'
        self.lib_dir = project_dir / 'lib'
        self.etc_dir = project_dir / 'etc'
        self.logs_dir = project_dir / 'var' / 'logs'
    
    def create_directories(self) -> bool:
        """Create necessary project directories"""
        directories = [
            self.logs_dir,
            self.project_dir / 'tests',
            self.project_dir / 'docs',
            self.project_dir / 'tmp'
        ]
        
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created directory: {directory}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            return False
    
    def make_scripts_executable(self) -> bool:
        """Make all scripts in bin/ executable"""
        if not self.bin_dir.exists():
            logger.warning(f"bin directory does not exist: {self.bin_dir}")
            return False
        
        success = True
        script_patterns = ['*.py', '*.sh']
        
        for pattern in script_patterns:
            for script in self.bin_dir.glob(pattern):
                try:
                    # Add execute permission
                    current_mode = script.stat().st_mode
                    script.chmod(current_mode | 0o755)
                    logger.info(f"✅ Made executable: {script.name}")
                except Exception as e:
                    logger.error(f"❌ Failed to make {script.name} executable: {e}")
                    success = False
        
        return success
    
    def setup_configuration(self) -> bool:
        """Set up initial configuration files"""
        try:
            # Import here to avoid circular imports during setup
            sys.path.insert(0, str(self.lib_dir))
            from config_models import create_default_config, save_config_to_file
            
            config_file = self.etc_dir / 'time-shift-config.json'
            
            if not config_file.exists():
                logger.info("Creating default configuration")
                default_config = create_default_config()
                save_config_to_file(default_config, str(config_file))
                logger.info(f"✅ Created default configuration: {config_file}")
            else:
                logger.info(f"Configuration file already exists: {config_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup configuration: {e}")
            return False
    
    def create_desktop_entry(self) -> bool:
        """Create desktop entry for the application"""
        try:
            desktop_dir = Path.home() / '.local' / 'share' / 'applications'
            desktop_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = desktop_dir / 'time-shift-proxmox.desktop'
            
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Time-Shift Proxmox
Comment=Temporal SSL certificate access for Proxmox VMs
Exec={self.bin_dir / 'time-shift-cli.py'}
Icon=utilities-terminal
Terminal=true
Categories=System;Network;
Keywords=proxmox;ssl;certificate;time;idrac;
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            desktop_file.chmod(0o755)
            logger.info(f"✅ Created desktop entry: {desktop_file}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to create desktop entry: {e}")
            return False
    
    def setup_systemd_service(self) -> bool:
        """Create systemd service for background operations"""
        try:
            service_content = f"""[Unit]
Description=Time-Shift Proxmox Background Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.project_dir}
ExecStart={self.project_dir}/.venv/bin/python {self.bin_dir}/time-shift-daemon.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
            
            service_file = Path('/tmp/time-shift-proxmox.service')
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            logger.info(f"✅ Created systemd service template: {service_file}")
            logger.info("To install the service, run:")
            logger.info(f"  sudo cp {service_file} /etc/systemd/system/")
            logger.info("  sudo systemctl daemon-reload")
            logger.info("  sudo systemctl enable time-shift-proxmox")
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to create systemd service: {e}")
            return False


class ModernSetup:
    """Main setup orchestrator"""
    
    def __init__(self, project_dir: Optional[Path] = None):
        if project_dir is None:
            self.project_dir = Path(__file__).parent.parent.absolute()
        else:
            self.project_dir = project_dir
        
        self.dependency_manager = DependencyManager()
        self.project_setup = ProjectSetup(self.project_dir)
        
    def print_banner(self):
        """Print setup banner"""
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    Time-Shift Proxmox Setup                 ║
║              Modern Installation & Configuration             ║
╚══════════════════════════════════════════════════════════════╝
{Colors.ENDC}

{Colors.OKCYAN}Project Directory: {self.project_dir}{Colors.ENDC}
{Colors.OKCYAN}Python Version: {sys.version}{Colors.ENDC}
{Colors.OKCYAN}Platform: {platform.platform()}{Colors.ENDC}
"""
        print(banner)
    
    def run_setup(self, interactive: bool = True, use_poetry: bool = False) -> bool:
        """Run the complete setup process"""
        self.print_banner()
        
        steps = [
            ("Checking Python version", self.dependency_manager.check_python_version),
            ("Installing system dependencies", self.dependency_manager.install_system_dependencies),
            ("Creating project directories", self.project_setup.create_directories),
            ("Setting up virtual environment", lambda: self.dependency_manager.setup_virtual_environment(self.project_dir)),
            ("Installing Python dependencies", lambda: self.dependency_manager.install_python_dependencies(self.project_dir, use_poetry)),
            ("Making scripts executable", self.project_setup.make_scripts_executable),
            ("Setting up configuration", self.project_setup.setup_configuration),
            ("Creating desktop entry", self.project_setup.create_desktop_entry),
            ("Setting up systemd service", self.project_setup.setup_systemd_service),
        ]
        
        failed_steps = []
        
        for step_name, step_function in steps:
            print(f"\n{Colors.OKBLUE}▶ {step_name}...{Colors.ENDC}")
            
            if interactive:
                response = input(f"Proceed with '{step_name}'? [Y/n]: ").strip().lower()
                if response in ['n', 'no']:
                    print(f"{Colors.WARNING}⚠ Skipped: {step_name}{Colors.ENDC}")
                    continue
            
            try:
                success = step_function()
                if success:
                    print(f"{Colors.OKGREEN}✅ {step_name} completed successfully{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ {step_name} failed{Colors.ENDC}")
                    failed_steps.append(step_name)
            except Exception as e:
                print(f"{Colors.FAIL}❌ {step_name} failed with error: {e}{Colors.ENDC}")
                failed_steps.append(step_name)
                logger.exception(f"Error in {step_name}")
        
        # Summary
        print(f"\n{Colors.HEADER}{Colors.BOLD}Setup Summary{Colors.ENDC}")
        print("=" * 50)
        
        if not failed_steps:
            print(f"{Colors.OKGREEN}✅ All setup steps completed successfully!{Colors.ENDC}")
            self.print_next_steps()
            return True
        else:
            print(f"{Colors.FAIL}❌ The following steps failed:{Colors.ENDC}")
            for step in failed_steps:
                print(f"  • {step}")
            print(f"\n{Colors.WARNING}Check the log file for details: /tmp/time-shift-setup.log{Colors.ENDC}")
            return False
    
    def print_next_steps(self):
        """Print next steps for the user"""
        next_steps = f"""
{Colors.OKCYAN}{Colors.BOLD}Next Steps:{Colors.ENDC}

{Colors.OKGREEN}1. Activate the virtual environment:{Colors.ENDC}
   source {self.project_dir}/.venv/bin/activate

{Colors.OKGREEN}2. Run the configuration wizard:{Colors.ENDC}
   ./bin/vm-config-wizard.py

{Colors.OKGREEN}3. Test the installation:{Colors.ENDC}
   ./bin/time-shift-cli.py --help

{Colors.OKGREEN}4. Validate your setup:{Colors.ENDC}
   ./bin/time-shift-cli.py --action validate --idrac-ip <your-idrac-ip>

{Colors.OKGREEN}5. Review security settings:{Colors.ENDC}
   Edit {self.project_dir}/etc/time-shift-config.json

{Colors.OKCYAN}For more information, see:{Colors.ENDC}
  • README.md
  • CODEBASE_ANALYSIS.md
  • Setup log: /tmp/time-shift-setup.log
"""
        print(next_steps)


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Modern setup script for Time-Shift Proxmox",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--non-interactive', '-y',
        action='store_true',
        help='Run setup without interactive prompts'
    )
    parser.add_argument(
        '--use-poetry',
        action='store_true',
        help='Use Poetry for dependency management'
    )
    parser.add_argument(
        '--project-dir',
        type=Path,
        default=None,
        help='Project directory (default: auto-detect)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if running as root (required for some operations)
    if os.geteuid() == 0:
        logger.warning("Running as root. This is required for system dependency installation.")
    
    try:
        setup = ModernSetup(args.project_dir)
        success = setup.run_setup(
            interactive=not args.non_interactive,
            use_poetry=args.use_poetry
        )
        
        if success:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 Setup completed successfully!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}❌ Setup completed with errors{Colors.ENDC}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Setup interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error during setup")
        print(f"\n{Colors.FAIL}❌ Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    main()