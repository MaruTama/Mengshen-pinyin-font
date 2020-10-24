# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import subprocess
import shell
import orjson
import font as ft
import path as p

def main():
    ALPHABET_FOR_PINYIN_JSON = os.path.join(p.DIR_TEMP, "alphabet4pinyin.json")
    # ALPHABET_FOR_PINYIN_JSON = "alphabet4pinyin_test.json"
    TAMPLATE_MAIN_JSON     = os.path.join(p.DIR_TEMP, "template_main.json")
    TAMPLATE_GLYF_JSON     = os.path.join(p.DIR_TEMP, "template_glyf.json")

    PATTERN_ONE_TXT        = os.path.join(p.DIR_OUTPUT, "duoyinzi_pattern_one.txt")
    PATTERN_TWO_JSON       = os.path.join(p.DIR_OUTPUT, "duoyinzi_pattern_two.json")
    EXCEPTION_PATTERN_JSON = os.path.join(p.DIR_OUTPUT, "duoyinzi_exceptional_pattern.json")

    OUTPUT_FONT = os.path.join(p.DIR_OUTPUT, "output.otf")

    font = ft.Font( TAMPLATE_MAIN_JSON, TAMPLATE_GLYF_JSON, ALPHABET_FOR_PINYIN_JSON, \
                    PATTERN_ONE_TXT, PATTERN_TWO_JSON, EXCEPTION_PATTERN_JSON )
    # glyf に追加するpinyin の種類は、mapping_table に完全に依存する
    font.build(OUTPUT_FONT)

if __name__ == "__main__":
    main()

    # error:
    # "12054": "cid11663", ⼖ -> mapping になし
    # cid11664 なし
    # "21305": "cid11665", 匹
    # "22630": "cid13827", 塦 -> mapping になし
    # cid13828 なし
    # "22631": "cid13829", 塧 -> mapping になし
    # 11663 11664 11665 13827 13828 13829
