<div align="center">

```
    ██████╗ ███████╗███████╗██████╗ ██╗  ██╗██╗   ██╗███╗   ██╗████████╗
    ██╔══██╗██╔════╝██╔════╝██╔══██╗██║  ██║██║   ██║████╗  ██║╚══██╔══╝
    ██║  ██║█████╗  █████╗  ██████╔╝███████║██║   ██║██╔██╗ ██║   ██║   
    ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║   ██║   
    ██████╔╝███████╗███████╗██║     ██║  ██║╚██████╔╝██║ ╚████║   ██║   
    ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   
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

### Installation

```bash
# Clone the repository
git clone https://github.com/PwnedBytes0x1/deephunt.git
cd deephunt

# Install dependencies
pip install -r requirements.txt

# Or install with make
make install

# Initialize workspace
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
```

---

## Building from Source

### Compile to Binary

```bash
# Install development dependencies
pip install -e ".[dev]"

# Build standalone binary
make binary

# Install globally
sudo cp dist/dhunt /usr/local/bin/
# Or for Termux:
cp dist/dhunt $PREFIX/bin/
```

### Termux-Specific Build

```bash
# Optimized for Android/Termux
make binary-termux

# Binary will be at:
# $HOME/.local/bin/dhunt-termux
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
├── 03-recon-osint/          # OSINT & Active Recon
├── 04-vulnerability-finding/# Systematic discovery
├── 05-web-exploitation/     # Web application attacks
├── 20-owasp-top10/          # OWASP Top 10 Manuals
├── 21-chaining/             # Attack Chaining
└── ...
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

# Search for skills by keyword
# (Coming in v1.2)
```

---

## Architecture

```
                    ┌─────────────────┐
                    │   CLI (dhunt)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌──────────┐  ┌──────────┐  ┌──────────┐
       │  Config  │  │ Identity │  │  Skills  │
       │ Manager  │  │ Manager  │  │  Loader  │
       └─────┬────┘  └─────┬────┘  └─────┬────┘
             │              │              │
             └──────────────┼──────────────┘
                            │
                   ┌────────┴────────┐
                   │   Orchestrator  │
                   └────────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │  Recon   │ │ Vuln ID  │ │  Skill   │
       │  Agent   │ │  Agent   │ │ Builder  │
       └──────────┘ └──────────┘ └──────────┘
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

### Required Permissions

```bash
# Grant notification permission (Android 14+)
termux-notification --title "DeepHunt Test" --content "OK"

# Disable battery optimization
termux-open --chooser "android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS"

# Wake lock for long hunts
termux-wake-lock
```

---

## Configuration

### Identity Files (`.identity/`)

| File | Purpose |
|------|---------|
| `user.md` | Operator profile, preferences, aggression level |
| `soul.md` | Agent personality, model preferences, identity |
| `taste.md` | Code style, vuln priorities, tool preferences |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `WORKSPACE_DIR` | Workspace directory path |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `DEEPHUNT_LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING) |

---

## Safety & Ethics

> **This tool is designed exclusively for authorized bug bounty hunting and penetration testing with explicit written permission.**

- **Action Gating**: All active exploitation requires explicit approval
- **Scope Enforcement**: Programmatic filters prevent out-of-scope operations
- **Emergency Kill**: Configurable regex patterns trigger immediate halt
- **Immutable Logging**: Tamper-evident audit trail for all actions

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
