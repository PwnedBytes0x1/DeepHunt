# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for building DeepHunt binary.

Usage:
    pyinstaller scripts/deephunt.spec --clean --noconfirm

Or use make:
    make binary
"""

import sys
from pathlib import Path

# Project root
project_root = Path(__file__).parent.parent

block_cipher = None

a = Analysis(
    [str(project_root / 'deephunt' / 'cli.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include bundled skills
        (str(project_root / 'deephunt' / 'skills'), 'deephunt/skills'),
        # Include identity templates (optional, can be generated at runtime)
    ],
    hiddenimports=[
        'click',
        'rich',
        'rich.console',
        'rich.panel',
        'rich.table',
        'rich.text',
        'rich.columns',
        'rich.box',
        'aiohttp',
        'aiofiles',
        'bs4',
        'lxml',
        'yaml',
        'cryptography',
        'psutil',
        'PIL',
        'pkg_resources',
        # Ensure all agents can be imported
        'deephunt.agents.recon_agent',
        'deephunt.agents.vuln_id_agent',
        'deephunt.agents.skill_builder_agent',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy/unused packages to reduce binary size
        'matplotlib',
        'numpy',
        'pandas',
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'pydoc',
        'test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='dhunt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Terminal metadata
    entitlements_file=None,
)
