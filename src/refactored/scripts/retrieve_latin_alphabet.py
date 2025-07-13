# -*- coding: utf-8 -*-
# !/usr/bin/env python

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional

from refactored.config.font_config import FontConfig, FontType
from refactored.config.paths import DIR_TEMP

from ..utils.logging_config import get_scripts_logger, setup_logging
from ..utils.shell_utils import ShellExecutor

# 呣 m̀, 嘸 m̄ を使うが、これは unicode ではないので除外する。グリフが収録されていない事が多い。
ALPHABET = [
    "a",
    "ā",
    "á",
    "ǎ",
    "à",
    "b",
    "c",
    "d",
    "e",
    "ē",
    "é",
    "ě",
    "è",
    "f",
    "g",
    "h",
    "i",
    "ī",
    "í",
    "ǐ",
    "ì",
    "j",
    "k",
    "l",
    "m",
    "ḿ",
    "n",
    "ń",
    "ň",
    "ǹ",
    "o",
    "ō",
    "ó",
    "ǒ",
    "ò",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "ū",
    "ú",
    "ǔ",
    "ù",
    "ü",
    "ǖ",
    "ǘ",
    "ǚ",
    "ǜ",
    "v",
    "w",
    "x",
    "y",
    "z",
]

UNICODE_ALPHABET = [ord(c) for c in ALPHABET]

ALPHABET_FOR_PINYIN_JSON = "alphabet4pinyin.json"
OUTPUT_JSON = "output_for_pinyin.json"


class LatinAlphabetRetriever:
    """Retrieves Latin alphabet glyphs for pinyin display from fonts."""

    def __init__(self, shell_executor: ShellExecutor = None):
        self.shell = shell_executor or ShellExecutor()

    def convert_otf2json(self, source_font_name: str, output_json: str) -> None:
        """Convert OpenType font to JSON format."""
        cmd = f"otfccdump -o {output_json} --pretty {source_font_name}"
        try:
            self.shell.execute(cmd)
        except Exception as e:
            logger = get_scripts_logger()
            logger.error(f"Error converting font to JSON: {e}")
            raise

    def get_cmap_table(self, source_font_json: str) -> Dict[str, str]:
        """Extract cmap table from font JSON."""
        cmd = f"cat {source_font_json} | jq '.cmap'"
        try:
            result = self.shell.execute(cmd, capture_output=True)
            # Handle both direct output and MockResult objects
            if hasattr(result, "stdout"):
                output = result.stdout
                if isinstance(output, bytes):
                    output = output.decode("utf-8")
            else:
                output = result
            return json.loads(output)
        except Exception as e:
            logger = get_scripts_logger()
            logger.error(f"Error extracting cmap table: {e}")
            return {}

    def get_glyf_table(self, source_font_json: str) -> Dict[str, Any]:
        """Extract glyf table from font JSON."""
        cmd = f"cat {source_font_json} | jq '.glyf'"
        try:
            result = self.shell.execute(cmd, capture_output=True)
            # Handle both direct output and MockResult objects
            if hasattr(result, "stdout"):
                output = result.stdout
                if isinstance(output, bytes):
                    output = output.decode("utf-8")
            else:
                output = result
            return json.loads(output)
        except Exception as e:
            logger = get_scripts_logger()
            logger.error(f"Error extracting glyf table: {e}")
            return {}

    def filter_alphabet_glyphs(
        self, cmap_table: Dict[str, str], glyf_table: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Filter alphabet glyphs for pinyin display."""
        result = {}

        for unicode_code in UNICODE_ALPHABET:
            unicode_str = str(unicode_code)
            if unicode_str in cmap_table:
                cid = cmap_table[unicode_str]
                if cid in glyf_table:
                    char = chr(unicode_code)
                    result[char] = glyf_table[cid]

        return result

    def save_alphabet_json(
        self, alphabet_glyphs: Dict[str, Any], output_path: str
    ) -> None:
        """Save filtered alphabet glyphs to JSON file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(alphabet_glyphs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger = get_scripts_logger()
            logger.error(f"Error saving alphabet JSON: {e}")
            raise

    def retrieve_alphabet(self, source_font_name: str, style: str) -> None:
        """Main process to retrieve alphabet glyphs."""
        # Setup file paths
        temp_font_json = os.path.join(DIR_TEMP, f"temp_font_{style}.json")
        output_json_path = os.path.join(DIR_TEMP, f"alphabet_for_pinyin_{style}.json")

        try:
            # Convert font to JSON
            self.convert_otf2json(source_font_name, temp_font_json)

            # Extract tables
            cmap_table = self.get_cmap_table(temp_font_json)
            glyf_table = self.get_glyf_table(temp_font_json)

            # Filter alphabet glyphs
            alphabet_glyphs = self.filter_alphabet_glyphs(cmap_table, glyf_table)

            # Save result
            self.save_alphabet_json(alphabet_glyphs, output_json_path)

            logger = get_scripts_logger()
            logger.info(
                f"Successfully extracted {len(alphabet_glyphs)} alphabet glyphs for {style} style"
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_font_json):
                os.remove(temp_font_json)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract Latin alphabet glyphs for pinyin display"
    )
    parser.add_argument(
        "--style",
        required=True,
        choices=["han_serif", "handwritten"],
        help="Font style to process.",
    )
    return parser.parse_args(args)


def retrieve_alphabet_main(args: Optional[List[str]] = None) -> None:
    """Main function for alphabet retrieval."""
    # Setup logging
    setup_logging(level="INFO", verbose=False, quiet=False)

    options = parse_args(args)

    # Get font config based on style
    if options.style == "han_serif":
        font_type = FontType.HAN_SERIF
    else:
        font_type = FontType.HANDWRITTEN

    # Get alphabet font path from configuration
    source_font = str(FontConfig.get_alphabet_font_path(font_type))

    # Create retriever and process
    retriever = LatinAlphabetRetriever()
    retriever.retrieve_alphabet(source_font, options.style)

    logger = get_scripts_logger()
    logger.info(f"Latin alphabet extraction completed for {options.style} style")


if __name__ == "__main__":
    retrieve_alphabet_main()
