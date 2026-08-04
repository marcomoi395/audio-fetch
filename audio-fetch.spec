# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Audio Fetch desktop application.

This spec file bundles the FastAPI server, Qt GUI, and all dependencies
into a standalone executable for Linux/Windows.

Build command:
    pyinstaller audio-fetch.spec --clean

Output:
    dist/audio-fetch (Linux) or dist/audio-fetch.exe (Windows)
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all template and static files
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('config/default_config.json', 'config'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    # PySide6 modules
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebChannel',
    
    # FastAPI and Starlette
    'fastapi',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.responses',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    
    # yt-dlp and dependencies
    'yt_dlp',
    'yt_dlp.extractor',
    'yt_dlp.postprocessor',
    'yt_dlp.downloader',
    'yt_dlp_plugins',
    'bgutil_ytdlp_pot_provider',
    'yt_dlp_ejs',
    
    # HTTP and async libraries
    'httpx',
    'h11',
    'h2',
    'anyio',
    'sniffio',
    'certifi',
    
    # Template engine
    'jinja2',
    'jinja2.ext',
    
    # Other utilities
    'aiofiles',
    'dotenv',
    'cryptography',
    
    # Desktop-specific
    'secretstorage',  # Linux credential storage
]

# Collect all submodules for complex packages
hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('yt_dlp')
hiddenimports += collect_submodules('fastapi')

# Collect data files from packages
datas += collect_data_files('yt_dlp')
datas += collect_data_files('certifi')

a = Analysis(
    ['desktop_main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test and development tools
        'pytest',
        'pytest_asyncio',
        'pytest_cov',
        'pytest_playwright',
        'mypy',
        'ruff',
        
        # Exclude unnecessary GUI backends
        'matplotlib',
        'PIL',
        'tkinter',
        
        # Exclude unnecessary libraries
        'IPython',
        'jupyter',
        'notebook',
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
    name='audio-fetch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False on Windows to hide console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
)

# For one-folder distribution (alternative to one-file above):
# Uncomment the following to create a folder distribution instead
# This is faster to start and easier to debug

# exe = EXE(
#     pyz,
#     a.scripts,
#     [],
#     exclude_binaries=True,
#     name='audio-fetch',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     console=True,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
# )
# 
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='audio-fetch',
# )
