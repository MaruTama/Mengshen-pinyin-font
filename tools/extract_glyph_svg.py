#!/usr/bin/env python3
"""Extract a glyph from a font as SVG for visual inspection."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


def parse_unicode(input_str: str) -> int:
    """Parse Unicode input: character (道), U+9053, hex 9053, or decimal 36947."""
    s = input_str.strip()
    if s.startswith(("U+", "u+")):
        return int(s[2:], 16)
    if len(s) == 1:
        return ord(s)
    try:
        return int(s, 16)
    except ValueError:
        return int(s)


def extract_glyph_svg(font_path: str, unicode_input: str, output_path: str = None):
    """Extract glyph as SVG and save to file. Returns the SVG path."""
    codepoint = parse_unicode(unicode_input)
    char = chr(codepoint)

    font = TTFont(font_path)
    cmap = font.getBestCmap()

    if codepoint not in cmap:
        print(f"Error: U+{codepoint:04X} ({char!r}) not found in cmap of {font_path}")
        sys.exit(1)

    glyph_name = cmap[codepoint]
    print(f"U+{codepoint:04X} ({char}) → {glyph_name}")

    glyph_set = font.getGlyphSet()
    glyph = glyph_set[glyph_name]

    width = glyph.width
    units_per_em = font["head"].unitsPerEm

    # Get actual bounding box (handles composite glyphs too)
    bounds_pen = BoundsPen(glyph_set)
    glyph.draw(bounds_pen)
    if bounds_pen.bounds:
        x_min, y_min, x_max, y_max = bounds_pen.bounds
    else:
        x_min, y_min, x_max, y_max = 0, 0, width, units_per_em

    padding = max(units_per_em // 20, 50)
    vb_x = x_min - padding
    vb_y = -(y_max + padding)  # flip: SVG Y is top-down
    vb_w = (x_max - x_min) + padding * 2
    vb_h = (y_max - y_min) + padding * 2

    pen = SVGPathPen(glyph_set)
    glyph.draw(pen)
    path_data = pen.getCommands()

    # Flip Y axis: OpenType uses bottom-up, SVG uses top-down
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="{vb_x} {vb_y} {vb_w} {vb_h}"
     width="{vb_w}" height="{vb_h}">
  <title>U+{codepoint:04X} {char} / {glyph_name}</title>
  <g transform="scale(1,-1)">
    <path d="{path_data}" fill="black"/>
  </g>
</svg>
"""

    if output_path is None:
        output_path = f"U{codepoint:04X}_{glyph_name}.svg"

    Path(output_path).write_text(svg_content, encoding="utf-8")
    print(f"Saved: {output_path}")
    return output_path


def svg_to_png(svg_path: str, size: int = 400) -> str:
    """Convert SVG to PNG using rsvg-convert. Returns the PNG path."""
    if not shutil.which("rsvg-convert"):
        print("Error: rsvg-convert not found. Install with: brew install librsvg")
        sys.exit(1)

    png_path = str(Path(svg_path).with_suffix(".png"))
    subprocess.run(
        ["rsvg-convert", "-w", str(size), svg_path, "-o", png_path],
        check=True,
    )
    print(f"Preview: {png_path}")
    return png_path


def main():
    parser = argparse.ArgumentParser(
        description="Extract glyph from font as SVG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python tools/extract_glyph_svg.py 道 outputs/Mengshen-HanSerif.ttf
  python tools/extract_glyph_svg.py U+9053 outputs/Mengshen-HanSerif.ttf
  python tools/extract_glyph_svg.py 9053 outputs/Mengshen-HanSerif.ttf -o debug_glyph.svg
  python tools/extract_glyph_svg.py 行 outputs/Mengshen-HanSerif.ttf --preview
        """,
    )
    parser.add_argument(
        "unicode",
        help="Unicode: character (道), U+9053, or hex 9053",
    )
    parser.add_argument("font", help="Font file path (.ttf / .otf)")
    parser.add_argument(
        "-o",
        "--output",
        help="Output SVG path (default: U<code>_<glyph>.svg)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Also generate PNG preview via rsvg-convert (requires: brew install librsvg)",
    )
    parser.add_argument(
        "--preview-size",
        type=int,
        default=400,
        metavar="PX",
        help="PNG preview size in pixels (default: 400)",
    )
    args = parser.parse_args()

    svg_path = extract_glyph_svg(args.font, args.unicode, args.output)

    if args.preview:
        svg_to_png(svg_path, args.preview_size)


if __name__ == "__main__":
    main()
