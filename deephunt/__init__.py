"""
DeepHunt v1.0 - Autonomous AI-Driven Cybersecurity Agent
Termux-First Implementation | Android 14 Compatible

An autonomous vulnerability hunting agent designed for authorized
bug bounty hunting and penetration testing on Android via Termux.

Author: PwnedBytes0x1 (HackerOne)
License: MIT
"""

__title__ = "deephunt"
__version__ = "1.0.0"
__author__ = "PwnedBytes0x1"
__license__ = "MIT"
__description__ = "Autonomous AI-Driven Cybersecurity Agent for Termux"

from pathlib import Path
from typing import Optional
import os


def get_workspace_dir() -> Path:
    """Get the DeepHunt workspace directory.
    
    Returns:
        Path to the workspace directory. On Termux, this defaults
        to $HOME/deephunt. On other systems, uses $HOME/.deephunt.
    """
    if is_termux():
        default = Path.home() / "deephunt"
    else:
        default = Path.home() / ".deephunt"

    return Path(os.getenv("WORKSPACE_DIR", str(default)))


def is_termux() -> bool:
    """Detect if running inside Termux environment."""
    return (
        "TERMUX_VERSION" in os.environ
        or os.path.exists("/data/data/com.termux/files/usr")
        or "com.termux" in os.environ.get("PREFIX", "")
    )


def is_android() -> bool:
    """Detect if running on Android."""
    return (
        is_termux()
        or "ANDROID_ROOT" in os.environ
        or os.path.exists("/system/build.prop")
    )


# Workspace paths
WORKSPACE_DIR = get_workspace_dir()
IDENTITY_DIR = WORKSPACE_DIR / ".identity"
HUNTS_DIR = WORKSPACE_DIR / "deephunt_hunts"
SKILLS_DIR = WORKSPACE_DIR / "skills"
LOGS_DIR = WORKSPACE_DIR / "logs"
CACHE_DIR = WORKSPACE_DIR / "cache"
TMP_DIR = WORKSPACE_DIR / "tmp"
WORDLISTS_DIR = WORKSPACE_DIR / "wordlists"
