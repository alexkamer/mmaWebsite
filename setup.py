#!/usr/bin/env python3
"""
MMA Website - Automated Setup Script
Handles dependency installation, configuration, and database setup
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")

def print_step(step, total, text):
    print(f"{BOLD}[{step}/{total}]{RESET} {text}")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET}  {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def run_command(cmd, description, capture_output=False):
    """Run a shell command with error handling"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        else:
            subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed: {description}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"  Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.12+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 12):
        print_error(f"Python 3.12+ required, but you have {version.major}.{version.minor}")
        print(f"  Please upgrade Python: https://www.python.org/downloads/")
        return False
    print_success(f"Python {version.major}.{version.minor} detected")
    return True

def check_uv_installed():
    """Check if uv is installed, offer to install if not"""
    if shutil.which('uv'):
        print_success("uv package manager found")
        return True

    print_warning("uv package manager not found")
    print("  uv is the recommended way to manage dependencies (faster than pip)")

    response = input(f"  Install uv? (Y/n): ").strip().lower()
    if response in ['', 'y', 'yes']:
        print("  Installing uv...")
        if sys.platform == 'win32':
            cmd = 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
        else:
            cmd = 'curl -LsSf https://astral.sh/uv/install.sh | sh'

        if run_command(cmd, "Installing uv"):
            print_success("uv installed successfully")
            return True
        else:
            print_warning("Failed to install uv, will use pip instead")
            return False
    else:
        print_warning("Skipping uv installation, will use pip")
        return False

def install_dependencies(use_uv):
    """Install project dependencies"""
    if use_uv:
        print("  Installing dependencies with uv...")
        return run_command("uv sync", "Installing dependencies")
    else:
        print("  Installing dependencies with pip...")
        # Ensure pip is available
        return run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing dependencies")

def create_env_file():
    """Create .env file from template"""
    env_file = Path('.env')
    env_example = Path('.env.example')

    if env_file.exists():
        print_success(".env file already exists")
        return True

    if not env_example.exists():
        print_warning(".env.example not found, creating basic .env")
        with open(env_file, 'w') as f:
            f.write("# Flask Configuration\n")
            f.write("FLASK_ENV=development\n")
            f.write("FLASK_DEBUG=1\n")
        print_success("Created .env with defaults")
        return True

    # Copy .env.example to .env
    shutil.copy(env_example, env_file)
    print_success("Created .env from template")
    print_warning("Note: Azure OpenAI keys are optional (only needed for /query feature)")
    return True

def create_database():
    """Set up the database"""
    db_path = Path('data/mma.db')

    if db_path.exists() and db_path.stat().st_size > 1000:
        print_success("Database already exists")
        return True

    print("\n  Choose database setup:")
    print(f"  {BOLD}1.{RESET} Seed database (2-3 minutes, ~100 fighters, recent events)")
    print(f"  {BOLD}2.{RESET} Full database (15-30 minutes, 17,000+ fighters, all data)")

    choice = input(f"\n  Enter choice (1 or 2) [{BOLD}1{RESET}]: ").strip() or "1"

    # Ensure data directory exists
    Path('data').mkdir(exist_ok=True)

    if choice == "1":
        print("\n  Setting up seed database (this will take 2-3 minutes)...")
        script = "scripts/create_seed_db.py"
        if Path(script).exists():
            cmd = f"uv run python {script}" if shutil.which('uv') else f"{sys.executable} {script}"
            return run_command(cmd, "Creating seed database")
        else:
            print_warning("Seed database script not found, using update_data.py")
            script = "scripts/update_data.py"
            cmd = f"uv run python {script}" if shutil.which('uv') else f"{sys.executable} {script}"
            return run_command(cmd, "Creating database")
    else:
        print("\n  Setting up full database (this will take 15-30 minutes)...")
        script = "scripts/update_data.py"
        cmd = f"uv run python {script}" if shutil.which('uv') else f"{sys.executable} {script}"
        return run_command(cmd, "Creating full database")

def verify_setup():
    """Verify the installation works"""
    db_path = Path('data/mma.db')
    if not db_path.exists():
        print_error("Database not found")
        return False

    if db_path.stat().st_size < 1000:
        print_error("Database appears to be empty")
        return False

    print_success("Setup verification passed")
    return True

def main():
    print_header("🥊 MMA Website - Automated Setup 🥊")

    print(f"{BOLD}This script will:{RESET}")
    print("  • Check Python version")
    print("  • Install dependencies")
    print("  • Configure environment")
    print("  • Set up database")
    print("  • Verify installation\n")

    total_steps = 5

    # Step 1: Check Python version
    print_step(1, total_steps, "Checking Python version...")
    if not check_python_version():
        sys.exit(1)

    # Step 2: Check/install uv
    print_step(2, total_steps, "Checking package manager...")
    use_uv = check_uv_installed()

    # Step 3: Install dependencies
    print_step(3, total_steps, "Installing dependencies...")
    if not install_dependencies(use_uv):
        print_error("Failed to install dependencies")
        sys.exit(1)
    print_success("Dependencies installed")

    # Step 4: Create .env file
    print_step(4, total_steps, "Configuring environment...")
    if not create_env_file():
        print_error("Failed to create .env file")
        sys.exit(1)

    # Step 5: Set up database
    print_step(5, total_steps, "Setting up database...")
    if not create_database():
        print_error("Failed to set up database")
        print("\n  You can set it up manually later with:")
        print(f"    {BOLD}uv run python scripts/update_data.py{RESET}")
        sys.exit(1)

    # Verify everything works
    print("\n" + "="*60)
    print(f"{BOLD}Verifying installation...{RESET}")
    if not verify_setup():
        sys.exit(1)

    # Success!
    print_header("✅ Setup Complete! ✅")
    print(f"{BOLD}To start the application:{RESET}")
    print(f"  {GREEN}uv run run.py{RESET}  (if using uv)")
    print(f"  {GREEN}python run.py{RESET}   (if using pip)")
    print(f"\n{BOLD}Then visit:{RESET} {BLUE}http://127.0.0.1:5000{RESET}")
    print(f"\n{BOLD}To update data later:{RESET}")
    print(f"  Daily:   {GREEN}uv run python scripts/incremental_update.py --days 30{RESET}")
    print(f"  Monthly: {GREEN}uv run python scripts/backfill_fighter_events.py --mode full{RESET}")
    print("\nEnjoy! 🥊\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Setup cancelled by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
