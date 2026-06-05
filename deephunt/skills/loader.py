"""
Skill Loader
Discovers, loads, and executes skills from multiple sources.

Skill search paths (in order of priority):
1. WORKSPACE_DIR/skills/*.md
2. WORKSPACE_DIR/skills/*/*.md (subdirectories)
3. bundled skills (deephunt/skills/)
"""

import json
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


class SkillLoader:
    """Loads and manages DeepHunt skills."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = Path(skills_dir)
        self.registry_file = self.skills_dir / "registry.json"
        self._skills_cache: Dict[str, Dict[str, Any]] = {}

    def create_registry(self) -> None:
        """Create initial skill registry."""
        self.skills_dir.mkdir(parents=True, exist_ok=True)

        if not self.registry_file.exists():
            registry = {
                "version": "1.0",
                "skills": [],
                "categories": [
                    "recon",
                    "exploitation",
                    "reporting",
                    "post_exploitation",
                    "network",
                    "payloads",
                    "custom",
                ],
            }
            with open(self.registry_file, "w") as f:
                json.dump(registry, f, indent=2)

    def discover_skills(self) -> List[Dict[str, Any]]:
        """Discover all available skills.

        Searches for .md files in:
        - skills_dir/*.md (flat)
        - skills_dir/*/*.md (nested categories)

        Returns:
            List of skill metadata dictionaries
        """
        skills = []

        if not self.skills_dir.exists():
            return skills

        # Search both flat and nested skill files
        # Flat: skills/skill.md
        for skill_file in self.skills_dir.glob("*.md"):
            if skill_file.name == "README.md":
                continue
            skill_meta = self._parse_skill_file(skill_file)
            if skill_meta:
                skills.append(skill_meta)

        # Nested: skills/category/skill.md
        for skill_file in self.skills_dir.glob("*/*.md"):
            if skill_file.name == "README.md":
                continue
            skill_meta = self._parse_skill_file(skill_file)
            if skill_meta:
                skills.append(skill_meta)

        return skills

    def _parse_skill_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Parse a skill Markdown file.

        Supports YAML frontmatter:
        ---
        name: Skill Name
        category: recon
        version: "1.0"
        author: "PwnedBytes0x1"
        description: "Skill description"
        commands:
          - skill_command
        ---

        # Skill Content

        Args:
            filepath: Path to skill .md file

        Returns:
            Skill metadata dictionary or None
        """
        try:
            content = filepath.read_text()

            # Try to parse YAML frontmatter
            meta = {}
            if content.startswith("---"):
                # Extract frontmatter
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        meta = yaml.safe_load(parts[1]) or {}
                        content = parts[2].strip()
                    except yaml.YAMLError:
                        meta = {}

            # Determine category from path
            category = "custom"
            rel_path = filepath.parent.relative_to(self.skills_dir)
            if str(rel_path) != ".":
                category = str(rel_path)

            skill_name = meta.get("name", filepath.stem)

            return {
                "name": skill_name,
                "category": meta.get("category", category),
                "version": meta.get("version", "1.0"),
                "author": meta.get("author", "unknown"),
                "description": meta.get("description", ""),
                "commands": meta.get("commands", []),
                "tags": meta.get("tags", []),
                "path": str(filepath),
                "content": content,
                "metadata": meta,
            }

        except (IOError, OSError):
            return None

    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific skill by name.

        Args:
            name: Skill name

        Returns:
            Skill dictionary or None
        """
        # Check cache first
        if name in self._skills_cache:
            return self._skills_cache[name]

        # Search for skill
        for skill in self.discover_skills():
            if skill["name"] == name:
                self._skills_cache[name] = skill
                return skill

        return None

    def get_skills_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all skills in a category.

        Args:
            category: Category name

        Returns:
            List of skill dictionaries
        """
        return [
            s for s in self.discover_skills()
            if s.get("category") == category
        ]

    def register_skill(self, skill_meta: Dict[str, Any]) -> bool:
        """Register a skill in the registry.

        Args:
            skill_meta: Skill metadata

        Returns:
            True if registered successfully
        """
        if not self.registry_file.exists():
            self.create_registry()

        try:
            with open(self.registry_file) as f:
                registry = json.load(f)

            # Add skill to registry
            existing = [s for s in registry["skills"] if s.get("name") != skill_meta["name"]]
            existing.append({
                "name": skill_meta["name"],
                "category": skill_meta.get("category", "custom"),
                "version": skill_meta.get("version", "1.0"),
                "path": skill_meta.get("path", ""),
            })
            registry["skills"] = existing

            with open(self.registry_file, "w") as f:
                json.dump(registry, f, indent=2)

            return True
        except (IOError, json.JSONDecodeError):
            return False

    def execute_skill(self, name: str, **kwargs) -> bool:
        """Execute a skill by name.

        Args:
            name: Skill name
            **kwargs: Arguments for skill execution

        Returns:
            True if executed successfully
        """
        skill = self.get_skill(name)
        if not skill:
            return False

        # Skills are currently informational - execution is placeholder
        # In production, skills could contain executable Python code
        # or reference external tools
        return True

    def list_categories(self) -> List[str]:
        """List available skill categories.

        Returns:
            List of category names
        """
        categories = set()
        for skill in self.discover_skills():
            categories.add(skill.get("category", "custom"))
        return sorted(categories)

    def search_skills(self, query: str) -> List[Dict[str, Any]]:
        """Search skills by query string.

        Args:
            query: Search query

        Returns:
            Matching skills
        """
        query = query.lower()
        results = []

        for skill in self.discover_skills():
            searchable = " ".join([
                skill.get("name", ""),
                skill.get("description", ""),
                " ".join(skill.get("tags", [])),
                skill.get("category", ""),
            ]).lower()

            if query in searchable:
                results.append(skill)

        return results
