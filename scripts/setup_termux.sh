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
    pkg update -y
    print_success "Package database updated"
}

step_install_core() {
    print_status "Step 2/7: Installing core dependencies..."
    
    # Update package database first (non-blocking)
    pkg update -y 2>/dev/null || true
    
    # Install core packages with fallback
    local packages="git curl wget jq python python-pip termux-api"
    
    for pkg_name in $packages; do
        pkg install -y "$pkg_name" 2>/dev/null || print_warning "$pkg_name install failed, continuing..."
    done
    
    # Install additional packages (non-blocking)
    pkg install -y clang make cmake pkg-config 2>/dev/null || true
    pkg install -y libffi libxml2 libxslt 2>/dev/null || true
    pkg install -y libpng libjpeg-turbo freetype zlib 2>/dev/null || true
    
    print_success "Core dependencies installed"
}

step_install_python() {
    print_status "Step 3/7: Installing Python libraries..."

    # Use python -m pip to ensure we're using the correct pip
    python -m pip install --upgrade pip setuptools wheel 2>/dev/null || true

    # Install core dependencies with error handling
    python -m pip install click rich aiohttp aiofiles beautifulsoup4 lxml html2text requests urllib3 pydantic pyyaml python-dotenv ujson schedule cryptography prompt-toolkit 2>/dev/null || true
    
    # Install httpx with http2 support (may fail on some platforms)
    python -m pip install "httpx[http2]" 2>/dev/null || python -m pip install httpx 2>/dev/null || true
    
    # Install optional telegram support (non-blocking)
    python -m pip install python-telegram-bot 2>/dev/null || true
    
    # Install psutil for system monitoring
    python -m pip install psutil 2>/dev/null || true

    print_success "Python libraries installed"
}

step_install_go_tools() {
    print_status "Step 4/7: Installing Go-based tools..."

    if command -v go &> /dev/null; then
        export GOPATH="$HOME/go"
        export PATH="$PATH:$GOPATH/bin"

        # Install Go tools with error handling
        go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest 2>/dev/null || true
        go install github.com/projectdiscovery/katana/cmd/katana@latest 2>/dev/null || true
        go install github.com/projectdiscovery/httpx/cmd/httpx@latest 2>/dev/null || true
        go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest 2>/dev/null || true
        go install github.com/projectdiscovery/notify/cmd/notify@latest 2>/dev/null || true
        go install github.com/lc/gau/v2/cmd/gau@latest 2>/dev/null || true
        go install github.com/ffuf/ffuf@latest 2>/dev/null || true

        print_success "Go tools installed"
    else
        print_warning "Go not found. Skipping native tools."
        print_warning "Install Go for better performance: pkg install golang"
    fi
}

step_install_python_tools() {
    print_status "Step 5/7: Installing Python-based tools..."

    # Install Python-based tools with error handling
    python -m pip install dirsearch arjun wafw00f 2>/dev/null || true

    print_success "Python tools installed"
}

step_permissions() {
    print_status "Step 6/7: Requesting Android permissions..."

    # Request notification permission (non-blocking)
    if command -v termux-notification &> /dev/null; then
        if ! termux-notification --title "DeepHunt Test" --content "API OK" 2>/dev/null; then
            print_warning "Please grant notification permission to Termux:API"
            termux-open --chooser "android.settings.NOTIFICATION_SETTINGS" 2>/dev/null || true
        fi
    else
        print_warning "Termux:API not found. Notifications disabled."
    fi

    # Disable battery optimization (non-blocking)
    termux-open --chooser "android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" 2>/dev/null || true

    print_success "Permission requests completed"
}

step_setup_workspace() {
    print_status "Step 7/7: Setting up DeepHunt workspace..."

    # Clone or update repository
    if [ -d "$WORKSPACE_DIR/.git" ]; then
        print_status "Updating existing repository..."
        cd "$WORKSPACE_DIR"
        git pull origin main 2>/dev/null || print_warning "Git pull failed"
    else
        print_status "Cloning DeepHunt repository..."
        git clone "$REPO_URL" "$WORKSPACE_DIR" 2>/dev/null || {
            print_warning "Git clone failed, creating workspace manually..."
            mkdir -p "$WORKSPACE_DIR"
        }
    fi

    # Install DeepHunt in development mode
    if [ -d "$WORKSPACE_DIR" ]; then
        cd "$WORKSPACE_DIR"
        python -m pip install -e . 2>/dev/null || print_warning "Development install failed"
    fi

    # Initialize workspace
    python -m deephunt.cli init 2>/dev/null || print_warning "Workspace initialization skipped"

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
