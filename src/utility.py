# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import orjson
import pinyin_getter as pg
import path as p

SIMPLED_ALPHABET = {
    "a":"a", "ā":"a1", "á":"a2", "ǎ":"a3", "à":"a4",
    "b":"b",
    "c":"c",
    "d":"d",
    "e":"e", "ē":"e1", "é":"e2", "ě":"e3", "è":"e4",
    "f":"f",
    "g":"g",
    "h":"h",
    "i":"i", "ī":"i1", "í":"i2", "ǐ":"i3", "ì":"i4",
    "j":"j",
    "k":"k",
    "l":"l",
    "m":"m", "m̄":"m1", "ḿ":"m2", "m̀":"m4",
    "n":"n",           "ń":"n2", "ň":"n3", "ǹ":"n4",
    "o":"o", "ō":"o1", "ó":"o2", "ǒ":"o3", "ò":"o4",
    "p":"p",
    "q":"q",
    "r":"r",
    "s":"s",
    "t":"t",
    "u":"u", "ū":"u1", "ú":"u2" ,"ǔ":"u3", "ù":"u4", "ü":"v", "ǖ":"v1", "ǘ":"v2", "ǚ":"v3", "ǜ":"v4",
    "v":"v",
    "w":"w",
    "x":"x",
    "y":"y",
    "z":"z"
}

cmap_table = {}
PINYIN_MAPPING_TABLE = pg.get_pinyin_table_with_mapping_table()

def get_cmap_table():
    TAMPLATE_MAIN_JSON = os.path.join(p.DIR_TEMP, "template_main.json")
    with open(TAMPLATE_MAIN_JSON, "rb") as read_file:
        marged_font = orjson.loads(read_file.read())
    cmap_table = marged_font["cmap"]

# ピンイン表記の簡略化、e.g.: wěi -> we3i
def simplification_pronunciation(pronunciation):
    return  "".join( [SIMPLED_ALPHABET[c] for c in pronunciation] )

# ピンインが一つだけの漢字をすべて取得する
def get_has_single_pinyin_hanzi():
    return [(hanzi, pinyins) for hanzi, pinyins in PINYIN_MAPPING_TABLE.items() if 1 == len(pinyins)]

# ピンインが2つ以上の漢字をすべて取得する
def get_has_multiple_pinyin_hanzi():
    return [(hanzi, pinyins) for hanzi, pinyins in PINYIN_MAPPING_TABLE.items() if 1 < len(pinyins)]

# 漢字から cid を取得する
def convert_str_hanzi_2_cid(str_hanzi):
    if len(cmap_table) == 0:
        get_cmap_table()
    return cmap_table[ str(ord(str_hanzi)) ]

# [階層構造のあるdictをupdateする](https://www.greptips.com/posts/1242/)
def deepupdate(dict_base, other):
    for k, v in other.items():
        if isinstance(v, dict) and k in dict_base:
            deepupdate(dict_base[k], v)
        else:
            dict_base[k] = v