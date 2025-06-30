# -*- coding: utf-8 -*-
#!/usr/bin/env python

import subprocess
from secure_shell import legacy_shell_process_replacement

def process(cmd=""):
    """
    DEPRECATED: Legacy shell command processor.
    
    This function has been replaced with a secure implementation
    to prevent shell injection vulnerabilities.
    """
    return legacy_shell_process_replacement(cmd)