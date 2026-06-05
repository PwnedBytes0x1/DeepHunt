#!/usr/bin/env python3
"""
DeepHunt CLI - Main Entry Point
Rich colorized interface optimized for Termux and standard terminals.
"""

import asyncio
import os
import sys
try:
    import ujson as json
except ImportError:
    import json
import click
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

from deephunt import (
    __version__,
    __author__,
    __description__,
    WORKSPACE_DIR,
    IDENTITY_DIR,
    HUNTS_DIR,
    SKILLS_DIR,
    LOGS_DIR,
    is_termux,
    is_android,
)
from deephunt.core.identity import IdentityManager
from deephunt.core.orchestrator import Orchestrator
from deephunt.core.config import ConfigManager
from deephunt.skills.loader import SkillLoader
from deephunt.utils.termux import TermuxUtils
from deephunt.utils.banner import get_banner, get_small_banner
from deephunt.utils.logger import setup_logging

# Rich console for beautiful output
console = Console()

# Color scheme consistent across the app
COLORS = {
    "primary": "cyan",
    "secondary": "magenta",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
    "accent": "bright_cyan",
    "muted": "dim",
}


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.version_option(
    version=__version__,
    prog_name="DeepHunt",
)
@click.option(
    "--workspace",
    "-w",
    type=click.Path(),
    help="Set workspace directory (default: ~/deephunt)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(),
    help="Path to config file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output",
)
@click.pass_context
def cli(ctx, workspace, config, verbose, no_color):
    """DeepHunt - Autonomous AI-Driven Cybersecurity Agent

    Designed for authorized bug bounty hunting and penetration testing.
    Optimized for Termux on Android 14+.

    \b
    Examples:
        dhunt init              Initialize workspace
        dhunt hunt example.com  Start a new hunt
        dhunt skills list       List available skills
        dhunt status            Show hunt status
        dhunt report            Generate report
    """
    ctx.ensure_object(dict)

    if no_color:
        console._color_system = None

    ctx.obj["verbose"] = verbose
    ctx.obj["workspace"] = workspace or str(WORKSPACE_DIR)
    ctx.obj["config"] = config

    if ctx.invoked_subcommand is None:
        # Show banner and help when no command given
        banner = get_banner(no_color=no_color)
        console.print(banner)
        console.print(cli.get_help(ctx))


@cli.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force reinitialize even if workspace exists",
)
@click.option(
    "--minimal",
    "-m",
    is_flag=True,
    help="Minimal setup (skip optional components)",
)
@click.pass_context
def init(ctx, force, minimal):
    """Initialize DeepHunt workspace and configuration."""
    workspace = Path(ctx.obj["workspace"])

    console.print()
    console.print(get_small_banner())
    console.print()

    # Check if already initialized
    if workspace.exists() and not force:
        console.print(
            f"[bold {COLORS['warning']}]Workspace already exists at {workspace}[/bold {COLORS['warning']}]"
        )
        console.print("Use [bold]--force[/bold] to reinitialize.")
        return

    with console.status(f"[bold {COLORS['primary']}]Initializing workspace...[/bold {COLORS['primary']}]"):
        # Create directory structure
        dirs = [
            ".identity",
            "deephunt_hunts",
            "skills/generated",
            "logs",
            "cache",
            "tmp",
            "wordlists",
        ]
        for d in dirs:
            (workspace / d).mkdir(parents=True, exist_ok=True)

        # Create identity files
        identity_mgr = IdentityManager(workspace)
        identity_mgr.create_default_identity()

        # Create config
        config_mgr = ConfigManager(workspace)
        config_mgr.create_default_config()

        # Create skill registry
        skill_loader = SkillLoader(workspace / "skills")
        skill_loader.create_registry()

        # Termux-specific setup
        if is_termux() and not minimal:
            termux = TermuxUtils()
            termux.setup_permissions()

    # Display success
    console.print()
    console.print(
        Panel(
            f"[bold {COLORS['success']}]DeepHunt workspace initialized![/bold {COLORS['success']}]\n\n"
            f"[bold]Location:[/bold] [cyan]{workspace}[/cyan]\n"
            f"[bold]Platform:[/bold] [cyan]{'Termux (Android)' if is_termux() else 'Standard Linux'}[/cyan]",
            title="Setup Complete",
            border_style=COLORS["success"],
            box=box.ROUNDED,
        )
    )

    # Next steps
    table = Table(
        title="Next Steps",
        box=box.ROUNDED,
        border_style=COLORS["primary"],
        show_header=False,
    )
    table.add_column("Step", style="bold")
    table.add_column("Command", style=f"bold {COLORS['accent']}")

    table.add_row("1. Configure identity", "dhunt config edit")
    table.add_row("2. Set API keys", "dhunt config set-apikey <provider> <key>")
    table.add_row("3. List skills", "dhunt skills list")
    table.add_row("4. Start a hunt", "dhunt hunt <target>")

    console.print()
    console.print(table)
    console.print()


