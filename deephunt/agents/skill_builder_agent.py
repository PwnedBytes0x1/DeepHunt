"""
Autonomous Skill Builder Agent
Dynamically generates new skills, scripts, and tools.
"""

import asyncio
try:
    import ujson as json
except ImportError:
    import json
from pathlib import Path
from typing import Dict, Any


class SkillBuilderAgent:
    """Agent for building and registering new skills on-the-fly.

    This agent can create new skill files and scripts locally
    without approval. Execution of those scripts IS gated.
    """

    def __init__(self, skills_dir: Path, message_bus: asyncio.Queue):
        self.skills_dir = Path(skills_dir)
        self.bus = message_bus
        self.generated_dir = self.skills_dir / "generated"

    async def run(self):
        """Main agent loop."""
        self.generated_dir.mkdir(parents=True, exist_ok=True)

        await self.bus.put({
            "type": "status",
            "agent": "skill_builder",
            "message": "Skill builder ready",
        })

    async def create_skill(
        self,
        name: str,
        category: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> Path:
        """Create a new skill file.

        Args:
            name: Skill name
            category: Skill category
            content: Skill content
            metadata: Additional metadata

        Returns:
            Path to created skill file
        """
        category_dir = self.skills_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        skill_file = category_dir / f"{name}.md"

        # Build YAML frontmatter
        frontmatter = {
            "name": metadata.get("name", name),
            "category": category,
            "version": metadata.get("version", "1.0"),
            "author": metadata.get("author", "skill_builder"),
            "description": metadata.get("description", ""),
            "commands": metadata.get("commands", []),
            "tags": metadata.get("tags", []),
            "auto_generated": True,
        }

        # Write skill file
        import yaml
        with open(skill_file, "w") as f:
            f.write("---\n")
            yaml.dump(frontmatter, f, default_flow_style=False)
            f.write("---\n\n")
            f.write(content)

        await self.bus.put({
            "type": "skill_created",
            "agent": "skill_builder",
            "skill_name": name,
            "skill_path": str(skill_file),
        })

        return skill_file
