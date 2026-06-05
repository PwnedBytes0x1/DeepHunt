"""
Configuration Management
Handles global config, environment variables, and runtime settings.
"""

import os
try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class Config:
    """DeepHunt configuration."""
    workspace: str = ""
    api_keys: Dict[str, str] = field(default_factory=dict)
    models: Dict[str, str] = field(default_factory=dict)
    limits: Dict[str, Any] = field(default_factory=dict)
    telegram: Dict[str, Any] = field(default_factory=dict)
    termux: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, str] = field(default_factory=dict)


class ConfigManager:
    """Manages DeepHunt configuration."""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.config_file = self.workspace / "config.json"

    def create_default_config(self) -> None:
        """Create default configuration file."""
        self.workspace.mkdir(parents=True, exist_ok=True)

        config = {
            "version": "1.0.0",
            "workspace": str(self.workspace),
            "api_keys": {
                "deepseek": "",
                "telegram": "",
                "hackerone": "",
            },
            "models": {
                "default": "deepseek-v4-flash",
                "fallback": "deepseek-v4-pro",
                "creative": "deepseek-v4-flash",
            },
            "limits": {
                "max_ram_mb": 1536,
                "max_concurrent_connections": 10,
                "default_budget_usd": 5.0,
                "max_tokens_per_task": 2048,
                "max_tokens_per_report": 16384,
                "request_rate_limit": 5,
                "jitter_min": 0.5,
                "jitter_max": 2.0,
            },
            "telegram": {
                "enabled": False,
                "webhook_url": "",
                "approval_timeout_minutes": 60,
                "escalation_minutes": [10, 30, 60],
            },
            "termux": {
                "use_wake_lock": True,
                "notifications": True,
                "toast_on_milestone": True,
                "tts_on_critical": True,
                "battery_threshold": 15,
                "temperature_threshold": 75,
                "shallow_mode_storage_gb": 2,
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "console_output": True,
            },
        }

        if not self.config_file.exists():
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment.

        Returns:
            Merged configuration dictionary
        """
        config = {}

        # Load from file
        if self.config_file.exists():
            with open(self.config_file) as f:
                config = json.load(f)

        # Override with environment variables
        env_overrides = {
            "DEEPSEEK_API_KEY": ["api_keys", "deepseek"],
            "TELEGRAM_BOT_TOKEN": ["api_keys", "telegram"],
            "HACKERONE_API_KEY": ["api_keys", "hackerone"],
            "WORKSPACE_DIR": ["workspace"],
            "DEEPHUNT_LOG_LEVEL": ["logging", "level"],
        }

        for env_var, path in env_overrides.items():
            value = os.environ.get(env_var)
            if value:
                self._set_nested(config, path, value)

        return config

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file.

        Args:
            config: Configuration dictionary
        """
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def update_config(self, path: list, value: Any) -> None:
        """Update a specific config value.

        Args:
            path: List of keys forming the path
            value: New value
        """
        config = self.load_config()
        self._set_nested(config, path, value)
        self.save_config(config)

    @staticmethod
    def _set_nested(data: dict, path: list, value: Any) -> None:
        """Set a nested dictionary value."""
        for key in path[:-1]:
            data = data.setdefault(key, {})
        data[path[-1]] = value
