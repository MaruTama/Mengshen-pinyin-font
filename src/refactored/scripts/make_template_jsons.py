# -*- coding: utf-8 -*-
# !/usr/bin/env python

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
from typing import List, Optional

from refactored.config.font_config import FontConfig, FontType
from refactored.config.paths import DIR_TEMP

from ..utils.logging_config import get_logger, setup_logging
from ..utils.shell_utils import ShellExecutor

TEMPLATE_TEMP_JSON = "template_temp.json"

# Common encodings for font JSON files
SUPPORTED_ENCODINGS = ["utf-8", "latin-1", "utf-8-sig"]


def is_docker_environment() -> bool:
    """Detect if running in Docker environment."""
    return os.path.exists("/.dockerenv") or os.environ.get("DOCKER_ENV") == "true"


def load_font_json_with_encoding(file_path: str) -> dict:
    """Load JSON file with multiple encoding attempts."""
    for encoding in SUPPORTED_ENCODINGS:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                result = json.load(f)
                if isinstance(result, dict):
                    return result
                return {}
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode JSON file with any supported encoding")


def save_json_compact(data: dict, file_path: str) -> None:
    """Save JSON data in compact format."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


class TemplateJsonMaker:
    """Converts OpenType fonts to JSON templates."""

    def __init__(self, shell_executor: Optional[ShellExecutor] = None):
        self.shell = shell_executor or ShellExecutor()

    def convert_otf2json(self, source_font_name: str) -> None:
        """Convert OpenType font to JSON format."""
        template_temp_json_path = os.path.join(DIR_TEMP, TEMPLATE_TEMP_JSON)
        # Use --ugly for faster processing, prettify later only if needed
        cmd = ["otfccdump", "-o", template_temp_json_path, "--ugly", source_font_name]
        self.shell.execute(cmd)

    def make_new_glyf_table_json(self, style: str) -> None:
        """Extract glyf table to separate JSON file."""
        template_temp_json_path = os.path.join(DIR_TEMP, TEMPLATE_TEMP_JSON)
        template_glyf_json_path = os.path.join(DIR_TEMP, f"template_glyf_{style}.json")

        if is_docker_environment():
            logger = get_logger("mengshen.scripts.make_template")
            logger.info(
                "Docker environment detected, using Python JSON processing for glyf extraction"
            )

            try:
                font_data = load_font_json_with_encoding(template_temp_json_path)
                glyf_data = font_data.get("glyf", {})
                save_json_compact(glyf_data, template_glyf_json_path)
            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as e:
                logger.warning(
                    "Python glyf processing failed, falling back to jq: %s", e
                )
                self._fallback_to_jq_glyf(
                    template_temp_json_path, template_glyf_json_path
                )
        else:
            # Use jq for local development (faster on local machines)
            self._fallback_to_jq_glyf(template_temp_json_path, template_glyf_json_path)

    def _fallback_to_jq_glyf(self, temp_path: str, output_path: str) -> None:
        """Extract glyf table using jq."""
        # Execute jq command and capture output
        cmd = ["jq", ".glyf", temp_path]
        result = self.shell.execute(cmd)

        # Write output to file
        with open(output_path, "wb") as f:
            f.write(result.stdout)

    def delete_glyf_table_on_main_json(self, style: str) -> None:
        """Create main template JSON with glyf contours removed."""
        template_temp_json_path = os.path.join(DIR_TEMP, TEMPLATE_TEMP_JSON)
        template_main_json_path = os.path.join(DIR_TEMP, f"template_main_{style}.json")

        if is_docker_environment():
            logger = get_logger("mengshen.scripts.make_template")
            logger.info(
                "Docker environment detected, using Python JSON processing for %s",
                style,
            )

            try:
                font_data = load_font_json_with_encoding(template_temp_json_path)
                self._remove_contours_from_glyf(font_data)
                save_json_compact(font_data, template_main_json_path)
            except (OSError, ValueError, RuntimeError, KeyError, TypeError) as e:
                logger.warning("Python processing failed, falling back to jq: %s", e)
                self._fallback_to_jq_main(
                    template_temp_json_path, template_main_json_path
                )
        else:
            # Use jq for local development (faster on local machines)
            self._fallback_to_jq_main(template_temp_json_path, template_main_json_path)

    def _remove_contours_from_glyf(self, font_data: dict) -> None:
        """Remove contours from glyf table in-place."""
        if "glyf" in font_data:
            for glyph_data in font_data["glyf"].values():
                if isinstance(glyph_data, dict) and "contours" in glyph_data:
                    glyph_data["contours"] = []

    def _fallback_to_jq_main(self, temp_path: str, output_path: str) -> None:
        """Create main template using jq."""
        # Execute jq command and capture output
        cmd = ["jq", ".glyf |= map_values( (select(1).contours |= []) // .)", temp_path]
        result = self.shell.execute(cmd)

        # Write output to file
        with open(output_path, "wb") as f:
            f.write(result.stdout)

    def make_template(self, source_font_name: str, style: str) -> None:
        """Create template JSON files from font."""
        self.convert_otf2json(source_font_name)

        if is_docker_environment():
            # Sequential processing in Docker for stability
            self._process_sequential(style)
        else:
            # Parallel processing for local development
            self._process_parallel(style)

        # Clean up temporary file
        template_temp_json_path = os.path.join(DIR_TEMP, TEMPLATE_TEMP_JSON)
        if os.path.exists(template_temp_json_path):
            os.remove(template_temp_json_path)

    def _process_sequential(self, style: str) -> None:
        """Process templates sequentially."""
        self.make_new_glyf_table_json(style)
        self.delete_glyf_table_on_main_json(style)

    def _process_parallel(self, style: str) -> None:
        """Process templates in parallel."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            glyf_future = executor.submit(self.make_new_glyf_table_json, style)
            main_future = executor.submit(self.delete_glyf_table_on_main_json, style)

            # Wait for completion
            glyf_future.result()
            main_future.result()


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert OpenType font (.otf/.ttf) to .json"
    )
    parser.add_argument(
        "--style",
        required=True,
        choices=["han_serif", "handwritten"],
        help="Font style to process.",
    )
    return parser.parse_args(args)


def make_template_main(args: Optional[List[str]] = None) -> None:
    """Main function for template creation."""
    # Setup logging
    setup_logging(level="INFO", verbose=False, quiet=False)

    options = parse_args(args)

    # Get font config based on style
    if options.style == "han_serif":
        font_type = FontType.HAN_SERIF
    else:
        font_type = FontType.HANDWRITTEN

    # Get font path from configuration
    source_font = str(FontConfig.get_font_path(font_type))

    # Create template maker and process
    maker = TemplateJsonMaker()
    maker.make_template(source_font, options.style)

    logger = get_logger("mengshen.scripts.make_template")
    logger.info("Template JSON files created for %s style", options.style)


if __name__ == "__main__":
    make_template_main()