@cli.command()
@click.argument("target")
@click.option(
    "--scope",
    "-s",
    multiple=True,
    help="Scope domains (e.g., -s '*.example.com')",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Exclude domains from scope",
)
@click.option(
    "--aggression",
    "-a",
    type=click.Choice(["passive", "recon", "full"], case_sensitive=False),
    default="recon",
    help="Aggression level",
)
@click.option(
    "--budget",
    "-b",
    type=float,
    default=5.0,
    help="Token budget in USD (default: 5.0)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without executing",
)
@click.option(
    "--from-program",
    type=click.Choice(["hackerone", "bugcrowd", "intigriti"]),
    help="Parse scope from bug bounty program URL",
)
@click.pass_context
def hunt(ctx, target, scope, exclude, aggression, budget, dry_run, from_program):
    """Start a new vulnerability hunt against TARGET."""
    workspace = Path(ctx.obj["workspace"])

    console.print()
    console.print(get_small_banner())
    console.print()

    # Validate workspace is initialized
    if not (workspace / ".identity").exists():
        console.print(
            f"[bold {COLORS['error']}]Workspace not initialized![/bold {COLORS['error']}]"
        )
        console.print("Run [bold]dhunt init[/bold] first.")
        sys.exit(1)

    # Build scope
    scope_dict = {
        "allow": list(scope) or [target],
        "deny": list(exclude),
        "target": target,
    }

    # Display hunt configuration
    table = Table(
        title="Hunt Configuration",
        box=box.ROUNDED,
        border_style=COLORS["primary"],
    )
    table.add_column("Setting", style="bold")
    table.add_column("Value", style=f"{COLORS['accent']}")

    table.add_row("Target", target)
    table.add_row("Scope", ", ".join(scope_dict["allow"]))
    table.add_row("Exclusions", ", ".join(scope_dict["deny"]) or "None")
    table.add_row("Aggression", aggression.upper())
    table.add_row("Budget", f"${budget:.2f} USD")
    table.add_row("Workspace", str(workspace))

    console.print()
    console.print(table)

    if dry_run:
        console.print(f"\n[{COLORS['warning']}]Dry run - not executing.[/]")
        return

    # Confirm hunt start
    if not click.confirm(f"\n[?] Start hunt against {target}?", default=True):
        console.print("Hunt cancelled.")
        return

    # Start hunt
    console.print()
    console.print(
        f"[bold {COLORS['primary']}]Starting hunt...[/bold {COLORS['primary']}]"
    )

    try:
        identity_mgr = IdentityManager(workspace)
        identity = identity_mgr.load_identity()

        orchestrator = Orchestrator(
            identity=identity,
            workspace=workspace,
            budget=budget,
        )

        hunt_id = asyncio.run(
            orchestrator.start_hunt(
                target=target,
                scope=scope_dict,
                aggression=aggression,
            )
        )

        console.print()
        console.print(
            Panel(
                f"[bold {COLORS['success']}]Hunt started successfully![/bold {COLORS['success']}]\n\n"
                f"[bold]Hunt ID:[/bold] [cyan]{hunt_id}[/cyan]\n"
                f"[bold]Target:[/bold] [cyan]{target}[/cyan]\n"
                f"[bold]Status:[/bold] [green]Running[/green]\n\n"
                f"Use [bold]dhunt status {hunt_id}[/bold] to check progress\n"
                f"Use [bold]dhunt logs {hunt_id}[/bold] to view logs",
                title="Hunt Started",
                border_style=COLORS["success"],
                box=box.ROUNDED,
            )
        )

    except Exception as e:
        console.print(f"[bold {COLORS['error']}]Error: {e}[/bold {COLORS['error']}]")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument("hunt_id", required=False)
