"""
DeepHunt Background Runner
Keeps DeepHunt running persistently in Termux and handles Telegram commands.
"""

import os
import sys
import signal
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Global state
is_running = True
telegram_bot = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global is_running
    print("\n[DeepHunt] Shutdown signal received, stopping...")
    is_running = False


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


class TelegramRunner:
    """Telegram bot runner for remote command execution."""
    
    def __init__(self, bot_token: str, workspace: Path):
        self.bot_token = bot_token
        self.workspace = workspace
        self.offset = 0
        self.bot_processed = set()  # Track processed update IDs
        self.commands = {
            "/start": self.cmd_start,
            "/help": self.cmd_help,
            "/status": self.cmd_status,
            "/hunt": self.cmd_hunt,
            "/stop": self.cmd_stop,
            "/logs": self.cmd_logs,
            "/stats": self.cmd_stats,
        }
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown"):
        """Send message via Telegram Bot API."""
        import httpx
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"[DeepHunt] Failed to send Telegram message: {e}")
    
    async def get_updates(self) -> list:
        """Fetch updates from Telegram Bot API."""
        import httpx
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        params = {
            "offset": self.offset,
            "timeout": 30,
            "allowed_updates": "message",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=35)
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
        except Exception as e:
            print(f"[DeepHunt] Failed to get Telegram updates: {e}")
        return []
    
    async def process_update(self, update: Dict[str, Any]):
        """Process a single Telegram update."""
        if "message" not in update:
            return
        
        message = update["message"]
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        update_id = update.get("update_id")
        
        if update_id in self.bot_processed:
            return
        self.bot_processed.add(update_id)
        self.offset = update_id + 1
        
        if not text:
            return
        
        # Parse command
        command = text.strip().split()[0].lower()
        
        if command in self.commands:
            await self.commands[command](chat_id, text)
        else:
            await self.send_message(chat_id, 
                "🤖 Unknown command. Send /help for available commands.")
    
    async def cmd_start(self, chat_id: int, text: str):
        """Handle /start command."""
        await self.send_message(chat_id,
            "🛡️ *DeepHunt Active*\n\n"
            "DeepHunt is now running and ready to receive commands.\n\n"
            "Send /help to see available commands.")
    
    async def cmd_help(self, chat_id: int, text: str):
        """Handle /help command."""
        await self.send_message(chat_id,
            "*📚 DeepHunt Commands*\n\n"
            "`/status` - Show current hunt status\n"
            "`/hunt <target>` - Start a new hunt\n"
            "`/stop` - Stop current hunt\n"
            "`/logs [lines]` - Get recent logs\n"
            "`/stats` - Show statistics\n"
            "`/help` - Show this help message")
    
    async def cmd_status(self, chat_id: int, text: str):
        """Handle /status command."""
        # Check if orchestrator is running
        status_file = self.workspace / ".hunt" / "status.json"
        if status_file.exists():
            import json
            with open(status_file) as f:
                status = json.load(f)
            await self.send_message(chat_id,
                f"📊 *Hunt Status*\n\n"
                f"Target: `{status.get('target', 'None')}`\n"
                f"Status: {status.get('status', 'Unknown')}\n"
                f"Findings: {status.get('findings_count', 0)}\n"
                f"Started: {status.get('started_at', 'N/A')}")
        else:
            await self.send_message(chat_id,
                "📊 *Hunt Status*\n\nNo active hunt. Use /hunt <target> to start one.")
    
    async def cmd_hunt(self, chat_id: int, text: str):
        """Handle /hunt command."""
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await self.send_message(chat_id,
                "⚠️ Usage: `/hunt example.com`")
            return
        
        target = parts[1].strip()
        await self.send_message(chat_id,
            f"🎯 Starting hunt on `{target}`...\n"
            "This may take a few moments. Use /status to check progress.")
        
        # Start hunt in background
        try:
            from deephunt.core.orchestrator import Orchestrator
            from deephunt.core.identity import IdentityManager
            
            identity = IdentityManager(self.workspace / "identity")
            orchestrator = Orchestrator(
                workspace=self.workspace,
                identity=identity,
                telegram_token=self.bot_token,
                telegram_chat_id=str(chat_id),
            )
            await orchestrator.start_hunt(target)
            await self.send_message(chat_id,
                f"✅ Hunt started on `{target}`\n"
                "Use /status to monitor progress.")
        except Exception as e:
            await self.send_message(chat_id,
                f"❌ Failed to start hunt: {str(e)}")
    
    async def cmd_stop(self, chat_id: int, text: str):
        """Handle /stop command."""
        await self.send_message(chat_id,
            "🛑 Stopping hunt...")
        # Signal orchestrator to stop
        try:
            # Create stop signal file
            stop_file = self.workspace / ".hunt" / "stop"
            stop_file.touch()
            await self.send_message(chat_id,
                "✅ Stop signal sent. Hunt will end gracefully.")
        except Exception as e:
            await self.send_message(chat_id,
                f"❌ Error: {str(e)}")
    
    async def cmd_logs(self, chat_id: int, text: str):
        """Handle /logs command."""
        parts = text.split()
        lines = 20
        if len(parts) > 1:
            try:
                lines = int(parts[1])
            except ValueError:
                pass
        
        log_file = self.workspace / "logs" / "deephunt.log"
        if log_file.exists():
            with open(log_file) as f:
                all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            logs = "".join(recent)
            if len(logs) > 4000:
                logs = logs[-4000:]
            await self.send_message(chat_id, f"📋 *Recent Logs*\n\n```\n{logs}\n```")
        else:
            await self.send_message(chat_id,
                "📋 No logs found.")
    
    async def cmd_stats(self, chat_id: int, text: str):
        """Handle /stats command."""
        from deephunt.utils.logger import ImmutableLog
        
        logs = ImmutableLog(self.workspace / "logs")
        stats = logs.get_stats()
        
        await self.send_message(chat_id,
            f"📈 *DeepHunt Statistics*\n\n"
            f"Total Hunts: {stats.get('total_hunts', 0)}\n"
            f"Total Findings: {stats.get('total_findings', 0)}\n"
            f"API Calls: {stats.get('total_api_calls', 0)}\n"
            f"Budget Used: ${stats.get('budget_used', 0):.4f}")
    
    async def get_me(self) -> Dict[str, Any]:
        """Get bot info from Telegram."""
        import httpx
        url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                data = response.json()
                if data.get("ok"):
                    return data.get("result", {})
        except Exception as e:
            print(f"[DeepHunt] Failed to get bot info: {e}")
        return {}
    
    async def run(self):
        """Main polling loop."""
        print("[DeepHunt] Telegram bot started. Waiting for commands...")
        
        # Get bot info and send startup message
        me = await self.get_me()
        bot_id = me.get("id", 0)
        if bot_id:
            await self.send_message(bot_id, "🛡️ DeepHunt is now running!")
        
        while is_running:
            try:
                updates = await self.get_updates()
                for update in updates:
                    await self.process_update(update)
                # Small delay to prevent tight loop
                await asyncio.sleep(1)
            except Exception as e:
                print(f"[DeepHunt] Error in Telegram loop: {e}")
                await asyncio.sleep(5)


