#!/data/data/com.termux/files/usr/bin/bash
#===============================================================================
# DeepHunt Termux Bootstrap Script
# Auto-executed on first run or manual setup
# Compatible with Android 14+ / Termux (F-Droid)
#===============================================================================

set -e

TERMUX_PREFIX="/data/data/com.termux/files/usr"
HOME_DIR="$HOME"
WORKSPACE_DIR="${HOME_DIR}/deephunt"
REPO_URL="https://github.com/PwnedBytes0x1/deephunt.git"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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
    available=$(df "$HOME" | tail -1 | awk '{print $4}')
    local available_gb=$((available / 1024 / 1024))

    if [ "$available_gb" -lt 2 ]; then
        print_error "Insufficient storage. Need at least 2GB free."
        print_error "Available: ${available_gb}GB"
        exit 1
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
    pkg install -y \
        git \
        curl \
        wget \
        jq \
        python \
        python-pip \
        sqlite \
        termux-api \
        termux-auth \
        openssl-tool \
        proot-distro \
        clang \
        make \
        cmake \
        pkg-config \
        libffi \
        libxml2 \
        libxslt \
        libpng \
        libjpeg-turbo \
        freetype \
        zlib \
        libzmq \
        libczmq \
        binutils \
        rust

    print_success "Core dependencies installed"
}

step_install_python() {
    print_status "Step 3/7: Installing Python libraries..."

    pip install --upgrade pip setuptools wheel

    pip install \
        click \
        rich \
        aiohttp \
        aiofiles \
        beautifulsoup4 \
        lxml \
        html2text \
        requests \
        urllib3 \
        pydantic \
        pyyaml \
        python-dotenv \
        orjson \
        httpx[http2] \
        websockets \
        schedule \
        cryptography \
        prompt-toolkit

    # Install optional telegram support
    pip install python-telegram-bot[ext] || print_warning "Telegram support installation failed"

    print_success "Python libraries installed"
}

step_install_go_tools() {
    print_status "Step 4/7: Installing Go-based tools..."

    if command -v go &> /dev/null; then
        export GOPATH="$HOME/go"
        export PATH="$PATH:$GOPATH/bin"

        go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest || print_warning "naabu install failed"
        go install github.com/projectdiscovery/katana/cmd/katana@latest || print_warning "katana install failed"
        go install github.com/projectdiscovery/httpx/cmd/httpx@latest || print_warning "httpx install failed"
        go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest || print_warning "subfinder install failed"
        go install github.com/projectdiscovery/notify/cmd/notify@latest || print_warning "notify install failed"
        go install github.com/lc/gau/v2/cmd/gau@latest || print_warning "gau install failed"
        go install github.com/ffuf/ffuf@latest || print_warning "ffuf install failed"
        go install github.com/sensepost/gowitness@latest || print_warning "gowitness install failed"

        print_success "Go tools installed"
    else
        print_warning "Go not found. Skipping native tools."
        print_warning "Install Go for better performance: pkg install golang"
    fi
}

step_install_python_tools() {
    print_status "Step 5/7: Installing Python-based tools..."

    pip install \
        dirsearch \
        arjun \
        wafw00f || print_warning "Some tools failed to install"

    print_success "Python tools installed"
}

step_permissions() {
    print_status "Step 6/7: Requesting Android permissions..."

    # Request notification permission
    if ! termux-notification --title "DeepHunt Test" --content "API OK" 2>/dev/null; then
        print_warning "Please grant notification permission to Termux:API"
        termux-open --chooser "android.settings.NOTIFICATION_SETTINGS" 2>/dev/null || true
    fi

    # Disable battery optimization
    termux-open --chooser "android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" 2>/dev/null || true

    print_success "Permission requests completed"
}

step_setup_workspace() {
    print_status "Step 7/7: Setting up DeepHunt workspace..."

    # Clone or update repository
    if [ -d "$WORKSPACE_DIR/.git" ]; then
        print_status "Updating existing repository..."
        cd "$WORKSPACE_DIR"
        git pull origin main || print_warning "Git pull failed"
    else
        print_status "Cloning DeepHunt repository..."
        git clone "$REPO_URL" "$WORKSPACE_DIR" || {
            print_warning "Git clone failed, creating workspace manually..."
            mkdir -p "$WORKSPACE_DIR"
        }
    fi

    # Install DeepHunt in development mode
    cd "$WORKSPACE_DIR"
    pip install -e . || print_warning "Development install failed, using direct execution"

    # Initialize workspace
    python -m deephunt.cli init || print_warning "Workspace initialization failed"

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
    print ""

    # Run checks
    check_termux
    check_storage

    # Run installation steps
    step_update_pkg
    step_install_core
    step_install_python
    step_install_go_tools
    step_install_python_tools
    step_permissions
    step_setup_workspace

    # Post-installation
    print ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  DeepHunt Bootstrap Complete!          ${NC}"
    echo -e "${GREEN}========================================${NC}"
    print ""
    print_status "Workspace: $WORKSPACE_DIR"
    print_status "Binary: dhunt"
    print ""
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
