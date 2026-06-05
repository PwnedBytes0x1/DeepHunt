#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# DeepHunt Termux Bootstrap Script
# Auto-executed on first run or manual setup
# Compatible with Android 14+ / Termux (F-Droid)
#===============================================================================

# Don't exit on error - handle errors gracefully
set +e

TERMUX_PREFIX="/data/data/com.termux/files/usr"
HOME_DIR="$HOME"
WORKSPACE_DIR="${HOME_DIR}/deephunt"
REPO_URL="https://github.com/PwnedBytes0x1/deephunt.git"

# Ensure pip scripts are in PATH
export PATH="$HOME/.local/bin:$PREFIX/bin:$PATH"

# Colors (with fallback for terminals that don't support colors)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    CYAN=''
    NC=''
fi

print_banner() {
    echo ""
    echo -e "${CYAN}"
    echo "    DeepHunt v1.0 - Termux Bootstrap"
    echo -e "${NC}"
    echo "    ================================"
    echo ""
}

print_status() {
    echo -e "${CYAN}[DeepHunt]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[DeepHunt]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[DeepHunt]${NC} $1"
}

print_error() {
    echo -e "${RED}[DeepHunt]${NC} $1"
}

#===============================================================================
# Pre-flight Checks
#===============================================================================

check_termux() {
    if [ ! -d "$TERMUX_PREFIX" ]; then
        print_error "This script is designed for Termux only."
        exit 1
    fi

    print_success "Termux environment detected"
}

check_storage() {
    local available
    # Get available space in KB and convert to GB
    available=$(df -k "$HOME" 2>/dev/null | tail -1 | awk '{print $4}')
    
    if [ -z "$available" ]; then
        print_warning "Could not determine storage. Proceeding anyway..."
        return 0
    fi
    
    local available_gb=$((available / 1024 / 1024))

    if [ "$available_gb" -lt 2 ]; then
        print_error "Insufficient storage. Need at least 2GB free."
        print_error "Available: ${available_gb}GB"
        return 1
    fi

    print_success "Storage check passed (${available_gb}GB free)"
}

#===============================================================================
# Installation Steps
#===============================================================================

step_update_pkg() {
    print_status "Step 1/7: Updating package database..."
    if ! pkg update -y >/dev/null 2>&1; then
        print_warning "Package update failed - network may be unavailable"
        print_warning "Continuing with existing package versions..."
    fi
    print_success "Package database updated"
}

step_install_core() {
    print_status "Step 2/7: Installing core dependencies..."
    
    # Install core packages silently, track failures
    local packages="git curl wget jq python python-pip termux-api"
    local failed=""
    
    for pkg_name in $packages; do
        if ! pkg install -y "$pkg_name" >/dev/null 2>&1; then
            failed="$failed $pkg_name"
        fi
    done
    
    # Install additional packages silently
    pkg install -y clang make cmake pkg-config >/dev/null 2>&1 || true
    pkg install -y libffi libxml2 libxslt >/dev/null 2>&1 || true
    pkg install -y libpng libjpeg-turbo freetype zlib >/dev/null 2>&1 || true
    
    if [ -n "$failed" ]; then
        print_warning "Some packages failed to install:$failed"
        print_warning "You may need to install them manually: pkg install <package>"
    fi
    print_success "Core dependencies installed"
}

step_install_python() {
    print_status "Step 3/7: Installing Python libraries..."

    # Upgrade pip silently
    if ! python -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1; then
        print_warning "Failed to upgrade pip - may affect some installations"
    fi

    # Install core dependencies silently
    if ! python -m pip install click rich aiohttp aiofiles beautifulsoup4 lxml html2text requests urllib3 pydantic pyyaml python-dotenv ujson schedule cryptography prompt-toolkit >/dev/null 2>&1; then
        print_warning "Some core Python packages failed to install"
        print_warning "Core functionality may be limited - run: pip install <package>"
    fi
    
    # Install httpx silently
    python -m pip install "httpx[http2]" >/dev/null 2>&1 || python -m pip install httpx >/dev/null 2>&1 || true
    
    # Install optional packages silently
    python -m pip install python-telegram-bot >/dev/null 2>&1 || print_warning "Telegram notifications disabled (python-telegram-bot failed)"
    python -m pip install psutil >/dev/null 2>&1 || print_warning "System monitoring limited (psutil failed)"

    print_success "Python libraries installed"
}

