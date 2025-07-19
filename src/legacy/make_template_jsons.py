# -*- coding: utf-8 -*-
#!/usr/bin/env python

# python3 src/make_template_jsons.py ./res/fonts/SourceHanSerifCN-Regular.ttf
# python3 sec/make_template_jsons.py ./res/fonts/SawarabiMincho-Regular.ttf

# Note
# glyf を出力
# cat sawarabi_setting.json | jq '.glyf' > test.json
# キーを出力
# cat sawarabi_setting.json | jq '.glyf|keys' > test.json

# [jq で特定条件にマッチする要素を置換する](https://tamakiii.hatenablog.com/entry/2019/11/21/001343)
# [シェル芸で使いたい jqイディオム](https://qiita.com/nmrmsys/items/5b4a4bd2e3909db161b1#json%E3%81%AE%E7%BD%AE%E6%8F%9B2)
# `glyf[].contours` を `[]` に置換する. これをビルドするとグリフデータが空のフォントができる。
# $ cat sawarabi_setting.json | jq '.glyf |= map_values( (select(1).contours |= []) // .)' > test.json


import argparse
import os
import subprocess
import sys

import path as p
import shell

TAMPLATE_TEMP_JSON = "template_temp.json"
TAMPLATE_MAIN_JSON = "template_main.json"
TAMPLATE_GLYF_JSON = "template_glyf.json"


def convert_otf2json(source_font_name):
    template_temp_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_TEMP_JSON)
    cmd = "otfccdump -o {} --pretty {}".format(
        template_temp_json_path, source_font_name
    )
    shell.process(cmd)


# TAMPLATE_MAIN_JSON の glyf table を別ファイルに分離する
def make_new_glyf_table_json():
    template_temp_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_TEMP_JSON)
    template_glyf_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_GLYF_JSON)
    cmd = "cat {} | jq '.glyf' > {}".format(
        template_temp_json_path, template_glyf_json_path
    )
    shell.process(cmd)


# TAMPLATE_MAIN_JSON の glyf のグリフ情報（contours）を削除する。これをビルドすると空のフォントができる。
def delete_glyf_table_on_main_json():
    template_temp_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_TEMP_JSON)
    template_main_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_MAIN_JSON)
    cmd = "cat {} | jq '.glyf |= map_values( (select(1).contours |= []) // .)' > {}".format(
        template_temp_json_path, template_main_json_path
    )
    shell.process(cmd)


def make_template(source_font_name):
    convert_otf2json(source_font_name)
    make_new_glyf_table_json()
    delete_glyf_table_on_main_json()

    template_temp_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_TEMP_JSON)
    os.remove(template_temp_json_path)


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Convert OpenType font (.otf/.ttf) to .json "
    )
    parser.add_argument(
        "source_font_name", metavar="source_font_name", help="Source font name"
    )

    return parser.parse_args(args)


def main(args=None):

    options = parse_args(args)
    # 変換するフォント
    source_font_name = options.source_font_name
    extension = os.path.splitext(source_font_name)[-1]
    if ".otf" == extension or ".ttf" == extension:
        if not os.path.exists(p.DIR_TEMP):
            os.makedirs(p.DIR_TEMP)
        make_template(source_font_name)
    else:
        print("invalid argument:")
        print("  input file is font file (.otf/.ttf) only.")


if __name__ == "__main__":
    sys.exit(main())
