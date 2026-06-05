"""
Logging utilities for DeepHunt
Handles both system logging and hunt-specific immutable logging.
"""

import logging
import hashlib
import hmac
try:
    import ujson as json
except ImportError:
    import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: Path,
    level: int = logging.INFO,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """Set up system logging.

    Args:
        log_dir: Directory for log files
        level: Logging level
        log_format: Custom log format string

    Returns:
        Configured logger instance
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "deephunt.log"

    if not log_format:
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
        )

    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure logger
    logger = logging.getLogger("deephunt")
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class ImmutableLog:
    """Immutable, hash-chained audit log for hunt activities.

    Each entry contains a SHA-256 hash of the previous entry,
    creating a tamper-evident chain. Entries are also signed
    with an HMAC key derived from the hunt ID and master passphrase.
    """

    def __init__(self, hunt_id: str, log_dir: Path):
        """Initialize the immutable log.

        Args:
            hunt_id: Unique hunt identifier
            log_dir: Directory to store the log file
        """
        self.hunt_id = hunt_id
        self.log_path = log_dir / "hunt.log"
        self.key = self._derive_key()
        self.last_hash = self._get_last_hash()

    def _derive_key(self) -> bytes:
        """Derive HMAC key from hunt_id and environment."""
        # Use environment-specific salt
        salt = os.environ.get("DEEPHUNT_SALT", "deephunt-default-salt").encode()
        return hashlib.pbkdf2_hmac("sha256", self.hunt_id.encode(), salt, 100000)

    def _get_last_hash(self) -> str:
        """Get the last hash from existing log or return genesis hash."""
        if not self.log_path.exists():
            return "0" * 64

        try:
            with open(self.log_path) as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    return last_entry.get("this_hash", "0" * 64)
        except (json.JSONDecodeError, IOError):
            pass

        return "0" * 64

    def append(
        self,
        agent: str,
        level: str,
        message: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Append an entry to the immutable log.

        Args:
            agent: Agent name that generated the entry
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message
            metadata: Optional metadata dictionary

        Returns:
            The complete log entry
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent": agent,
            "level": level,
            "message": message,
            "metadata": metadata or {},
            "prev_hash": self.last_hash,
        }

        # Calculate this entry's hash
        entry_str = json.dumps(entry, sort_keys=True)
        entry["this_hash"] = hashlib.sha256(entry_str.encode()).hexdigest()

        # Sign the entry
        entry["signature"] = hmac.new(
            self.key, entry_str.encode(), hashlib.sha256
        ).hexdigest()

        # Append to file
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # Update last hash
        self.last_hash = entry["this_hash"]

        return entry

    def verify_chain(self) -> list:
        """Verify the integrity of the log chain.

        Returns:
            List of any tampered entry indices
        """
        if not self.log_path.exists():
            return []

        tampered = []
        expected_hash = "0" * 64

        with open(self.log_path) as f:
            for i, line in enumerate(f):
                try:
                    entry = json.loads(line)

                    # Check prev_hash matches
                    if entry.get("prev_hash") != expected_hash:
                        tampered.append(i)
                        expected_hash = entry.get("this_hash", "0" * 64)
                        continue

                    # Verify this_hash
                    entry_copy = dict(entry)
                    actual_hash = entry_copy.pop("this_hash", "")
                    entry_copy.pop("signature", None)
                    expected_this = hashlib.sha256(
                        json.dumps(entry_copy, sort_keys=True).encode()
                    ).hexdigest()

                    if actual_hash != expected_this:
                        tampered.append(i)
                        expected_hash = actual_hash
                        continue

                    # Verify HMAC signature
                    entry_str = json.dumps(entry_copy, sort_keys=True)
                    expected_sig = hmac.new(
                        self.key, entry_str.encode(), hashlib.sha256
                    ).hexdigest()
                    
                    if entry.get("signature") != expected_sig:
                        tampered.append(i)

                    expected_hash = actual_hash

                except (json.JSONDecodeError, KeyError, TypeError):
                    tampered.append(i)

        return tampered