step_install_go_tools() {
    print_status "Step 4/7: Installing Go-based tools..."

    if ! command -v go >/dev/null 2>&1; then
        print_warning "Go not installed - native security tools will be skipped"
        print_warning "For full functionality: pkg install golang"
        print_warning "Then re-run this script to install: go install ..."
        return 0
    fi
    
    print_status "Go detected, installing security tools..."
    export GOPATH="$HOME/go"
    export PATH="$PATH:$GOPATH/bin"

    # Install Go tools silently
    go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest >/dev/null 2>&1 || true
    go install github.com/projectdiscovery/katana/cmd/katana@latest >/dev/null 2>&1 || true
    go install github.com/projectdiscovery/httpx/cmd/httpx@latest >/dev/null 2>&1 || true
    go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest >/dev/null 2>&1 || true
    go install github.com/projectdiscovery/notify/cmd/notify@latest >/dev/null 2>&1 || true
    go install github.com/lc/gau/v2/cmd/gau@latest >/dev/null 2>&1 || true
    go install github.com/ffuf/ffuf@latest >/dev/null 2>&1 || true

    print_success "Go tools installed"
}

step_install_python_tools() {
    print_status "Step 5/7: Installing Python-based tools..."

    # Install Python-based tools silently
    if ! python -m pip install dirsearch arjun wafw00f >/dev/null 2>&1; then
        print_warning "Some Python security tools failed to install"
        print_warning "You can install manually: pip install dirsearch arjun wafw00f"
    fi

    print_success "Python tools installed"
}

step_permissions() {
    print_status "Step 6/7: Configuring Android permissions..."

    # Skip permission requests in non-interactive mode or if not in Termux
    if [ -z "$TERMUX_VERSION" ]; then
        print_warning "Not running in Termux - skipping Android permissions"
        print_warning "On desktop Linux/macOS, no special permissions needed"
        print_success "Permissions step skipped (non-Termux environment)"
        return 0
    fi

    # Check if termux-notification is available
    if ! command -v termux-notification >/dev/null 2>&1; then
        print_warning "Termux:API app not installed"
        print_warning "DeepHunt will run without notification support"
        print_warning "To enable: pkg install termux-api, then grant notification permission"
        print_success "Permissions setup skipped (Termux:API not available)"
        return 0
    fi

    # Test notification permission (with timeout to prevent hanging)
    print_status "Testing notification permission..."
    if timeout 5 termux-notification --title "DeepHunt" --content "API test" >/dev/null 2>&1; then
        print_success "Notifications enabled - you'll receive hunt approvals via notifications"
    else
        print_warning "Notifications require permission setup"
        print_warning "To enable: Open Termux app > Settings > Permissions > Allow notifications"
        print_warning "DeepHunt will still work but you'll need to check manually for approvals"
    fi

    # Battery optimization info
    print_status "Battery optimization (optional but recommended):"
    print_status "  Settings > Apps > Termux > Battery > Unrestricted"
    print_status "  This prevents Termux from being killed during long hunts"

    print_success "Permissions configuration complete"
}

