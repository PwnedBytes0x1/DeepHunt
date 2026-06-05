"""
Scope Enforcement Engine
Programmatic filter for in-scope/out-of-scope decisions.
"""

import re
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from urllib.parse import urlparse


class ScopeFilter:
    """Enforces scope boundaries for all network operations.

    Every sub-agent must check targets through this filter
    before making any network request.
    """

    def __init__(
        self,
        allow_patterns: List[str],
        deny_patterns: Optional[List[str]] = None,
    ):
        """Initialize scope filter.

        Args:
            allow_patterns: Regex patterns for allowed targets
            deny_patterns: Regex patterns for denied targets
        """
        self.allow = []
        self.deny = []
        self.allow_patterns = allow_patterns
        self.deny_patterns = deny_patterns or []

        # Compile patterns
        for pattern in allow_patterns:
            try:
                self.allow.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                pass

        for pattern in (deny_patterns or []):
            try:
                self.deny.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                pass

    def check(self, url: str) -> Tuple[bool, str]:
        """Check if URL is in scope.

        Args:
            url: URL to check

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Parse URL
        parsed = urlparse(url)
        hostname = parsed.hostname or url

        # Check deny list first
        for pattern in self.deny:
            if pattern.search(hostname) or pattern.search(url):
                return False, f"DENIED: matches deny pattern {pattern.pattern}"

        # Check deny list for emergency kill patterns
        for pattern in self.deny:
            if pattern.search(hostname) or pattern.search(url):
                return False, f"DENIED: emergency kill pattern matched"

        # Check allow list
        for pattern in self.allow:
            if pattern.search(hostname) or pattern.search(url):
                return True, "ALLOWED"

        # Default deny
        return False, "DENIED: no allow pattern matched"

    def check_redirect(self, original_url: str, redirect_url: str) -> Tuple[bool, str]:
        """Check if a redirect target is in scope.

        Args:
            original_url: Initial request URL
            redirect_url: Redirect destination

        Returns:
            Tuple of (is_allowed, reason)
        """
        allowed, reason = self.check(redirect_url)
        if not allowed:
            return False, f"REDIRECT_BLOCKED: {redirect_url} -> {reason}"
        return True, "ALLOWED"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize filter configuration."""
        return {
            "allow": self.allow_patterns,
            "deny": self.deny_patterns,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScopeFilter":
        """Create filter from dictionary."""
        return cls(
            allow_patterns=data.get("allow", []),
            deny_patterns=data.get("deny", []),
        )