@click.pass_context
def status(ctx, hunt_id):
    """Show status of hunts. If HUNT_ID is provided, show detailed status."""
    workspace = Path(ctx.obj["workspace"])

    console.print()
    console.print(get_small_banner())
    console.print()

    hunts_dir = workspace / "deephunt_hunts"
    if not hunts_dir.exists():
        console.print("[yellow]No hunts directory found.[/yellow]")
        return

    if hunt_id:
        # Show detailed status for specific hunt
        hunt_dir = hunts_dir / hunt_id
        if not hunt_dir.exists():
            console.print(f"[bold {COLORS['error']}]Hunt {hunt_id} not found.[/bold {COLORS['error']}]")
            return

        # Read hunt state
        state_file = hunt_dir / "state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)

            table = Table(
                title=f"Hunt Status: {hunt_id}",
                box=box.ROUNDED,
                border_style=COLORS["primary"],
            )
            table.add_column("Property", style="bold")
            table.add_column("Value", style=COLORS["accent"])

            table.add_row("Target", state.get("target", "Unknown"))
            table.add_row("Status", state.get("status", "Unknown"))
            table.add_row("Started", state.get("started_at", "Unknown"))
            table.add_row("Agents Active", str(len(state.get("agents", []))))
            table.add_row("Findings", str(state.get("findings_count", 0)))
            table.add_row("Budget Used", f"${state.get('budget_used', 0):.3f}")

            console.print(table)
        else:
            console.print(f"[yellow]No state file found for hunt {hunt_id}.[/yellow]")
    else:
        # List all hunts
        hunts = sorted(hunts_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)

        if not hunts:
            console.print("[yellow]No hunts found.[/yellow]")
            return

        table = Table(
            title="Hunt History",
            box=box.ROUNDED,
            border_style=COLORS["primary"],
        )
        table.add_column("Hunt ID", style="bold")
        table.add_column("Target", style=COLORS["accent"])
        table.add_column("Status")
        table.add_column("Started", style="dim")

        for hunt_dir in hunts[:20]:  # Show last 20 hunts
            if not hunt_dir.is_dir():
                continue
            state_file = hunt_dir / "state.json"
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                status_color = {
                    "running": COLORS["success"],
                    "completed": "blue",
                    "paused": COLORS["warning"],
                    "error": COLORS["error"],
                }.get(state.get("status", ""), "white")

                table.add_row(
                    hunt_dir.name[:40],
                    state.get("target", "Unknown")[:30],
                    f"[{status_color}]{state.get('status', 'Unknown').upper()}[/{status_color}]",
                    state.get("started_at", "")[:19],
                )

        console.print(table)


@cli.command()
@click.argument("hunt_id", required=False)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "json", "html"], case_sensitive=False),
    default="markdown",
    help="Report format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path",
)
@click.pass_context
def report(ctx, hunt_id, format, output):
    """Generate report for a hunt."""
    workspace = Path(ctx.obj["workspace"])
    console.print(f"\n[bold {COLORS['primary']}]Generating {format.upper()} report...[/bold {COLORS['primary']}]")
    console.print(f"[yellow]Feature coming in v1.1 - generating placeholder report[/yellow]")


