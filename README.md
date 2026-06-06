<div align="center">

```
    DeepHunt v1.0 - Autonomous AI-Driven Cybersecurity Agent
    =========================================================
```

### Autonomous AI-Driven Cybersecurity Agent

[![Version](https://img.shields.io/badge/version-1.0.0-cyan?style=flat-square)](https://github.com/PwnedBytes0x1/deephunt)
[![Python](https://img.shields.io/badge/python-3.8+-blue?style=flat-square&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Termux%20%7C%20Linux-green?style=flat-square&logo=android)](https://termux.dev)
[![License](https://img.shields.io/badge/license-MIT-purple?style=flat-square)](LICENSE)

**Designed for authorized bug bounty hunting and penetration testing on Android via Termux.**

</div>

---

## Features

| Feature | Description |
|---------|-------------|
| **AI-Driven Analysis** | Integrates with DeepSeek API for intelligent vulnerability identification |
| **Termux-First Design** | Optimized for Android 14+ with foreground service support |
| **Zero-Error Installation** | Robust error handling with graceful fallbacks |
| **Approval Gates** | All active exploitation requires explicit approval |
| **Immutable Audit Trail** | Hash-chained, tamper-evident logging |
| **Custom Skill System** | Markdown-based skills in `skills/` directory with nested support |
| **Attack Chaining** | Specialized methodology for combining vulnerabilities for maximum impact |
| **Binary Compilation** | Build standalone executables with PyInstaller |
| **Multi-Agent Architecture** | Lazy-loaded agents to minimize RAM usage |
| **Scope Enforcement** | Programmatic regex + domain filter for every request |
| **Cost Management** | Token budget tracking with per-hunt limits |

---

## Quick Start

### Installation (Termux)

```bash
# Clone the repository
git clone https://github.com/PwnedBytes0x1/deephunt.git
cd deephunt

# Install dependencies
pip install -r requirements.txt

# Or use the bootstrap script (recommended for Termux)
bash scripts/setup_termux.sh

# Initialize workspace
dhunt init
```

### Installation (Linux/macOS)

```bash
git clone https://github.com/PwnedBytes0x1/deephunt.git
cd deephunt
pip install -r requirements.txt
make install
dhunt init
```

### First Hunt

```bash
# Set your API key
dhunt config set-apikey deepseek sk-your-key-here

# Start a hunt
dhunt hunt example.com --scope "*.example.com" --aggression recon

# Check status
dhunt status

# View logs
dhunt logs

# List available skills
dhunt skills list

# Run system health check
dhunt check
```

---

## Termux Installation Guide

### Prerequisites

1. **Install Termux** from F-Droid (recommended over Play Store)
2. **Grant storage permission** (if needed for external storage access)
3. **Install Termux:API** from F-Droid for notifications and wake locks

### Automated Setup (Recommended)

```bash
# Download and run the bootstrap script
curl -fsSL https://raw.githubusercontent.com/PwnedBytes0x1/deephunt/main/scripts/setup_termux.sh | bash

# Or clone and run manually
git clone https://github.com/PwnedBytes0x1/deephunt.git
cd deephunt
bash scripts/setup_termux.sh
```

### Manual Installation

```bash
# Update package database
pkg update && pkg upgrade -y

# Install core dependencies
pkg install -y git curl wget jq python python-pip termux-api

# Install additional packages (optional but recommended)
pkg install -y clang make cmake pkg-config
pkg install -y libffi libxml2 libxslt libpng libjpeg-turbo

# Clone repository
git clone https://github.com/PwnedBytes0x1/deephunt.git
cd deephunt

# Install Python dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Initialize
dhunt init
```

### Granting Android Permissions

For full functionality, grant these permissions in Termux:

```bash
# Test notification permission
termux-notification --title "DeepHunt Test" --content "OK"

# Open battery optimization settings
termux-open --chooser "android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS"

# Acquire wake lock (optional, for long-running hunts)
termux-wake-lock
```

---

## Building from Source

### Compile to Binary (Desktop)

```bash
# Install development dependencies
pip install -e ".[dev]"

# Build standalone binary
make binary

# Install globally
sudo cp dist/dhunt /usr/local/bin/
```

### Termux-Specific Build

```bash
# Optimized for Android/Termux
make binary-termux

# Binary will be at:
# $HOME/.local/bin/dhunt-termux
```

### Using Make

```bash
make help          # Show all available targets
make install       # Install production dependencies
make install-dev   # Install with dev dependencies
make setup         # Full first-time setup
make termux-install # Termux-specific install
make install-minimal # Minimal install (core deps only)
make binary        # Build standalone binary
make clean          # Clean build artifacts
```

---

## Skills System

DeepHunt uses a modular Markdown-based skills system. Skills are stored as Markdown files with YAML frontmatter, providing the AI agent with domain-specific knowledge and methodologies.

### Core Modules

| Module | Purpose |
|--------|---------|
| **03-recon-osint** | Advanced attack surface mapping and target discovery |
| **04-vuln-finding** | Systematic vulnerability identification (CVE, SAST, SCA) |
| **05-web-exploit** | Web application attack vectors and methodologies |
| **10-cloud-security** | Cloud-native (AWS/Azure/GCP) and container exploitation |
| **12-ai-redteam** | Specialized techniques for attacking AI/ML models |
| **20-owasp-top10** | Detailed manuals for the OWASP Top 10 categories |
| **21-chaining** | Methodology for combining low-impact bugs into critical chains |

### Directory Structure

```
skills/
+-- 03-recon-osint/          # OSINT & Active Recon
+-- 04-vulnerability-finding/ # Systematic discovery
+-- 05-web-exploitation/     # Web application attacks
+-- 20-owasp-top10/          # OWASP Top 10 Manuals
+-- 21-chaining/             # Attack Chaining
+-- ...
```

### Skill Format (YAML Frontmatter)

Each skill file (`.md`) must include YAML frontmatter for the loader to identify it:

```markdown
---
name: SSRF to Cloud Metadata
category: chaining
version: "1.0"
author: "PwnedBytes0x1"
description: "Chaining SSRF to extract cloud IAM credentials"
tags:
  - ssrf
  - cloud
  - chaining
---

# SSRF to Cloud Metadata

Your methodology and technical details here...
```

### CLI Commands

```bash
# List all discovered skills
dhunt skills list

# Filter by category (e.g., recon, chaining)
dhunt skills list --category chaining

# Show specific skill content
dhunt skills show "Common Attack Chains"

# Load and execute a skill
dhunt skills load "Skill Name"
```

---

## Architecture

```
                    +------------------------+
                    |   CLI (dhunt)          |
                    +------------------------+
                             |
        +--------------------+--------------------+
        |                    |                    |
   +--------+          +-----------+         +---------+
   | Config |          | Identity  |         | Skills  |
   |Manager |          | Manager   |         | Loader  |
   +--------+          +-----------+         +---------+
        |                    |                    |
        +--------------------+--------------------+
                             |
                    +------------------------+
                    |   Orchestrator         |
                    +------------------------+
                             |
        +--------------------+--------------------+
        |                    |                    |
   +---------+         +----------+         +-----------+
   | Recon   |         | Vuln ID  |         | Skill     |
   | Agent   |         | Agent    |         | Builder   |
   +---------+         +----------+         +-----------+
```

---

## Termux Compatibility

DeepHunt is built specifically for Termux on Android 14+.

### Android 14 Considerations

- **Foreground Services**: Runs as Termux foreground process with `termux-wake-lock`
- **Notifications**: Uses `termux-notification` for approval requests
- **Scoped Storage**: All data stays within `$HOME` (Termux internal storage)
- **Battery Optimization**: Disables battery optimization for long hunts
- **RAM Management**: Soft 1.5GB cap with automatic agent serialization
- **Thermal Throttling**: Monitors CPU temperature and throttles scans

### Termux-Specific Features

- **Non-blocking Installation**: Script continues even if some packages fail
- **Graceful Fallbacks**: Missing optional dependencies don't break the tool
- **Memory Fallback**: Uses `/proc/meminfo` when psutil is unavailable
- **Notification Fallback**: Silently skips notifications if Termux:API unavailable

### Troubleshooting Termux Issues

```bash
# Check if Termux environment is detected
dhunt check

# Re-run bootstrap script
bash scripts/setup_termux.sh

# Install missing dependencies manually
pip install package-name

# Check Termux:API availability
termux-notification --title "Test" --content "DeepHunt"
```

---

## Configuration

### Identity Files (`.identity/`)

| File | Purpose |
|------|---------|
| `user.md` | Operator profile, preferences, aggression level |
| `soul.md` | Agent personality, model preferences, identity |
| `taste.md` | Code style, vuln priorities, tool preferences |

### Configuration Commands

```bash
# Show current configuration
dhunt config show

# Edit configuration
dhunt config edit

# Set API key
dhunt config set-apikey deepseek YOUR_API_KEY

# Set environment variable for workspace
export WORKSPACE_DIR=~/deephunt
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `WORKSPACE_DIR` | Workspace directory path (default: ~/deephunt on Termux, ~/.deephunt elsewhere) |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for notifications |
| `DEEPHUNT_LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING) |
| `DEEPHUNT_SALT` | Salt for immutable log HMAC (change for production) |

---

## Safety & Ethics

> **This tool is designed exclusively for authorized bug bounty hunting and penetration testing with explicit written permission.**

- **Action Gating**: All active exploitation requires explicit approval
- **Scope Enforcement**: Programmatic filters prevent out-of-scope operations
- **Emergency Kill**: Configurable regex patterns trigger immediate halt
- **Immutable Logging**: Tamper-evident audit trail for all actions

---

## Troubleshooting

### Installation Issues

```bash
# Clean install
rm -rf ~/.local/lib/python*/site-packages/deephunt*
pip uninstall deephunt
pip install -e .

# Check Python version
python --version  # Requires 3.8+

# Verify installation
python -c "import deephunt; print(deephunt.__version__)"
```

### Termux-Specific Issues

```bash
# Fix permissions
termux-setup-storage

# Reinstall Termux:API
pkg uninstall termux-api && pkg install termux-api

# Check available space
df -h ~

# Clear pip cache
pip cache purge
```

### Running the Tool

```bash
# Verbose mode
dhunt --verbose hunt example.com

# No color output (for terminals without color support)
dhunt --no-color init

# Use custom workspace
dhunt --workspace /path/to/workspace init
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) file.

**Disclaimer**: The user bears full legal, ethical, and financial responsibility for the use of this tool. The author and contributors are not responsible for any damage caused by the use of this script.

---

<div align="center">

**[PwnedBytes0x1](https://hackerone.com/PwnedBytes0x1)**

</div>