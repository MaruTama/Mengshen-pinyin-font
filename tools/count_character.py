# -*- coding: utf-8 -*-
#!/usr/bin/env python

# python3 tools/count_character.py ./res/fonts/SawarabiMincho-Regular.ttf

# Note
# cmap を出力
# cat sawarabi_setting.json | jq '.cmap' > test.json

import os
import sys
import json
import argparse
import shell

DIR_TBL = "./res/phonics/unicode_mapping_table"

DIR_TEMP = "./tmp"
TEMP_JSON = "tmp.json"
CMAP_JSON = "cmap.json"


def convert_otf2json(source_font_name):
    temp_json_path = os.path.join(DIR_TEMP, TEMP_JSON)
    cmd = "otfccdump -o {} --pretty {}".format(temp_json_path, source_font_name)
    shell.process(cmd)

# TAMPLATE_MAIN_JSON の cmap table を別ファイルに分離する
def make_new_cmap_table_json():
    temp_json_path = os.path.join(DIR_TEMP, TEMP_JSON)
    cmap_json_path = os.path.join(DIR_TEMP, CMAP_JSON)
    cmd = "cat {} | jq '.cmap' > {}".format(temp_json_path, cmap_json_path)
    shell.process(cmd)

def read_table(file_path):
    hanzi_unicodes = []
    with open(file_path, encoding='utf_8') as read_file:
        for line in read_file:
            # TGSCC and big5
            if "#" in line:
               [_, hanzi] = line.rstrip('\n').split("#")
            # 常用漢字
            else:
                [_, hanzi] = line.rstrip('\n').split(": ")
            hanzi_unicodes.append("{:d}".format(ord(hanzi)))
    return hanzi_unicodes


def count(table_name):
    unicodes_in_table = read_table(table_name)

    abs_dir_name = os.getcwd()
    cmap_json_path = os.path.normpath( os.path.join(abs_dir_name, DIR_TEMP, CMAP_JSON) )
    json_dict = {}
    with open(cmap_json_path, 'r', encoding='utf_8') as f:
        json_dict = json.load(f)
    
    font_has_character_count = 0
    for str_unicode in unicodes_in_table:
        if str_unicode in json_dict:
            font_has_character_count += 1    
    return "  {}/{}".format(font_has_character_count, len(unicodes_in_table))

def count_TGSCC():
    path  = os.path.join(DIR_TBL, "TGSCC-mapping-table.txt")
    print("通用规范汉字表")
    print(count(path))

def count_big5():
    path  = os.path.join(DIR_TBL, "BIG5-mapping-table.txt")
    print("Big5 (大五碼)-2003")
    print(count(path))

def count_joyokanji():
    path  = os.path.join(DIR_TBL, "joyokanjihyo_20101130.txt")
    print("常用漢字表（平成22年内閣告示第2号）")
    print(count(path))

def pickup_cmap(source_font_name):
    convert_otf2json(source_font_name)
    make_new_cmap_table_json()
    temp_json_path = os.path.join(DIR_TEMP, TEMP_JSON)
    os.remove(temp_json_path)

def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Convert OpenType font (.otf/.ttf) to .json ")
    parser.add_argument(
        "source_font_name", metavar="source_font_name", help="Source font name")

    return parser.parse_args(args)

def main(args=None):

    options = parse_args(args)
    # 変換するフォント
    source_font_name = options.source_font_name
    extension = os.path.splitext(source_font_name)[-1]
    if (".otf" == extension or ".ttf" == extension):
        if not os.path.exists(DIR_TEMP):
            os.makedirs(DIR_TEMP)
        pickup_cmap(source_font_name)
        count_TGSCC()
        count_big5()
        count_joyokanji()
    else:
        print("invalid argument:")
        print("  input file is font file (.otf/.ttf) only.")

if __name__ == "__main__":
    sys.exit(main())