@cli.command()
@click.argument("hunt_id", required=False)
@click.option(
    "--lines",
    "-n",
    type=int,
    default=50,
    help="Number of lines to show",
)
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    help="Follow log output (like tail -f)",
)
@click.pass_context
def logs(ctx, hunt_id, lines, follow):
    """View hunt logs."""
    workspace = Path(ctx.obj["workspace"])

    if hunt_id:
        log_file = workspace / "deephunt_hunts" / hunt_id / "hunt.log"
        if not log_file.exists():
            console.print(f"[bold {COLORS['error']}]No logs found for hunt {hunt_id}.[/bold {COLORS['error']}]")
            return

        console.print(f"\n[bold {COLORS['primary']}]Logs for hunt {hunt_id}:[/bold {COLORS['primary']}]")
        console.print(f"[dim]File: {log_file}[/dim]\n")

        # Read and display logs
        try:
            with open(log_file) as f:
                log_lines = f.readlines()

            for line in log_lines[-lines:]:
                try:
                    entry = json.loads(line)
                    timestamp = entry.get("timestamp", "")[:19]
                    agent = entry.get("agent", "unknown")
                    level = entry.get("level", "INFO")
                    message = entry.get("message", "")

                    level_color = {
                        "INFO": COLORS["info"],
                        "WARNING": COLORS["warning"],
                        "ERROR": COLORS["error"],
                        "SUCCESS": COLORS["success"],
                    }.get(level, "white")

                    console.print(
                        f"[{COLORS['muted']}]{timestamp}[/{COLORS['muted']}] "
                        f"[bold {COLORS['secondary']}]{agent:12}[/{COLORS['secondary']}] "
                        f"[{level_color}]{level:8}[/{level_color}] {message}"
                    )
                except json.JSONDecodeError:
                    console.print(f"[dim]{line.strip()}[/dim]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Log viewing interrupted.[/yellow]")
    else:
        # Show system logs
        log_file = workspace / "logs" / "deephunt.log"
        if log_file.exists():
            console.print(f"[bold {COLORS['primary']}]System logs:[/bold {COLORS['primary']}]")
            with open(log_file) as f:
                for line in f.readlines()[-lines:]:
                    console.print(f"[dim]{line.strip()}[/dim]")
        else:
            console.print("[yellow]No system logs found.[/yellow]")


@cli.group()
@click.pass_context
def skills(ctx):
    """Manage DeepHunt skills and skill sets."""
    pass


@skills.command("list")
@click.option(
    "--category",
    "-c",
    type=click.Choice(["all", "recon", "exploitation", "reporting", "post_exploitation", "network", "payloads", "chaining"]),
    default="all",
    help="Filter by category",
)
@click.option(
    "--detail",
    "-d",
    is_flag=True,
    help="Show detailed skill information",
)
@click.pass_context
def skills_list(ctx, category, detail):
    """List all available skills."""
    workspace = Path(ctx.obj["workspace"])

    # Load from workspace skills (user-created)
    ws_skill_loader = SkillLoader(workspace / "skills")

    # Load bundled skills (shipped with package)
    bundled_dir = Path(__file__).parent / "skills"

    # Also check project root skills/ directory (for development)
    project_skills_dir = Path(__file__).parent.parent / "skills"

    console.print()
    console.print(get_small_banner())
    console.print()

    # Discover all skills from all sources
    all_skills = []
    seen_names = set()

    # Priority 1: Workspace skills (user-created take precedence)
    if ws_skill_loader.skills_dir.exists():
        for skill in ws_skill_loader.discover_skills():
            if skill["name"] not in seen_names:
                seen_names.add(skill["name"])
                skill["source"] = "workspace"
                all_skills.append(skill)

    # Priority 2: Bundled skills in package
    if bundled_dir.exists():
        bundled_loader = SkillLoader(bundled_dir)
        for skill in bundled_loader.discover_skills():
            if skill["name"] not in seen_names:
                seen_names.add(skill["name"])
                skill["source"] = "bundled"
                all_skills.append(skill)

    # Priority 3: Project root skills (development mode)
    if project_skills_dir.exists() and project_skills_dir != bundled_dir:
        project_loader = SkillLoader(project_skills_dir)
        for skill in project_loader.discover_skills():
            if skill["name"] not in seen_names:
                seen_names.add(skill["name"])
                skill["source"] = "project"
                all_skills.append(skill)

    if not all_skills:
        console.print("[yellow]No skills found.[/yellow]")
        console.print("Run [bold]dhunt init[/bold] to create the skills directory.")
        console.print("Create skills in [cyan]~/deephunt/skills/[/cyan] or [cyan]~/deephunt/skills/<category>/[/cyan]")
        return

    if detail:
        # Detailed view
        for skill in all_skills:
            if category != "all" and skill.get("category") != category:
                continue

            panel = Panel(
                f"[bold {COLORS['accent']}]{skill.get('description', 'No description')}[/bold {COLORS['accent']}]\n\n"
                f"[bold]Category:[/bold] {skill.get('category', 'uncategorized')}\n"
                f"[bold]Version:[/bold] {skill.get('version', 'unknown')}\n"
                f"[bold]Author:[/bold] {skill.get('author', 'unknown')}\n"
                f"[bold]Path:[/bold] [dim]{skill.get('path', 'unknown')}[/dim]\n"
                f"[bold]Commands:[/bold] {', '.join(skill.get('commands', []))}",
                title=f"[bold]{skill.get('name', 'Unnamed Skill')}[/bold]",
                border_style=COLORS["primary"],
                box=box.ROUNDED,
            )
            console.print(panel)
            console.print()
    else:
        # Compact table view
        table = Table(
            title=f"Available Skills ({category})",
            box=box.ROUNDED,
            border_style=COLORS["primary"],
        )
        table.add_column("Skill Name", style="bold")
        table.add_column("Category", style=COLORS["secondary"])
        table.add_column("Version", style="dim")
        table.add_column("Description")

        for skill in all_skills:
            if category != "all" and skill.get("category") != category:
                continue

            table.add_row(
                skill.get("name", "Unknown"),
                skill.get("category", "-"),
                skill.get("version", "-"),
                (skill.get("description", "-"))[:50],
            )

        console.print(table)

    console.print(f"\n[dim]Total: {len(all_skills)} skills loaded[/dim]")
    console.print()


