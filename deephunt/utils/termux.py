"""
Termux-specific utilities for Android 14 compatibility.
Handles permissions, notifications, wake locks, and storage.
"""

import os
import subprocess
try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path
from typing import Optional, Dict, Any

from deephunt import is_termux


class TermuxUtils:
    """Utilities for Termux integration on Android."""

    def __init__(self):
        self.is_termux = is_termux()
        self.prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        self.has_api = self._check_termux_api()

    def _check_termux_api(self) -> bool:
        """Check if Termux:API is available."""
        if not self.is_termux:
            return False
        return os.path.exists(f"{self.prefix}/libexec/termux-api")

    def _run_api(self, command: str, *args) -> tuple:
        """Run a Termux:API command.

        Args:
            command: API command name
            *args: Additional arguments

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        if not self.has_api:
            return (-1, "", "Termux:API not available")

        try:
            # Convert all args to strings to avoid type issues
            cmd_list = [f"termux-{command}"] + [str(arg) for arg in args]
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return (result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            return (-1, "", f"termux-{command} timed out")
        except FileNotFoundError:
            return (-1, "", f"termux-{command} not found")
        except Exception as e:
            return (-1, "", f"termux-{command} error: {e}")

    def setup_permissions(self) -> bool:
        """Request necessary Android permissions.

        Returns:
            True if setup was successful (or skipped gracefully)
        """
        if not self.is_termux:
            return True

        # Battery optimization exemption (non-blocking)
        try:
            rc, _, _ = self._run_api("battery-status")
            if rc != 0:
                # Try to open settings (non-blocking)
                self._run_api("open", "--chooser", "android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS")
        except Exception:
            pass

        # Notification permission (Android 14+) - non-blocking
        try:
            rc, _, _ = self._run_api(
                "notification",
                "--title", "DeepHunt Setup",
                "--content", "Testing notification permission",
            )
            if rc != 0:
                self._run_api("open", "--chooser", "android.settings.NOTIFICATION_SETTINGS")
        except Exception:
            pass

        return True  # Always return True, permissions are optional

    def send_notification(
        self,
        title: str,
        content: str,
        priority: str = "high",
    ) -> bool:
        """Send an Android notification via Termux:API.

        Args:
            title: Notification title
            content: Notification body
            priority: Priority level (low, default, high, max)

        Returns:
            True if notification was sent
        """
        if not self.has_api:
            return False

        rc, _, _ = self._run_api(
            "notification",
            "--title", title,
            "--content", content,
            "--priority", priority,
        )
        return rc == 0

    def acquire_wake_lock(self) -> bool:
        """Acquire a wake lock to prevent sleep during hunts.

        Returns:
            True if wake lock was acquired
        """
        if not self.is_termux:
            return True

        try:
            result = subprocess.run(
                ["termux-wake-lock"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def release_wake_lock(self) -> bool:
        """Release the wake lock.

        Returns:
            True if wake lock was released
        """
        if not self.is_termux:
            return True

        try:
            result = subprocess.run(
                ["termux-wake-unlock"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def toast(self, message: str) -> bool:
        """Show a toast message.

        Args:
            message: Toast message text

        Returns:
            True if toast was shown
        """
        if not self.has_api:
            return False

        rc, _, _ = self._run_api("toast", "-s", message)
        return rc == 0

    def tts_speak(self, message: str) -> bool:
        """Text-to-speech for critical alerts.

        Args:
            message: Message to speak

        Returns:
            True if message was spoken
        """
        if not self.has_api:
            return False

        rc, _, _ = self._run_api("tts-speak", message)
        return rc == 0

    def get_battery_status(self) -> Dict[str, Any]:
        """Get Android battery status.

        Returns:
            Dictionary with battery info
        """
        if not self.has_api:
            return {"status": "unknown", "percentage": 100}

        rc, stdout, _ = self._run_api("battery-status")
        if rc == 0:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                pass

        # Fallback: try reading sysfs
        try:
            with open("/sys/class/power_supply/battery/capacity") as f:
                percentage = int(f.read().strip())
            with open("/sys/class/power_supply/battery/status") as f:
                status = f.read().strip().lower()
            return {"percentage": percentage, "status": status}
        except (FileNotFoundError, PermissionError, ValueError) as e:
            import logging
            logging.getLogger(__name__).debug(f"Could not read battery sysfs: {e}")
            return {"status": "unknown", "percentage": 100}

    def get_thermal_status(self) -> Dict[str, Any]:
        """Get device thermal status.

        Returns:
            Dictionary with thermal info
        """
        temps = []

        # Try to read thermal zones
        thermal_dir = Path("/sys/class/thermal")
        if thermal_dir.exists():
            for zone in thermal_dir.glob("thermal_zone*/temp"):
                try:
                    temp_millidegrees = int(zone.read_text().strip())
                    temp_celsius = temp_millidegrees / 1000
                    temps.append({
                        "zone": zone.parent.name,
                        "temperature": temp_celsius,
                    })
                except (ValueError, PermissionError):
                    continue

        if temps:
            max_temp = max(t["temperature"] for t in temps)
            return {
                "temperatures": temps,
                "max_temperature": max_temp,
                "throttled": max_temp > 75,
            }

        return {"temperatures": [], "max_temperature": 0, "throttled": False}

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information.

        Returns:
            Dictionary with storage info
        """
        try:
            import shutil
            path = Path.home()
            total, used, free = shutil.disk_usage(path)
            return {
                "total": total,
                "used": used,
                "free": free,
                "total_gb": total / (1024**3),
                "used_gb": used / (1024**3),
                "free_gb": free / (1024**3),
            }
        except Exception:
            return {"total": 0, "used": 0, "free": 0, "total_gb": 0, "used_gb": 0, "free_gb": 0}

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage (fallback for psutil on Android)."""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()

            mem_info = {}
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    name = parts[0].strip()
                    value = parts[1].strip().split(" ")[0]
                    mem_info[name] = int(value) * 1024  # Convert KB to bytes

            total = mem_info.get("MemTotal", 0)
            available = mem_info.get("MemAvailable", mem_info.get("MemFree", 0) + mem_info.get("Cached", 0))
            used = total - available

            return {
                "total": total,
                "available": available,
                "used": used,
                "percent": (used / total * 100) if total > 0 else 0
            }
        except Exception:
            return {"total": 0, "available": 0, "used": 0, "percent": 0}
