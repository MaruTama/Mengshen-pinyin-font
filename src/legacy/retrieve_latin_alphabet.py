# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import sys
import argparse
import subprocess
import json
import utility
import path as p

# できた
# cat alphabet4pinyin.json | jq '.glyf | with_entries(select(.key|match("^a$|^b$")))' > out.json

# 一文字なら、これの方がわかりやすい。置換のときに使えるかな
# cat alphabet4pinyin.json | jq '.glyf | with_entries(select(.key == "a"))' > out.json

"""
指定された任意のフォントからピンイン表示のために利用するグリフを取得する
グリフ名はcid のままだとわかりづらいので、unicode に修正する
"""

ALPHABET_FOR_PINYIN_JSON = "alphabet4pinyin.json"
OUTPUT_JSON = "output_for_pinyin.json"

# 呣 m̀, 嘸 m̄ を使うが、これは unicode ではないので除外する。グリフが収録されていない事が多い。
ALPHABET = ["a","ā","á","ǎ","à","b","c","d","e","ē","é","ě","è","f","g","h","i","ī","í","ǐ","ì","j","k","l","m","ḿ","n","ń","ň","ǹ","o","ō","ó","ǒ","ò","p","q","r","s","t","u","ū","ú","ǔ","ù","ü","ǖ","ǘ","ǚ","ǜ","v","w","x","y","z"]

UNICODE_ALPHABET = [ord(c) for c in ALPHABET]

def process_shell(cmd=""):
    completed_process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # print(f'returncode: {completed_process.returncode},stdout: {completed_process.stdout},stderr: {completed_process.stderr}')
    if b'' != completed_process.stderr:
        raise Exception(completed_process.stderr)
    return completed_process.stdout

def convert_otf2json(source_font_name, output_json):
    cmd = f"otfccdump -o {output_json} --pretty {source_font_name}"
    try:
        process_shell(cmd)
    except Exception as e:
        print(e)

# cmap の大きさなら、全部取得しても 65536 程度だから、フィルターしなくてもいいな
def get_cmap_table(source_font_json):
    cmd = f"cat {source_font_json} | jq '.cmap'"
    try:
        cmap_table = json.loads(process_shell(cmd))
    except Exception as e:
        print(e)
        return None
    return cmap_table

def expand_pattern_list2match_pattern(alphabet_list):
    match_pattern = ""
    for c in alphabet_list:
        match_pattern += f"^{c}$|" if alphabet_list[-1] != c else f"^{c}$"
    return f' "{match_pattern}" '

def get_reversed_cmap_table(output_json):
    cmap_table = get_cmap_table(output_json)
    if cmap_table is None:
        return {}

    reversed_cmap_table = {}
    for ucode in UNICODE_ALPHABET:
        # Check if ucode exists in cmap_table
        if str(ucode) in cmap_table:
            cid = cmap_table[str(ucode)]
            reversed_cmap_table.update({cid: "py_alphablet_" + utility.SIMPLED_ALPHABET[chr(ucode)]})

    return reversed_cmap_table

def rename_cid_of_alphabet_for_pinyin(alphabet_glyf4pinyin_json, output_json):
    with open(alphabet_glyf4pinyin_json, mode='r', encoding='utf-8') as read_file:
        glyf_json = json.load(read_file)
    
    reversed_cmap_table = get_reversed_cmap_table(output_json)

    new_glyf_json = {}
    for cid, glyf_data in glyf_json.items():
        if cid in reversed_cmap_table:
            new_glyf_json.update({reversed_cmap_table[cid]: glyf_data})
    
    with open(alphabet_glyf4pinyin_json, mode='w', encoding='utf-8') as write_file:
        json.dump(new_glyf_json, write_file, indent=4, ensure_ascii=False)

def make_alphabet_glyf_json(source_font_name, style):
    output_json = os.path.join(p.DIR_TEMP, f"output_for_pinyin_{style}.json")
    convert_otf2json(source_font_name, output_json)
    
    cmap_table = get_cmap_table(output_json)
    if cmap_table is None:
        print("Failed to get cmap table.")
        return

    cid_table_of_alphabet = [cmap_table[str(ucode)] for ucode in UNICODE_ALPHABET if str(ucode) in cmap_table]
    match_pattern = expand_pattern_list2match_pattern(cid_table_of_alphabet)
    
    alphabet_glyf4pinyin_json = os.path.join(p.DIR_TEMP, f"alphabet_for_pinyin_{style}.json")
    cmd = f"cat {output_json} | jq '.glyf | with_entries(select(.key|match({match_pattern})))' > {alphabet_glyf4pinyin_json}"
    try:
        process_shell(cmd)
        rename_cid_of_alphabet_for_pinyin(alphabet_glyf4pinyin_json, output_json)
    except Exception as e:
        print(e)

def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Extract pinyin glyphs from a font file.")
    parser.add_argument(
        "--style",
        required=True,
        choices=['han_serif', 'handwritten'],
        help="Font style to process.")
    return parser.parse_args(args)

def main(args=None):
    options = parse_args(args)

    font_paths = {
        "han_serif": "./res/fonts/han-serif/mplus-1m-medium.ttf",
        "handwritten": "./res/fonts/handwritten/latin-alphabet-of-SetoFont-SP.ttf"
    }

    source_font_name = font_paths.get(options.style)

    if source_font_name:
        if not os.path.exists(p.DIR_TEMP):
            os.makedirs(p.DIR_TEMP)
        make_alphabet_glyf_json(source_font_name, options.style)
    else:
        print("Invalid style specified.")

if __name__ == "__main__":
    sys.exit(main())
