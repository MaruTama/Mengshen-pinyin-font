# -*- coding: utf-8 -*-
"""Simplified path configuration management."""

from __future__ import annotations

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Main directories
SRC_DIR = PROJECT_ROOT / "src"
RES_DIR = PROJECT_ROOT / "res"
FONTS_DIR = RES_DIR / "fonts"
PHONICS_DIR = RES_DIR / "phonics"
TEMP_DIR = PROJECT_ROOT / "tmp"
JSON_TEMP_DIR = TEMP_DIR / "json"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
TOOLS_DIR = PROJECT_ROOT / "tools"

# Font-specific directories
HAN_SERIF_FONT_DIR = FONTS_DIR / "han-serif"
HANDWRITTEN_FONT_DIR = FONTS_DIR / "handwritten"

# Phonics data directories
UNICODE_MAPPING_DIR = PHONICS_DIR / "unicode_mapping_table"
DUO_YIN_ZI_DIR = PHONICS_DIR / "duo_yin_zi"


class ProjectPaths:
    """Simplified path management for backward compatibility."""

    def __init__(self, project_root: Path = None):
        """Initialize project paths."""
        self.project_root = project_root or PROJECT_ROOT

    @property
    def src_dir(self) -> Path:
        """Source code directory."""
        return self.project_root / "src"

    @property
    def resources_dir(self) -> Path:
        """Resources directory."""
        return self.project_root / "res"

    @property
    def fonts_dir(self) -> Path:
        """Fonts directory."""
        return self.resources_dir / "fonts"

    @property
    def phonics_dir(self) -> Path:
        """Phonics data directory."""
        return self.resources_dir / "phonics"

    @property
    def temp_dir(self) -> Path:
        """Temporary directory."""
        return self.project_root / "tmp"

    @property
    def json_temp_dir(self) -> Path:
        """JSON temporary directory."""
        return self.temp_dir / "json"

    @property
    def outputs_dir(self) -> Path:
        """Outputs directory."""
        return self.project_root / "outputs"

    @property
    def tools_dir(self) -> Path:
        """Tools directory."""
        return self.project_root / "tools"

    def get_output_path(self, filename: str) -> Path:
        """Get output path for a given filename."""
        return self.outputs_dir / filename

    def get_temp_json_path(self, filename: str) -> Path:
        """Get temp JSON path for a given filename."""
        return self.json_temp_dir / filename


# Legacy constants for direct import
DIR_ROOT = str(PROJECT_ROOT)
DIR_SRC = str(SRC_DIR)
DIR_RES = str(RES_DIR)
DIR_FONTS = str(FONTS_DIR)
DIR_PHONICS = str(PHONICS_DIR)
DIR_TEMP = str(JSON_TEMP_DIR)  # Point to json temp dir for backward compatibility
DIR_OUTPUT = str(OUTPUTS_DIR)
DIR_TOOLS = str(TOOLS_DIR)
