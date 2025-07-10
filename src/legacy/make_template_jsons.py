# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import annotations

import os
import sys
import argparse
import shell
import path as p

TAMPLATE_TEMP_JSON = "template_temp.json"

def convert_otf2json(source_font_name):
    template_temp_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_TEMP_JSON)
    cmd = f"otfccdump -o {template_temp_json_path} --pretty {source_font_name}"
    shell.process(cmd)

def make_new_glyf_table_json(style):
    template_temp_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_TEMP_JSON)
    template_glyf_json_path = os.path.join(p.DIR_TEMP, f"template_glyf_{style}.json")
    cmd = f"cat {template_temp_json_path} | jq '.glyf' > {template_glyf_json_path}"
    shell.process(cmd)

def delete_glyf_table_on_main_json(style):
    template_temp_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_TEMP_JSON)
    template_main_json_path = os.path.join(p.DIR_TEMP, f"template_main_{style}.json")
    cmd = f"cat {template_temp_json_path} | jq '.glyf |= map_values( (select(1).contours |= []) // .)' > {template_main_json_path}"
    shell.process(cmd)

def make_template(source_font_name, style):
    convert_otf2json(source_font_name)
    make_new_glyf_table_json(style)
    delete_glyf_table_on_main_json(style)

    template_temp_json_path = os.path.join(p.DIR_TEMP, TAMPLATE_TEMP_JSON)
    os.remove(template_temp_json_path)

def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Convert OpenType font (.otf/.ttf) to .json ")
    parser.add_argument(
        "--style",
        required=True,
        choices=['han_serif', 'handwritten'],
        help="Font style to process.")
    return parser.parse_args(args)

def main(args=None):
    options = parse_args(args)
    
    font_paths = {
        "han_serif": "./res/fonts/han-serif/SourceHanSerifCN-Regular.ttf",
        "handwritten": "./res/fonts/handwritten/XiaolaiMonoSC-without-Hangul-Regular.ttf"
    }
    
    source_font_name = font_paths.get(options.style)

    if source_font_name:
        if not os.path.exists(p.DIR_TEMP):
            os.makedirs(p.DIR_TEMP)
        make_template(source_font_name, options.style)
    else:
        print("Invalid style specified.")

if __name__ == "__main__":
    sys.exit(main())
