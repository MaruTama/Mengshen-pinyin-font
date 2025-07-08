# -*- coding: utf-8 -*-
"""Command line interface with dependency injection."""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Optional

from ..config import FontType, ProjectPaths
from ..font import FontBuilder


class FontGenerationCLI:
    """Command line interface for font generation."""
    
    def __init__(self, paths: Optional[ProjectPaths] = None):
        """Initialize CLI with project paths."""
        self.paths = paths or ProjectPaths()
    
    def _create_argument_parser(self) -> argparse.ArgumentParser:
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Generate Mengshen Pinyin Font with automatic pinyin annotations",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s -t han_serif     Generate han serif style font
  %(prog)s -t handwritten   Generate handwritten style font
  %(prog)s --help           Show this help message
            """
        )
        
        parser.add_argument(
            "-t", "--style",
            choices=["han_serif", "handwritten"],
            default="han_serif",
            help="Font style to generate (default: han_serif)"
        )
        
        parser.add_argument(
            "-o", "--output",
            type=Path,
            help="Output font file path (default: outputs/Mengshen-{type}.ttf)"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose output"
        )
        
        parser.add_argument(
            "--dry-run",
            action="store_true", 
            help="Show what would be done without actually generating font"
        )
        
        return parser
    
    def _get_font_type(self, style_str: str) -> FontType:
        """Convert string to FontType enum."""
        type_mapping = {
            "han_serif": FontType.HAN_SERIF,
            "handwritten": FontType.HANDWRITTEN
        }
        return type_mapping[style_str]
    
    def _get_template_paths(self, font_type: FontType) -> dict:
        """Get template file paths for font type."""
        if font_type == FontType.HAN_SERIF:
            template_main_filename = "template_main.json"
            template_glyf_filename = "template_glyf.json"
            alphabet_filename = "alphabet4pinyin.json"  # M+ font style
        elif font_type == FontType.HANDWRITTEN:
            template_main_filename = "template_main.json"
            template_glyf_filename = "template_glyf.json"
            alphabet_filename = "alphabet4pinyin.json"  # SetoFont style
        else:
            raise ValueError(f"Unsupported font type: {font_type}")
        
        return {
            "template_main": self.paths.get_temp_json_path(template_main_filename),
            "template_glyf": self.paths.get_temp_json_path(template_glyf_filename),
            "alphabet_pinyin": self.paths.get_temp_json_path(alphabet_filename),
            "pattern_one": self.paths.outputs_dir / "duoyinzi_pattern_one.txt",
            "pattern_two": self.paths.outputs_dir / "duoyinzi_pattern_two.json", 
            "exception_pattern": self.paths.outputs_dir / "duoyinzi_exceptional_pattern.json"
        }
    
    def _get_output_path(self, font_type: FontType, custom_output: Optional[Path]) -> Path:
        """Get output font file path."""
        if custom_output:
            return custom_output
        
        if font_type == FontType.HAN_SERIF:
            filename = "Mengshen-HanSerif.ttf"
        elif font_type == FontType.HANDWRITTEN:
            filename = "Mengshen-Handwritten.ttf"
        else:
            raise ValueError(f"Unsupported font type: {font_type}")
        
        return self.paths.get_output_path(filename)
    
    def _validate_prerequisites(self, template_paths: dict) -> list[str]:
        """Validate that all required files exist."""
        missing_files = []
        
        for name, path in template_paths.items():
            if not Path(path).exists():
                missing_files.append(f"{name}: {path}")
        
        return missing_files
    
    def run(self, args: Optional[list[str]] = None) -> int:
        """Run the CLI application."""
        parser = self._create_argument_parser()
        parsed_args = parser.parse_args(args)
        
        try:
            # Get configuration
            font_type = self._get_font_type(parsed_args.style)
            template_paths = self._get_template_paths(font_type)
            output_path = self._get_output_path(font_type, parsed_args.output)
            
            if parsed_args.verbose:
                print(f"Font type: {font_type.name}")
                print(f"Output path: {output_path}")
                print(f"Template paths: {template_paths}")
            
            # Validate prerequisites
            missing_files = self._validate_prerequisites(template_paths)
            if missing_files:
                print("Error: Missing required files:", file=sys.stderr)
                for missing_file in missing_files:
                    print(f"  {missing_file}", file=sys.stderr)
                return 1
            
            if parsed_args.dry_run:
                print("Dry run mode - would generate font with these settings:")
                print(f"  Type: {font_type.name}")
                print(f"  Output: {output_path}")
                return 0
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create and run font builder
            font_builder = FontBuilder(
                font_type=font_type,
                template_main_path=template_paths["template_main"],
                template_glyf_path=template_paths["template_glyf"], 
                alphabet_pinyin_path=template_paths["alphabet_pinyin"],
                pattern_one_path=template_paths["pattern_one"],
                pattern_two_path=template_paths["pattern_two"],
                exception_pattern_path=template_paths["exception_pattern"],
                paths=self.paths
            )
            
            font_builder.build(output_path)
            
            if parsed_args.verbose:
                stats = font_builder.get_build_statistics()
                print("\\nBuild statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
            
            print(f"Font generation completed successfully: {output_path}")
            return 0
            
        except KeyboardInterrupt:
            print("\\nOperation cancelled by user", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point for the CLI application."""
    cli = FontGenerationCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())