step_setup_workspace() {
    print_status "Step 7/7: Setting up DeepHunt workspace..."

    # Ensure pip bin directory is in PATH
    export PATH="$HOME/.local/bin:$PREFIX/bin:$PATH"

    # Clone or update repository silently
    if [ -d "$WORKSPACE_DIR/.git" ]; then
        print_status "Updating existing DeepHunt installation..."
        cd "$WORKSPACE_DIR"
        if ! git pull origin main >/dev/null 2>&1; then
            print_warning "Failed to update - check your internet connection"
            print_warning "Continuing with existing installation..."
        fi
    else
        print_status "Downloading DeepHunt repository..."
        if ! git clone "$REPO_URL" "$WORKSPACE_DIR" >/dev/null 2>&1; then
            print_warning "Failed to clone repository - check your internet connection"
            print_warning "Creating empty workspace directory..."
            mkdir -p "$WORKSPACE_DIR"
        fi
    fi

    # Install DeepHunt in development mode
    if [ -d "$WORKSPACE_DIR" ]; then
        print_status "Installing DeepHunt package..."
        cd "$WORKSPACE_DIR"
        
        # Run pip install and capture output
        pip_output=$(python -m pip install -e . 2>&1)
        
        # Check if installation actually succeeded
        if echo "$pip_output" | grep -qE "(Successfully installed|Requirement already satisfied)"; then
            print_success "DeepHunt package installed successfully"
        elif python -c "import deephunt" 2>/dev/null; then
            print_success "DeepHunt package installed"
        else
            print_warning "Package installation may have failed"
            print_warning "Try manually: cd ~/deephunt && pip install -e ."
        fi
    fi

    # Initialize workspace
    print_status "Initializing DeepHunt configuration..."
    if python -m deephunt.cli init >/dev/null 2>&1; then
        print_success "DeepHunt configuration initialized"
    else
        print_warning "Configuration initialization failed"
        print_warning "You can run 'dhunt init' later to configure"
    fi

    # Create symlinks for dhunt command in PATH
    print_status "Setting up dhunt command..."
    
    # Try multiple locations for the dhunt script
    local script_sources="$HOME/.local/bin/dhunt $HOME/.local/bin/deephunt"
    local linked=false
    
    for script in $script_sources; do
        if [ -f "$script" ]; then
            local cmd_name=$(basename "$script")
            # Create symlink in PREFIX/bin if not already there
            if [ ! -f "$PREFIX/bin/$cmd_name" ]; then
                ln -sf "$script" "$PREFIX/bin/$cmd_name" 2>/dev/null && {
                    print_success "Linked $cmd_name to $PREFIX/bin"
                    linked=true
                }
            fi
        fi
    done
    
    # If symlink creation failed, ensure PATH includes local bin
    if [ "$linked" = false ]; then
        export PATH="$HOME/.local/bin:$PREFIX/bin:$PATH"
        
        # Add to bashrc for persistence if not already there
        if ! grep -q "\.local/bin" ~/.bashrc 2>/dev/null; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        fi
        
        if command -v dhunt >/dev/null 2>&1; then
            print_success "dhunt command available in PATH"
        else
            print_warning "dhunt command not found in PATH"
            print_warning "Added ~/.local/bin to PATH. Run: source ~/.bashrc"
        fi
    fi

    print_success "Workspace setup complete"
}

#===============================================================================
# Main
#===============================================================================

main() {
    print_banner

    print_status "Starting DeepHunt bootstrap..."
    print_status "Platform: Android $(getprop ro.build.version.release 2>/dev/null || echo 'Unknown')"
    print_status "Termux: ${TERMUX_VERSION:-Unknown}"
    echo ""

    # Run checks (non-fatal)
    check_termux 2>/dev/null || true
    check_storage 2>/dev/null || true

    # Run installation steps (non-fatal)
    step_update_pkg 2>/dev/null || true
    step_install_core 2>/dev/null || true
    step_install_python 2>/dev/null || true
    step_install_go_tools 2>/dev/null || true
    step_install_python_tools 2>/dev/null || true
    step_permissions 2>/dev/null || true
    step_setup_workspace 2>/dev/null || true

    # Post-installation
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  DeepHunt Bootstrap Complete!          ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    print_status "Workspace: $WORKSPACE_DIR"
    print_status "Binary: dhunt"
    echo ""
    echo "  Quick start:"
    echo "    dhunt --help"
    echo "    dhunt init"
    echo "    dhunt hunt example.com"
    echo ""
    echo "  Set API keys:"
    echo "    dhunt config set-apikey deepseek YOUR_API_KEY"
    echo ""
}

# Handle interrupts
trap 'print_error "Bootstrap interrupted"; exit 1' INT TERM

# Run main
main "$@"
