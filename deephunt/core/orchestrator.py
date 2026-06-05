"""
Orchestrator Agent
Manages hunt lifecycle, spawns/kills agents, enforces approval gates.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Optional imports with graceful fallback
try:
    import ujson as json
except ImportError:
    import json

try:
    import psutil
except ImportError:
    psutil = None

from deephunt.core.identity import Identity
from deephunt.core.scope import ScopeFilter
from deephunt.utils.logger import ImmutableLog
from deephunt.utils.termux import TermuxUtils


class TokenBudgetManager:
    """Manages API token budget per hunt."""

    def __init__(self, hunt_id: str, budget_usd: float = 5.0):
        self.hunt_id = hunt_id
        self.budget = budget_usd
        self.spent = 0.0
        self.tokens_used = 0

    async def check_budget(self, estimated_cost: float) -> bool:
        """Check if estimated cost fits within budget."""
        return self.spent + estimated_cost <= self.budget

    async def record_spend(self, cost: float, tokens: int = 0):
        """Record API usage."""
        self.spent += cost
        self.tokens_used += tokens

    def get_status(self) -> Dict[str, Any]:
        """Get budget status."""
        return {
            "budget": self.budget,
            "spent": self.spent,
            "remaining": self.budget - self.spent,
            "tokens_used": self.tokens_used,
            "percent_used": (self.spent / self.budget * 100) if self.budget > 0 else 0,
        }


class Orchestrator:
    """Central orchestrator for managing hunts and agents."""

    def __init__(
        self,
        identity: Identity,
        workspace: Path,
        budget: float = 5.0,
    ):
        self.identity = identity
        self.workspace = Path(workspace)
        self.budget = budget
        self.active_hunts: Dict[str, Any] = {}
        self.agents: Dict[str, Any] = {}
        self.approval_queue: Dict[str, Any] = {}
        self.message_bus = asyncio.Queue()
        self.memory_limit = 1.5 * 1024 * 1024 * 1024  # 1.5GB
        self.termux = TermuxUtils()

    async def start_hunt(
        self,
        target: str,
        scope: Dict[str, Any],
        aggression: str = "recon",
    ) -> str:
        """Start a new hunt.

        Args:
            target: Target domain/URL
            scope: Scope configuration
            aggression: Aggression level

        Returns:
            Hunt ID
        """
        hunt_id = f"{target.replace('.', '_').replace('/', '_')}_{int(time.time())}"
        hunt_dir = self.workspace / "deephunt_hunts" / hunt_id
        hunt_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        for subdir in ["checkpoints", "findings", "reports", "evidence", "cache"]:
            (hunt_dir / subdir).mkdir(exist_ok=True)

        # Initialize immutable log
        log = ImmutableLog(hunt_id, hunt_dir)

        # Initialize budget
        budget_mgr = TokenBudgetManager(hunt_id, self.budget)

        # Create scope filter
        scope_filter = ScopeFilter(
            allow_patterns=scope.get("allow", [target]),
            deny_patterns=scope.get("deny", []),
        )

        # Save scope
        scope_file = hunt_dir / "scope.json"
        with open(scope_file, "w") as f:
            json.dump({
                "target": target,
                "aggression": aggression,
                "scope": scope,
            }, f, indent=2)

        # Create state
        state = {
            "target": target,
            "scope": scope,
            "aggression": aggression,
            "status": "running",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "hunt_id": hunt_id,
            "agents": [],
            "findings_count": 0,
            "budget_used": 0.0,
        }

        state_file = hunt_dir / "state.json"
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

        # Log hunt start
        await asyncio.to_thread(
            log.append,
            "orchestrator",
            "INFO",
            f"Hunt started for {target}",
            {"scope": scope, "aggression": aggression},
        )

        # Store hunt state
        self.active_hunts[hunt_id] = {
            "target": target,
            "scope": scope,
            "scope_filter": scope_filter,
            "log": log,
            "budget": budget_mgr,
            "hunt_dir": hunt_dir,
            "status": "running",
            "aggression": aggression,
        }

        # Save asset structure
        assets = {
            "hunt_id": hunt_id,
            "target": target,
            "scope": scope,
            "domains": [],
            "endpoints": [],
            "parameters": [],
            "technologies": [],
            "scope_violations": [],
        }

        assets_file = hunt_dir / "assets.json"
        with open(assets_file, "w") as f:
            json.dump(assets, f, indent=2)

        # Acquire wake lock on Termux
        if self.termux.is_termux and self.termux.acquire_wake_lock():
            await asyncio.to_thread(
                log.append,
                "orchestrator",
                "INFO",
                "Wake lock acquired for Android",
            )

        return hunt_id

    async def approve_action(self, action_id: str) -> bool:
        """Approve a gated action.

        Args:
            action_id: Action identifier

        Returns:
            True if approved successfully
        """
        if action_id not in self.approval_queue:
            return False

        action = self.approval_queue[action_id]
        action["status"] = "approved"

        await self.message_bus.put({
            "type": "approval_granted",
            "action_id": action_id,
            "hunt_id": action["hunt_id"],
        })

        return True

    async def deny_action(self, action_id: str) -> bool:
        """Deny a gated action.

        Args:
            action_id: Action identifier

        Returns:
            True if denied successfully
        """
        if action_id not in self.approval_queue:
            return False

        action = self.approval_queue[action_id]
        action["status"] = "denied"

        await self.message_bus.put({
            "type": "approval_denied",
            "action_id": action_id,
            "hunt_id": action["hunt_id"],
        })

        return True

    async def request_approval(self, action: Dict[str, Any]) -> str:
        """Request approval for a gated action.

        Args:
            action: Action details

        Returns:
            Action ID
        """
        action_id = action["action_id"]
        action["status"] = "pending"
        action["created_at"] = datetime.utcnow().isoformat() + "Z"
        action["expires_at"] = None  # Set by caller if needed

        self.approval_queue[action_id] = action

        # Send notification on Termux
        if self.termux.is_termux:
            self.termux.send_notification(
                title=f"DeepHunt Approval Required",
                content=f"{action.get('type', 'Unknown action')} on {action.get('target', 'unknown')}",
                priority="max",
            )

        return action_id

    async def check_memory(self):
        """Monitor memory usage and throttle if needed."""
        while True:
            try:
                if psutil:
                    mem_used = psutil.virtual_memory().used
                else:
                    mem_used = self.termux.get_memory_usage()["used"]

                if mem_used > self.memory_limit:
                    await self.message_bus.put({
                        "type": "memory_pressure",
                        "action": "serialize",
                        "used_mb": mem_used / (1024 * 1024),
                    })

                # Check battery on Termux
                if self.termux.is_termux:
                    battery = self.termux.get_battery_status()
                    if battery.get("percentage", 100) < 15:
                        await self.message_bus.put({
                            "type": "battery_low",
                            "percentage": battery["percentage"],
                            "action": "pause",
                        })

                    thermal = self.termux.get_thermal_status()
                    if thermal.get("throttled", False):
                        await self.message_bus.put({
                            "type": "thermal_throttle",
                            "temperature": thermal["max_temperature"],
                            "action": "throttle",
                        })

                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)

    async def stop_hunt(self, hunt_id: str) -> bool:
        """Gracefully stop a hunt.

        Args:
            hunt_id: Hunt to stop

        Returns:
            True if stopped successfully
        """
        if hunt_id not in self.active_hunts:
            return False

        hunt = self.active_hunts[hunt_id]
        hunt["status"] = "stopped"

        # Update state file
        state_file = hunt["hunt_dir"] / "state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            state["status"] = "stopped"
            state["stopped_at"] = datetime.utcnow().isoformat() + "Z"
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)

        # Release wake lock
        if self.termux.is_termux:
            self.termux.release_wake_lock()

        # Log stop
        await asyncio.to_thread(
            hunt["log"].append,
            "orchestrator",
            "INFO",
            f"Hunt {hunt_id} stopped",
        )

        return True

    def get_hunt_status(self, hunt_id: str) -> Optional[Dict[str, Any]]:
        """Get current hunt status.

        Args:
            hunt_id: Hunt identifier

        Returns:
            Status dictionary or None
        """
        if hunt_id not in self.active_hunts:
            return None

        hunt = self.active_hunts[hunt_id]
        return {
            "hunt_id": hunt_id,
            "target": hunt["target"],
            "status": hunt["status"],
            "budget": hunt["budget"].get_status(),
            "pending_approvals": len([
                a for a in self.approval_queue.values()
                if a["hunt_id"] == hunt_id and a["status"] == "pending"
            ]),
        }
