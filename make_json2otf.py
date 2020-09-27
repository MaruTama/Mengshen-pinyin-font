# python3 make_json2otf.py output.otf

# Note
# [How to merge 2 json file using jq?](https://stackoverrun.com/ja/q/5331015)
# template_main.json の glyf table に template_glyf.json をマージする
# 前半の '.[0].glyf = .[1]' こっちが引数をとる
# 後半の '.[0]' こっちが出力された json の最初の要素(template_main.jsonの要素)を取る。（このコマンドだと置換できるが、なぜか末尾にtemplate_glyf.json の内容がくっつくため）
# $ jq -s '.[0].glyf = .[1] | .[0]' tmp/json/template_main.json tmp/json/template_glyf.json > text.json


import os
import sys
import argparse
import subprocess

TAMPLATE_MAIN_JSON = "template_main.json"
TAMPLATE_GLYF_JSON = "template_glyf.json"
TAMPLATE_JSON = "template.json"

DIR_SOURCE_FONT = "./tmp/json"
DIR_OUTPUT_FONT = "./outputs"

def process_shell(cmd=""):
    result = (subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]).decode('utf-8')
    if not ("" == result):
        print(result)

# TAMPLATE_MAIN_JSON の glyf table に TAMPLATE_GLYF_JSON をマージする
def marge_json():
    template_main_json_path = os.path.join(DIR_SOURCE_FONT, TAMPLATE_MAIN_JSON)
    template_glyf_json_path = os.path.join(DIR_SOURCE_FONT, TAMPLATE_GLYF_JSON)
    template_json_path = os.path.join(DIR_SOURCE_FONT, TAMPLATE_JSON)
    # FIXME: なんとか動いているがもっときれいなコマンドにしたい
    cmd = "jq -s '.[0].glyf = .[1] | .[0]' {} {} > {}".format(template_main_json_path, template_glyf_json_path, template_json_path)
    process_shell(cmd)

def convert_json2otf(output_font_name):
    template_json_path = os.path.join(DIR_SOURCE_FONT, TAMPLATE_JSON)
    output_font_path = os.path.join(DIR_OUTPUT_FONT, output_font_name)
    cmd = "otfccbuild {} -o {}".format(template_json_path, output_font_path)
    process_shell(cmd)

def make_font(output_font_name):
    marge_json()
    convert_json2otf(output_font_name)

def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Convert .json to OpenType font (.otf/.ttf)")
    parser.add_argument("output_font_name", metavar="Output font name", help="Output font name")
    return parser.parse_args(args)

def main(args=None):
    options = parse_args(args)
    output_font_name = options.output_font_name
    extension = os.path.splitext(output_font_name)[-1]
    if (".otf" == extension or ".ttf" == extension):
        if not os.path.exists(DIR_OUTPUT_FONT):
            os.makedirs(DIR_OUTPUT_FONT)
        make_font(output_font_name)
    else:
        print("invalid argument:")
        print("  output file is font file (.otf/.ttf) only.")

if __name__ == "__main__":
    sys.exit(main())