@skills.command("show")
@click.argument("skill_name")
@click.pass_context
def skills_show(ctx, skill_name):
    """Show detailed information about a specific skill."""
    workspace = Path(ctx.obj["workspace"])
    skill_loader = SkillLoader(workspace / "skills")

    skill = skill_loader.get_skill(skill_name)
    if not skill:
        console.print(f"[bold {COLORS['error']}]Skill '{skill_name}' not found.[/bold {COLORS['error']}]")
        return

    # Read skill file content
    skill_path = Path(skill.get("path", ""))
    content = ""
    if skill_path.exists():
        content = skill_path.read_text()

    console.print()
    console.print(
        Panel(
            content or "[dim]No content available[/dim]",
            title=f"[bold]{skill.get('name', skill_name)}[/bold]",
            subtitle=f"[dim]{skill.get('category', '')} | v{skill.get('version', '?')}[/dim]",
            border_style=COLORS["primary"],
            box=box.ROUNDED,
        )
    )
    console.print()


@skills.command("load")
@click.argument("skill_name")
@click.pass_context
def skills_load(ctx, skill_name):
    """Load and execute a skill."""
    workspace = Path(ctx.obj["workspace"])
    skill_loader = SkillLoader(workspace / "skills")

    console.print(f"[bold {COLORS['primary']}]Loading skill: {skill_name}...[/bold {COLORS['primary']}]")

    result = skill_loader.execute_skill(skill_name)
    if result:
        console.print(f"[bold {COLORS['success']}]Skill executed successfully![/bold {COLORS['success']}]")
    else:
        console.print(f"[bold {COLORS['error']}]Failed to execute skill.[/bold {COLORS['error']}]")


@cli.group()
@click.pass_context
def config(ctx):
    """Manage DeepHunt configuration."""
    pass


@config.command("show")
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    workspace = Path(ctx.obj["workspace"])
    config_mgr = ConfigManager(workspace)
    config_data = config_mgr.load_config()

    console.print()
    console.print(get_small_banner())
    console.print()

    table = Table(
        title="Configuration",
        box=box.ROUNDED,
        border_style=COLORS["primary"],
    )
    table.add_column("Setting", style="bold")
    table.add_column("Value", style=COLORS["accent"])

    def flatten_dict(d, prefix=""):
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flatten_dict(v, key)
            else:
                # Mask sensitive values
                if any(s in key.lower() for s in ["key", "token", "password", "secret"]):
                    v = "***" if v else "(not set)"
                table.add_row(key, str(v))

    flatten_dict(config_data)
    console.print(table)
    console.print()


