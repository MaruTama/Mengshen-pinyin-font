# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import annotations

import os
import orjson
from functools import lru_cache
from typing import Dict

from refactored.config.paths import DIR_TEMP


cmap_table: Dict[str, str] = {}


def get_cmap_table() -> None:
    """Load cmap table from template_main.json."""
    global cmap_table
    TAMPLATE_MAIN_JSON = os.path.join(DIR_TEMP, "template_main.json")
    with open(TAMPLATE_MAIN_JSON, "rb") as read_file:
        marged_font = orjson.loads(read_file.read())
    cmap_table = marged_font["cmap"]


# 漢字から cid を取得する
@lru_cache(maxsize=2048)
def convert_str_hanzi_2_cid(str_hanzi: str) -> str:
    """Convert hanzi character to CID with caching for performance."""
    if len(cmap_table) == 0:
        get_cmap_table()
    return cmap_table[ str(ord(str_hanzi)) ]
