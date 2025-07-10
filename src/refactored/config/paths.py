# -*- coding: utf-8 -*-
"""Path configuration management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class ProjectPaths:
    """Centralized path management for the project."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize project paths."""
        if project_root is None:
            # Determine project root from current file location
            self.project_root = Path(__file__).parent.parent.parent.parent
        else:
            self.project_root = Path(project_root)
    
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
        directories = [
            self.temp_dir,
            self.json_temp_dir,
            self.outputs_dir
        ]
        
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
        return self.json_temp_dir / filename


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
        'DIR_ROOT': str(paths.project_root),
        'DIR_SRC': str(paths.src_dir),
        'DIR_RES': str(paths.resources_dir),
        'DIR_FONTS': str(paths.fonts_dir),
        'DIR_PHONICS': str(paths.phonics_dir),
        'DIR_TEMP': str(paths.temp_dir),
        'DIR_OUTPUT': str(paths.outputs_dir),
        'DIR_TOOLS': str(paths.tools_dir)
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