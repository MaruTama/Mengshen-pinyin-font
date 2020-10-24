# -*- coding: utf-8 -*-
#!/usr/bin/env python

# time python3 src/main.py

import os
import subprocess
import shell
import orjson
import font as ft
import path as p

def main():
    ALPHABET_FOR_PINYIN_JSON = os.path.join(p.DIR_TEMP, "alphabet4pinyin.json")
    TAMPLATE_MAIN_JSON       = os.path.join(p.DIR_TEMP, "template_main.json")
    TAMPLATE_GLYF_JSON       = os.path.join(p.DIR_TEMP, "template_glyf.json")

    PATTERN_ONE_TXT          = os.path.join(p.DIR_OUTPUT, "duoyinzi_pattern_one.txt")
    PATTERN_TWO_JSON         = os.path.join(p.DIR_OUTPUT, "duoyinzi_pattern_two.json")
    EXCEPTION_PATTERN_JSON   = os.path.join(p.DIR_OUTPUT, "duoyinzi_exceptional_pattern.json")

    OUTPUT_FONT = os.path.join(p.DIR_OUTPUT, "output.otf")

    font = ft.Font( TAMPLATE_MAIN_JSON, TAMPLATE_GLYF_JSON, ALPHABET_FOR_PINYIN_JSON, \
                    PATTERN_ONE_TXT, PATTERN_TWO_JSON, EXCEPTION_PATTERN_JSON )
    # glyf に追加するpinyin の種類は、mapping_table に完全に依存する
    font.build(OUTPUT_FONT)

if __name__ == "__main__":
    main()