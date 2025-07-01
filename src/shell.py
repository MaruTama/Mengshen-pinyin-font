# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import annotations

from secure_shell import legacy_shell_process_replacement

def process(cmd: str = "") -> bytes:
    """
    DEPRECATED: Legacy shell command processor.
    
    This function has been replaced with a secure implementation
    to prevent shell injection vulnerabilities.
    """
    # Return bytes for backward compatibility 
    result = legacy_shell_process_replacement(cmd)
    return result.encode('utf-8') if isinstance(result, str) else result