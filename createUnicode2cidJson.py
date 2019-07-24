#!/usr/bin/env python
import json
import sys
import os
import argparse
from fontTools.ttLib import TTFont

# json の名前
UNICODE_TO_CID_JSON = "unicode-cid-mapping.json"
DIR_JSN = "./jsons"

# fontのunicodeとcidの対応表を取得する
def getUnicode2CidJson(cmap):
    dict_cid_mapping = {}

    for c in cmap:
        int_unicode = int(c)
        glyph_name = cmap[c]
        # 2byte 以上のときは, 表示桁を 5 桁にする
        str_unicode = "U+{:04X}".format(int_unicode) if int_unicode < 65536 else "U+{:05X}".format(int_unicode)
        dict_cid_mapping.update( {str_unicode: glyph_name} )

    # json 書き出し
    f = open(os.path.join(DIR_JSN,UNICODE_TO_CID_JSON), "w")
    json.dump(dict_cid_mapping, f, ensure_ascii=False, indent=3, sort_keys=True, separators=(',', ': '))


def main(args=None):
    parser = argparse.ArgumentParser(description='this script is to convert ttf to png')
    parser.add_argument('font_name')
    arg = parser.parse_args(args)
    font = TTFont(arg.font_name)
    cmap = font.getBestCmap()
    getUnicode2CidJson(cmap)

if __name__ == '__main__':
    sys.exit(main())
