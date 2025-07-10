# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import annotations

import os
import sys
import argparse
from typing import List, Optional

from refactored.core.shell import ShellExecutor
from refactored.config.paths import DIR_TEMP
from refactored.config.font_config import FontType, FontConfig


TAMPLATE_TEMP_JSON = "template_temp.json"


class TemplateJsonMaker:
    """Handles font to JSON template conversion."""
    
    def __init__(self, shell_executor: ShellExecutor = None):
        self.shell = shell_executor or ShellExecutor()
    
    def convert_otf2json(self, source_font_name: str) -> None:
        """Convert OpenType font to JSON format."""
        template_temp_json_path = os.path.join(DIR_TEMP, TAMPLATE_TEMP_JSON)
        cmd = f"otfccdump -o {template_temp_json_path} --pretty {source_font_name}"
        self.shell.execute(cmd)
    
    def make_new_glyf_table_json(self, style: str) -> None:
        """Extract glyf table to separate JSON file."""
        template_temp_json_path = os.path.join(DIR_TEMP, TAMPLATE_TEMP_JSON)
        template_glyf_json_path = os.path.join(DIR_TEMP, f"template_glyf_{style}.json")
        cmd = f"cat {template_temp_json_path} | jq '.glyf' > {template_glyf_json_path}"
        self.shell.execute(cmd)
    
    def delete_glyf_table_on_main_json(self, style: str) -> None:
        """Remove glyf contours from main JSON to reduce size."""
        template_temp_json_path = os.path.join(DIR_TEMP, TAMPLATE_TEMP_JSON)
        template_main_json_path = os.path.join(DIR_TEMP, f"template_main_{style}.json")
        cmd = f"cat {template_temp_json_path} | jq '.glyf |= map_values( (select(1).contours |= []) // .)' > {template_main_json_path}"
        self.shell.execute(cmd)
    
    def make_template(self, source_font_name: str, style: str) -> None:
        """Create template JSON files from font."""
        self.convert_otf2json(source_font_name)
        self.make_new_glyf_table_json(style)
        self.delete_glyf_table_on_main_json(style)
        
        # Clean up temporary file
        template_temp_json_path = os.path.join(DIR_TEMP, TAMPLATE_TEMP_JSON)
        if os.path.exists(template_temp_json_path):
            os.remove(template_temp_json_path)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert OpenType font (.otf/.ttf) to .json")
    parser.add_argument(
        "--style",
        required=True,
        choices=['han_serif', 'handwritten'],
        help="Font style to process.")
    return parser.parse_args(args)


def make_template_main(args: Optional[List[str]] = None) -> None:
    """Main function for template creation."""
    options = parse_args(args)
    
    # Get font config based on style
    if options.style == "han_serif":
        font_type = FontType.HAN_SERIF
    else:
        font_type = FontType.HANDWRITTEN
    
    font_config = FontConfig.get_config(font_type)
    # For now, use a simple path construction since FontConfig doesn't have main_font_path
    if font_type == FontType.HAN_SERIF:
        source_font = "res/fonts/han-serif/SourceHanSerifCN-Regular.ttf"
    else:
        source_font = "res/fonts/handwritten/XiaolaiMonoSC-without-Hangul-Regular.ttf"
    
    # Create template maker and process
    maker = TemplateJsonMaker()
    maker.make_template(source_font, options.style)
    
    print(f"Template JSON files created for {options.style} style")


if __name__ == "__main__":
    make_template_main()