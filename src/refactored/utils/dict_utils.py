# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import annotations

from typing import Dict, Any


# [階層構造のあるdictをupdateする](https://www.greptips.com/posts/1242/)
def deepupdate(dict_base: Dict[str, Any], other: Dict[str, Any]) -> None:
    """Deep update nested dictionary structure."""
    for k, v in other.items():
        if isinstance(v, dict) and k in dict_base:
            deepupdate(dict_base[k], v)
        else:
            dict_base[k] = v
