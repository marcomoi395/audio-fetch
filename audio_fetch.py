#!/usr/bin/env python3
"""
Wrapper script - Đảm bảo chạy với Python từ virtual environment
"""

import sys
import os
from pathlib import Path

# Get script directory
script_dir = Path(__file__).parent.absolute()
venv_python = script_dir / "venv" / "bin" / "python"

# Check if we're running from venv
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    # Not in venv, re-execute with venv python
    if venv_python.exists():
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    else:
        print("❌ Virtual environment không tồn tại!")
        print("Chạy: python -m venv venv && ./venv/bin/pip install -r requirements.txt")
        sys.exit(1)

# Now we're in venv, import and run
from audio_downloader import main

if __name__ == '__main__':
    main()