def keep_termux_alive():
    """Keep Termux process alive using termux-specific methods."""
    # Method 1: Use termux-wake-lock if available
    if os.path.exists("/system/bin/termux-wake-lock"):
        os.system("termux-wake-lock >/dev/null 2>&1 &")
        print("[DeepHunt] Wake lock acquired")
    
    # Method 2: Create a status file to indicate running
    workspace = Path(os.environ.get("WORKSPACE_DIR", str(Path.home() / "deephunt")))
    pid_file = workspace / ".deephunt" / "running.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))
    
    return pid_file


def run_background(workspace: Path, telegram_token: Optional[str] = None):
    """
    Run DeepHunt in background mode.
    
    Keeps the process alive and responds to Telegram commands.
    """
    global is_running, telegram_bot
    
    print("=" * 50)
    print("  DeepHunt Background Runner")
    print("=" * 50)
    print()
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Keep Termux alive
    pid_file = keep_termux_alive()
    print(f"[DeepHunt] Running in background (PID: {os.getpid()})")
    print(f"[DeepHunt] PID file: {pid_file}")
    print()
    
    if not telegram_token:
        # Load from environment
        env_file = workspace / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    telegram_token = line.split("=", 1)[1].strip().strip('"')
                    break
    
    if telegram_token:
        print("[DeepHunt] Telegram integration enabled")
        print("[DeepHunt] Send /help to the bot for available commands")
        print()
        
        telegram_bot = TelegramRunner(telegram_token, workspace)
        asyncio.run(telegram_bot.run())
    else:
        print("[DeepHunt] Telegram not configured")
        print("[DeepHunt] Set TELEGRAM_BOT_TOKEN to enable remote commands")
        print()
        
        # Just keep alive without Telegram
        print("[DeepHunt] Keeping process alive... Press Ctrl+C to stop")
        while is_running:
            import time
            time.sleep(10)
            print(f"[DeepHunt] Still running... ({datetime.now().strftime('%H:%M:%S')})")
    
    # Cleanup
    if pid_file.exists():
        pid_file.unlink()
    print("[DeepHunt] Background runner stopped")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DeepHunt Background Runner")
    parser.add_argument("-w", "--workspace", type=Path, default=Path.home() / "deephunt",
        help="Workspace directory")
    parser.add_argument("--telegram-token", help="Telegram bot token")
    args = parser.parse_args()
    
    run_background(args.workspace, args.telegram_token)