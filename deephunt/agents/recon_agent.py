"""
Reconnaissance Agent
Handles passive and active reconnaissance with politeness engine.
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import aiohttp


class ReconAgent:
    """Agent for reconnaissance tasks."""

    def __init__(
        self,
        hunt_id: str,
        scope: Dict[str, Any],
        message_bus: asyncio.Queue,
        hunt_dir: Optional[Path] = None,
    ):
        self.hunt_id = hunt_id
        self.scope = scope
        self.bus = message_bus
        self.hunt_dir = hunt_dir or Path.home() / "deephunt" / "deephunt_hunts" / hunt_id
        self.cache_dir = self.hunt_dir / "cache"
        self.assets = {
            "domains": [],
            "endpoints": [],
            "parameters": [],
            "technologies": [],
        }
        self.running = True

    async def run(self):
        """Main agent loop."""
        await self.bus.put({
            "type": "status",
            "agent": "recon",
            "hunt_id": self.hunt_id,
            "message": "Starting reconnaissance",
        })

        try:
            # Passive reconnaissance (no approval needed)
            await self._passive_dns_enum()
            await self._certificate_transparency()
            await self._web_archive_crawl()
            await self._web_fingerprinting()

            # Request approval for active recon
            action_id = f"{self.hunt_id}_portscan"
            await self.bus.put({
                "type": "approval_request",
                "agent": "recon",
                "hunt_id": self.hunt_id,
                "action_id": action_id,
                "action_type": "port_scanning",
                "target": self.scope.get("allow", ["unknown"])[0],
                "payload_preview": "naabu -host target -top-ports 1000",
                "risk_level": "medium",
                "estimated_cost_usd": 0.01,
            })

            # Save assets after passive phase
            await self._save_assets()

            await self.bus.put({
                "type": "status",
                "agent": "recon",
                "hunt_id": self.hunt_id,
                "message": "Passive reconnaissance complete",
                "assets": self.assets,
            })

        except Exception as e:
            await self.bus.put({
                "type": "error",
                "agent": "recon",
                "hunt_id": self.hunt_id,
                "message": f"Recon error: {e}",
            })

    async def _passive_dns_enum(self):
        """Passive DNS enumeration via subfinder or fallback."""
        target = self.scope.get("allow", ["unknown"])[0]
        cache_key = f"subfinder_{target}"
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    self.assets["domains"] = json.load(f)
                return
            except (json.JSONDecodeError, IOError):
                pass

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["subfinder", "-d", target, "-all", "-silent", "-oJ"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        self.assets["domains"].append({
                            "domain": data.get("host", ""),
                            "source": "subfinder",
                            "ip": data.get("ip", None),
                            "discovered_at": datetime.utcnow().isoformat(),
                        })
                    except json.JSONDecodeError:
                        pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            await self._fallback_dns_enum(target)

        # Cache results
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(cache_file, "w") as f:
                json.dump(self.assets["domains"], f)
        except IOError:
            pass

    async def _certificate_transparency(self):
        """Query certificate transparency logs."""
        target = self.scope.get("allow", ["unknown"])[0]
        url = f"https://crt.sh/?q=%.{target}&output=json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={"User-Agent": "DeepHunt/1.0"},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data:
                            domain = entry.get("name_value", "").strip()
                            if domain and domain not in [
                                d["domain"] for d in self.assets["domains"]
                            ]:
                                self.assets["domains"].append({
                                    "domain": domain,
                                    "source": "crt.sh",
                                    "ip": None,
                                    "discovered_at": datetime.utcnow().isoformat(),
                                })
        except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError):
            pass

    async def _web_archive_crawl(self):
        """Crawl web archives for endpoints."""
        target = self.scope.get("allow", ["unknown"])[0]

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["gau", target],
                capture_output=True,
                text=True,
                timeout=300,
            )
            urls = result.stdout.strip().split("\n")
            for url in urls:
                if url:
                    self.assets["endpoints"].append({
                        "url": url,
                        "method": "GET",
                        "source": "gau",
                        "discovered_at": datetime.utcnow().isoformat(),
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Will be handled by crawler agent

    async def _web_fingerprinting(self):
        """Fingerprint web technologies."""
        target = self.scope.get("allow", ["unknown"])[0]

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["httpx", "-u", target, "-tech-detect", "-json", "-silent"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        techs = data.get("technologies", [])
                        for tech in techs:
                            self.assets["technologies"].append({
                                "name": tech.get("name", "unknown"),
                                "version": tech.get("version"),
                                "confidence": tech.get("confidence", 0.5),
                                "source": "httpx",
                            })
                    except json.JSONDecodeError:
                        pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    async def _fallback_dns_enum(self, target: str):
        """Python-based DNS enumeration fallback."""
        # Placeholder for Python fallback
        pass

    async def _save_assets(self):
        """Save discovered assets."""
        assets_file = self.hunt_dir / "assets.json"
        try:
            with open(assets_file) as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing = {}

        existing.update({
            "hunt_id": self.hunt_id,
            "domains": self.assets["domains"],
            "endpoints": self.assets["endpoints"],
            "parameters": self.assets["parameters"],
            "technologies": self.assets["technologies"],
        })

        with open(assets_file, "w") as f:
            json.dump(existing, f, indent=2)
