# -*- coding: utf-8 -*-
#!/usr/bin/env python

# python3 make_json2otf.py output.otf

# Note
# [How to merge 2 JSON objects from 2 files using jq?](https://stackoverflow.com/questions/19529688/how-to-merge-2-json-objects-from-2-files-using-jq)
# jq -n --argfile o1 template_main.json --argfile o2 template_sample.json '$o1 | select(1).glyf |=  $o2' > marged.json

import os
import sys
import argparse
import subprocess
import shell

TAMPLATE_MAIN_JSON = "template_main.json"
TAMPLATE_GLYF_JSON = "template_glyf.json"
TAMPLATE_JSON = "template.json"

DIR_SOURCE_FONT = "./tmp/json"
DIR_OUTPUT_FONT = "./outputs"



# TAMPLATE_MAIN_JSON の glyf table に TAMPLATE_GLYF_JSON をマージする
def marge_json():
    template_main_json_path = os.path.join(DIR_SOURCE_FONT, TAMPLATE_MAIN_JSON)
    template_glyf_json_path = os.path.join(DIR_SOURCE_FONT, TAMPLATE_GLYF_JSON)
    template_json_path = os.path.join(DIR_SOURCE_FONT, TAMPLATE_JSON)
    cmd = "jq -n --argfile o1 {} --argfile o2 {} '$o1 | select(1).glyf |=  $o2' > {}".format(template_main_json_path, template_glyf_json_path, template_json_path)
    shell.process(cmd)

def convert_json2otf(output_font_name):
    template_json_path = os.path.join(DIR_SOURCE_FONT, TAMPLATE_JSON)
    output_font_path = os.path.join(DIR_OUTPUT_FONT, output_font_name)
    cmd = "otfccbuild {} -o {}".format(template_json_path, output_font_path)
    shell.process(cmd)

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