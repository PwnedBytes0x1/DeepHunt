"""
Banner generation for DeepHunt CLI
Rich, colorized banners for Termux and standard terminals.
"""

from rich.text import Text
from rich.panel import Panel
from rich import box

# Full DeepHunt ASCII Art Banner
BANNER_ART = """
    ██████╗ ███████╗███████╗██████╗ ██╗  ██╗██╗   ██╗███╗   ██╗████████╗
    ██╔══██╗██╔════╝██╔════╝██╔══██╗██║  ██║██║   ██║████╗  ██║╚══██╔══╝
    ██║  ██║█████╗  █████╗  ██████╔╝███████║██║   ██║██╔██╗ ██║   ██║   
    ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║   ██║   
    ██████╔╝███████╗███████╗██║     ██║  ██║╚██████╔╝██║ ╚████║   ██║   
    ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   
"""

# Compact banner for repeated use
SMALL_BANNER = """
 ╔╦╗┌─┐┌─┐┌─┐┬ ┬┌┐┌┌┬┐
  ║║├┤ ├┤ ├┤ ├─┤│││ │  
 ═╩╝└─┘└  └─┘┴ ┴┘└┘ ┴  
"""

# Tagline
TAGLINE = "Autonomous AI-Driven Cybersecurity Agent"
VERSION_TAG = "v1.0.0"


def get_banner(no_color: bool = False) -> Panel:
    """Get the full DeepHunt banner.
    
    Args:
        no_color: Disable colors
        
    Returns:
        Rich Panel with the banner
    """
    if no_color:
        content = f"{BANNER_ART}\n    {TAGLINE} | {VERSION_TAG}"
        return Panel(content, border_style="white")

    # Colorized version
    banner_text = Text()
    
    # Add banner art with gradient-like coloring
    lines = BANNER_ART.strip("\n").split("\n")
    colors = ["bright_cyan", "cyan", "blue", "blue_violet", "purple", "magenta"]
    
    for i, line in enumerate(lines):
        color = colors[min(i, len(colors) - 1)]
        banner_text.append(line, style=f"bold {color}")
        if i < len(lines) - 1:
            banner_text.append("\n")

    # Add tagline
    banner_text.append("\n\n    ")
    banner_text.append(TAGLINE, style="italic bright_white")
    banner_text.append("  |  ", style="dim")
    banner_text.append(VERSION_TAG, style="bold yellow")

    # Add termux indicator if applicable
    import os
    if "TERMUX_VERSION" in os.environ:
        banner_text.append("  [TERMUX]", style="bold green")

    return Panel(
        banner_text,
        border_style="cyan",
        box=box.ROUNDED,
        padding=(0, 2),
    )


def get_small_banner() -> Panel:
    """Get a compact banner for repeated display.
    
    Returns:
        Rich Panel with small banner
    """
    text = Text()
    
    lines = SMALL_BANNER.strip("\n").split("\n")
    colors = ["bright_cyan", "cyan", "blue"]
    
    for i, line in enumerate(lines):
        color = colors[min(i, len(colors) - 1)]
        text.append(line, style=f"bold {color}")
        if i < len(lines) - 1:
            text.append("\n")

    text.append(f"  {TAGLINE}", style="dim italic")

    return Panel(
        text,
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(0, 1),
    )


def get_status_banner(status: str, hunt_id: str) -> Panel:
    """Get a status banner for hunt display.
    
    Args:
        status: Hunt status (running, paused, completed, etc.)
        hunt_id: Hunt identifier
        
    Returns:
        Rich Panel with status info
    """
    status_colors = {
        "running": "green",
        "paused": "yellow",
        "completed": "blue",
        "error": "red",
        "stalled": "orange3",
    }
    color = status_colors.get(status.lower(), "white")

    text = Text()
    text.append("Hunt: ", style="bold")
    text.append(hunt_id, style="cyan")
    text.append("  Status: ", style="bold")
    text.append(status.upper(), style=f"bold {color}")

    return Panel(text, border_style=color, box=box.ROUNDED)
