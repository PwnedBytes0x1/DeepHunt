"""
Identity Management - The .md Trinity
Handles user.md, soul.md, and taste.md identity files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Identity:
    """Combined identity for the agent."""
    user: Dict[str, Any] = field(default_factory=dict)
    soul: Dict[str, Any] = field(default_factory=dict)
    taste: Dict[str, Any] = field(default_factory=dict)

    @property
    def handle(self) -> str:
        return self.user.get("handle", "unknown")

    @property
    def aggression_level(self) -> str:
        return self.user.get("aggression_level", "recon_plus_validation")

    @property
    def model_preference(self) -> str:
        return self.soul.get("default_model", "deepseek-v4-flash")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "soul": self.soul,
            "taste": self.taste,
        }


DEFAULT_USER_MD = """# Operator Profile
# Edit this file to customize your DeepHunt identity

platform: HackerOne
handle: PwnedBytes0x1
preferred_language: en
report_language: en
quiet_hours: 00:00-08:00
notification_priority: high
aggression_level: recon_plus_validation  # Options: passive_only | recon_plus_validation | full_exploit
cvss_version: "3.1"
max_cvss_for_auto_report: 6.0
preferred_poc_format: python_requests
preferred_report_template: hackerone_markdown
auto_submit_drafts: false
emergency_kill_regexes:
  - '*.prod.*'
  - '*.internal.*'
  - '*.admin.*'
"""

DEFAULT_SOUL_MD = """# DeepHunt Soul
# The agent's persistent personality and operational preferences

name: DeepHunt
version: "1.0"
reasoning_style: paranoid_about_false_positives
confirmation_required_signals: 3
default_model: deepseek-v4-flash
fallback_model: deepseek-v4-pro
high_temp_model: deepseek-v4-flash
creative_temperature: 0.8
recon_order:
  - subdomains
  - endpoints
  - parameters
  - technologies
  - content
meta_learning: enabled
failure_response: update_prompt_templates
identity_anchor: |
  I am DeepHunt, an autonomous cybersecurity agent operating on behalf
  of {handle}. I prioritize accuracy over speed. I never operate
  outside scope. I require explicit approval before any active
  exploitation. I learn from every hunt and update my own strategies.
"""

DEFAULT_TASTE_MD = """# DeepHunt Taste
# Coding and vulnerability preferences

## Code Style
indent: 4 spaces
max_line_length: 100
quote_style: double
language_preference: python3
async_first: true

## Vulnerability Priority (High to Low)
priority_vulns:
  - SSRF
  - IDOR
  - SQLi
  - JWT_Attacks
  - Business_Logic
  - GraphQL_Injection
  - Cache_Poisoning
  - XXE
  - SSTI
  - Open_Redirect
  - XSS

## Tool Preferences
preferred_subdomain_enum:
  - subfinder
  - amass
  - assetfinder
preferred_crawler: katana
preferred_endpoint_discovery:
  - gau
  - waybackurls
  - hakrawler
preferred_port_scanner: naabu
preferred_fuzzer: ffuf
preferred_param_discovery:
  - arjun
  - x8
preferred_tech_fingerprint:
  - httpx
  - wappalyzer

## Report Preferences
include_screenshots: true
include_http_transcripts: true
include_reproduction_steps: true
include_remediation: true
include_xai_chain: true
"""


class IdentityManager:
    """Manages DeepHunt identity files."""

    IDENTITY_FILES = {
        "user.md": DEFAULT_USER_MD,
        "soul.md": DEFAULT_SOUL_MD,
        "taste.md": DEFAULT_TASTE_MD,
    }

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.identity_dir = self.workspace / ".identity"

    def create_default_identity(self) -> None:
        """Create default identity files if they don't exist."""
        self.identity_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in self.IDENTITY_FILES.items():
            filepath = self.identity_dir / filename
            if not filepath.exists():
                filepath.write_text(content)

    def load_identity(self) -> Identity:
        """Load identity from .md files.

        Returns:
            Identity object with user, soul, and taste data
        """
        identity = Identity()

        for section, filename in [("user", "user.md"), ("soul", "soul.md"), ("taste", "taste.md")]:
            filepath = self.identity_dir / filename
            if filepath.exists():
                try:
                    data = yaml.safe_load(filepath.read_text())
                    if data:
                        setattr(identity, section, data)
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to parse {filename}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error loading {filename}: {e}")

        # Format identity anchor with handle
        if "identity_anchor" in identity.soul:
            identity.soul["identity_anchor"] = identity.soul["identity_anchor"].format(
                handle=identity.handle
            )

        return identity

    def update_section(self, section: str, data: Dict[str, Any]) -> None:
        """Update a specific identity section.

        Args:
            section: Section name (user, soul, taste)
            data: New data to merge
        """
        filename_map = {
            "user": "user.md",
            "soul": "soul.md",
            "taste": "taste.md",
        }

        if section not in filename_map:
            raise ValueError(f"Unknown section: {section}")

        filepath = self.identity_dir / filename_map[section]

        # Load existing
        existing = {}
        if filepath.exists():
            try:
                existing = yaml.safe_load(filepath.read_text()) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse {filepath}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading {filepath}: {e}")

        # Merge and save
        existing.update(data)
        filepath.write_text(yaml.dump(existing, default_flow_style=False))
