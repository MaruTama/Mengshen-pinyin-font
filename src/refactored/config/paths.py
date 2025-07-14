# -*- coding: utf-8 -*-
"""Path configuration management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..utils.shell_utils import SecurityError


class ProjectPaths:
    """Centralized path management for the project."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize project paths."""
        if project_root is None:
            # Determine project root from current file location
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)

    def get_project_root(self) -> Path:
        """Get the project root directory.

        This method is primarily used in tests for mocking purposes.
        """
        return self.project_root

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
    def unicode_mapping_dir(self) -> Path:
        """Unicode mapping directory."""
        return self.phonics_dir / "unicode_mapping_table"

    @property
    def duo_yin_zi_dir(self) -> Path:
        """Duo yin zi (homograph) directory."""
        return self.phonics_dir / "duo_yin_zi"

    @property
    def pinyin_data_dir(self) -> Path:
        """Pinyin data submodule directory."""
        return self.phonics_dir / "pinyin-data"

    @property
    def temp_dir(self) -> Path:
        """Temporary files directory."""
        return self.project_root / "tmp"

    @property
    def json_temp_dir(self) -> Path:
        """JSON temporary files directory."""
        return self.temp_dir / "json"

    @property
    def outputs_dir(self) -> Path:
        """Output files directory."""
        return self.project_root / "outputs"

    @property
    def tools_dir(self) -> Path:
        """Tools directory."""
        return self.project_root / "tools"

    def ensure_directories(self) -> None:
        """Ensure all necessary directories exist."""
        directories = [self.temp_dir, self.json_temp_dir, self.outputs_dir]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_font_path(self, font_style: str, font_name: str) -> Path:
        """Get path to a specific font file."""
        return self.fonts_dir / font_style / font_name

    def get_output_path(self, filename: str) -> Path:
        """Get path to an output file."""
        return self.outputs_dir / filename

    def get_temp_json_path(self, filename: str) -> Path:
        """Get path to a temporary JSON file."""
        # Basic filename validation for security
        self._validate_filename(filename)
        return self.json_temp_dir / filename

    def validate_path(self, path: str) -> Path:
        """Validate a path for security."""
        from ..utils.shell_utils import validate_file_path

        return validate_file_path(path)

    def get_pattern_path(self, filename: str) -> Path:
        """Get path to a pattern file."""
        self._validate_filename(filename)
        return self.duo_yin_zi_dir / filename

    def canonicalize_path(self, path: str) -> Path:
        """Canonicalize a path securely."""
        validated_path = self.validate_path(path)
        return validated_path.resolve()

    def _validate_filename(self, filename: str) -> None:
        """Validate filename for security."""
        if not isinstance(filename, str):
            raise SecurityError("Filename must be a string")

        # Check for dangerous patterns in filename
        dangerous_patterns = [
            "..",
            "/",
            "\\",
            ":",
            "*",
            "?",
            '"',
            "<",
            ">",
            "|",
            "\x00",
            "\n",
            "\r",
            "\t",
        ]

        for pattern in dangerous_patterns:
            if pattern in filename:
                raise SecurityError(
                    f"Dangerous pattern '{pattern}' in filename: {filename}"
                )

        # Check for Windows reserved names
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]

        if filename.upper() in reserved_names:
            raise SecurityError(f"Reserved filename not allowed: {filename}")

        # Check filename length
        if len(filename) > 255:
            raise SecurityError(f"Filename too long: {len(filename)} characters")


# Global instance for backward compatibility
_default_paths: Optional[ProjectPaths] = None


def get_default_paths() -> ProjectPaths:
    """Get the default project paths instance."""
    global _default_paths
    if _default_paths is None:
        _default_paths = ProjectPaths()
    return _default_paths


# Backward compatibility with old path module
def get_legacy_paths():
    """Get legacy path constants for backward compatibility."""
    paths = get_default_paths()

    # Legacy constants that other modules expect
    return {
        "DIR_ROOT": str(paths.project_root),
        "DIR_SRC": str(paths.src_dir),
        "DIR_RES": str(paths.resources_dir),
        "DIR_FONTS": str(paths.fonts_dir),
        "DIR_PHONICS": str(paths.phonics_dir),
        "DIR_TEMP": str(paths.temp_dir),
        "DIR_OUTPUT": str(paths.outputs_dir),
        "DIR_TOOLS": str(paths.tools_dir),
    }


# Legacy constants for direct import
paths = get_default_paths()
DIR_ROOT = str(paths.project_root)
DIR_SRC = str(paths.src_dir)
DIR_RES = str(paths.resources_dir)
DIR_FONTS = str(paths.fonts_dir)
DIR_PHONICS = str(paths.phonics_dir)
DIR_TEMP = str(paths.json_temp_dir)  # Point to json temp dir for backward compatibility
DIR_OUTPUT = str(paths.outputs_dir)
DIR_TOOLS = str(paths.tools_dir)
