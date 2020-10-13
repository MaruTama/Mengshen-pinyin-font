# encoding: utf-8

# python3 get_alphabet_glyf4pinyin.py ./res/fonts/mplus-1m-medium.ttf
import os
import sys
import argparse
import subprocess
import json

# できた
# cat alphabet4pinyin.json | jq '.glyf | with_entries(select(.key|match("^a$|^b$")))' > out.json

# 一文字なら、これの方がわかりやすい。置換のときに使えるかな
# cat alphabet4pinyin.json | jq '.glyf | with_entries(select(.key == "a"))' > out.json


ALPHABET_FOR_PINYIN_JSON = "alphabet4pinyin.json"
DIR_JSON = "./res/fonts/"

OUTPUT_JSON = "output.json"
DIR_TEMP = "./tmp"

ALPHABET = ["a","ā","á","ǎ","à","b","c","d","e","ē","é","ě","è","f","g","h","i","ī","í","ǐ","ì","j","k","l","m","ḿ","n","ń","o","ō","ó","ǒ","ò","ở","p","q","r","s","t","u","ū","ú","ǔ","ù","ü","ǖ","ǘ","ǚ","ǜ","v","w","x","y","z"]
UNICODE_ALPHABET = [ord(c) for c in ALPHABET]

def process_shell(cmd=""):
    # print('start')
    completed_process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # print(f'returncode: {completed_process.returncode},stdout: {completed_process.stdout},stderr: {completed_process.stderr}')
    if b'' != completed_process.stderr:
        raise Exception(completed_process.stderr)
    return completed_process.stdout

def convert_otf2json(source_font_name, output_json):
    cmd = "otfccdump -o {} --pretty {}".format(output_json, source_font_name)
    try:
        process_shell(cmd)
    except Exception as e:
        print()
        print(e)

# cmap の大きさなら、全部取得しても 65536 程度だから、フィルターしなくてもいいな
def get_cmap_table(source_font_json):
    cmd = "cat {} | jq '.cmap' ".format(source_font_json)
    try:
        cmap_table = json.loads( process_shell(cmd) )
    except Exception as e:
        print()
        print(e)
    return cmap_table

def expand_pattern_list2match_pattern(ALPHABET):
    match_pattern = ""
    for c in ALPHABET:
        match_pattern += "^{}$|".format(c) if ALPHABET[-1] != c else "^{}$".format(c)
    return ' "{}" '.format(match_pattern)

def make_alphabet_glyf_json(source_font_name):
    output_json = os.path.join(DIR_TEMP, OUTPUT_JSON)
    convert_otf2json( source_font_name, output_json )
    cmap_table = get_cmap_table( output_json )
    cid_table_of_alphabet  = [cmap_table[str(uni)] for uni in UNICODE_ALPHABET]
    match_pattern = expand_pattern_list2match_pattern( cid_table_of_alphabet )
    
    alphabet_glyf4pinyin_json_path = os.path.join(DIR_JSON, ALPHABET_FOR_PINYIN_JSON)
    # match_pattern = ' "^a$|^b$" ' 
    cmd = "cat {} | jq '.glyf | with_entries(select(.key|match({})))' > {}".format(output_json, match_pattern, alphabet_glyf4pinyin_json_path)
    try:
        print(cmd)
        process_shell(cmd)
    except Exception as e:
        print()
        print(e)

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
        if not os.path.exists(DIR_JSON):
            os.makedirs(DIR_JSON)
        make_alphabet_glyf_json(source_font_name)
        
    else:
        print("invalid argument:")
        print("  input file is font file (.otf/.ttf) only.")

if __name__ == "__main__":
    sys.exit(main())