# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import annotations

import sys
from pathlib import Path

# Add src directory to path for secure_shell import
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from secure_shell import legacy_shell_process_replacement

def process(cmd: str = "") -> str:
    """
    DEPRECATED: Legacy shell command processor.
    
    This function has been replaced with a secure implementation
    to prevent shell injection vulnerabilities.
    
    Args:
        cmd: Command string to execute safely
        
    Returns:
        Command output as string
    """
    return legacy_shell_process_replacement(cmd)