@config.command("edit")
@click.pass_context
def config_edit(ctx):
    """Edit configuration in default editor."""
    workspace = Path(ctx.obj["workspace"])
    config_file = workspace / ".identity" / "user.md"

    if not config_file.exists():
        console.print(f"[bold {COLORS['error']}]Config not found. Run dhunt init first.[/bold {COLORS['error']}]")
        return

    click.edit(filename=str(config_file))
    console.print(f"[bold {COLORS['success']}]Configuration updated.[/bold {COLORS['success']}]")


@config.command("set-apikey")
@click.argument("provider")
@click.argument("api_key")
@click.pass_context
def config_set_apikey(ctx, provider, api_key):
    """Set API key for a provider (deepseek, telegram, etc.)."""
    workspace = Path(ctx.obj["workspace"])

    env_file = workspace / ".env"
    env_lines = []

    if env_file.exists():
        with open(env_file) as f:
            env_lines = f.readlines()

    # Update or add the API key
    key_name = f"{provider.upper()}_API_KEY"
    new_line = f"{key_name}={api_key}\n"

    found = False
    for i, line in enumerate(env_lines):
        if line.startswith(f"{key_name}="):
            env_lines[i] = new_line
            found = True
            break

    if not found:
        env_lines.append(new_line)

    with open(env_file, "w") as f:
        f.writelines(env_lines)

    console.print(f"[bold {COLORS['success']}]API key for {provider} set successfully.[/bold {COLORS['success']}]")
    console.print(f"[dim]Stored in: {env_file}[/dim]")


@cli.command()
@click.pass_context
def check(ctx):
    """Run system health check."""
    console.print()
    console.print(get_small_banner())
    console.print()

    console.print(f"[bold {COLORS['primary']}]Running health check...[/bold {COLORS['primary']}]")
    console.print()

    table = Table(
        title="Health Check Results",
        box=box.ROUNDED,
        border_style=COLORS["primary"],
    )
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Details", style="dim")

    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row(
        "Python",
        f"[{COLORS['success']}]OK[/{COLORS['success']}]",
        py_version,
    )

    # Termux detection
    termux_status = "Detected" if is_termux() else "Not detected"
    termux_color = COLORS["success"] if is_termux() else COLORS["warning"]
    table.add_row(
        "Termux",
        f"[{termux_color}]{termux_status}[/{termux_color}]",
        "Android" if is_android() else "Standard",
    )

    # Workspace
    workspace = Path(ctx.obj["workspace"])
    ws_status = "Found" if workspace.exists() else "Not initialized"
    ws_color = COLORS["success"] if workspace.exists() else COLORS["error"]
    table.add_row(
        "Workspace",
        f"[{ws_color}]{ws_status}[/{ws_color}]",
        str(workspace),
    )

    # Key dependencies
    deps = [
        ("click", False),
        ("rich", False),
        ("aiohttp", False),
        ("bs4", True),
        ("yaml", True),
        ("cryptography", False),
    ]

    for dep, is_alt in deps:
        try:
            if is_alt:
                # Try alternative import names
                if dep == "bs4":
                    __import__("bs4")
                elif dep == "yaml":
                    __import__("yaml")
            else:
                __import__(dep)
            table.add_row(dep, f"[{COLORS['success']}]OK[/{COLORS['success']}]", "installed")
        except ImportError:
            table.add_row(dep, f"[{COLORS['error']}]Missing[/{COLORS['error']}]", "pip install required")

    # Disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(workspace.parent)
        free_gb = free / (1024**3)
        free_color = COLORS["success"] if free_gb > 2 else COLORS["warning"] if free_gb > 1 else COLORS["error"]
        table.add_row(
            "Disk Space",
            f"[{free_color}]{free_gb:.1f}GB free[/{free_color}]",
            f"{(used/total)*100:.1f}% used",
        )
    except Exception:
        table.add_row("Disk Space", "[yellow]Unknown[/yellow]", "")

    console.print(table)
    console.print()


# Entry point
def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Interrupted by user.[/bold yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold {COLORS['error']}]Fatal error: {e}[/bold {COLORS['error']}]")
        sys.exit(1)


if __name__ == "__main__":
    main()
