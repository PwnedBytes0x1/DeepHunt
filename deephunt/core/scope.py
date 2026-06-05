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
        self._compile_errors: List[str] = []

        # Compile patterns with proper error handling
        for pattern in allow_patterns:
            try:
                self.allow.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                # Try to convert glob-style pattern to regex
                glob_pattern = self._glob_to_regex(pattern)
                try:
                    self.allow.append(re.compile(glob_pattern, re.IGNORECASE))
                except re.error:
                    self._compile_errors.append(f"Allow pattern '{pattern}': {e}")
                    self.allow.append(re.compile(re.escape(pattern), re.IGNORECASE))

        for pattern in (deny_patterns or []):
            try:
                self.deny.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                # Try to convert glob-style pattern to regex
                glob_pattern = self._glob_to_regex(pattern)
                try:
                    self.deny.append(re.compile(glob_pattern, re.IGNORECASE))
                except re.error:
                    self._compile_errors.append(f"Deny pattern '{pattern}': {e}")
                    # Fallback: escape special characters but allow wildcards
                    escaped = pattern.replace(".", r"\.").replace("*", ".*")
                    self.deny.append(re.compile(escaped, re.IGNORECASE))

    @staticmethod
    def _glob_to_regex(pattern: str) -> str:
        """Convert glob-style wildcard pattern to regex.
        
        Args:
            pattern: Glob pattern (e.g., '*.internal.*')
            
        Returns:
            Regex pattern string
        """
        # Escape special regex chars except * and ?
        result = ""
        for char in pattern:
            if char == "*":
                result += ".*"
            elif char == "?":
                result += "."
            else:
                result += re.escape(char)
        return result

    def get_compile_errors(self) -> List[str]:
        """Return list of pattern compilation errors."""
        return self._compile_errors.copy()

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

        # FIRST check deny list (emergency kill patterns take priority)
        for pattern in self.deny:
            if pattern.search(hostname) or pattern.search(url):
                return False, f"DENIED: matches deny pattern {pattern.pattern}"

        # THEN check allow list (only if not denied)
        for pattern in self.allow:
            if pattern.search(hostname) or pattern.search(url):
                return True, "ALLOWED"

        # Default deny - nothing matched allow list
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
