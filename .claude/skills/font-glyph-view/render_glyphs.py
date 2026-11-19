"""Render Mengshen font glyphs (default + every IVS variant) to a PNG sheet.

Usage (run from anywhere):
  uv run --with pillow --with fonttools python render_glyphs.py FONT [FONT ...]
      --chars 欸誒呣 [--text "你好"] [--size 90] [--out sheet.png]

- --chars: one row per character: default glyph, then each IVS variant
  registered for it in the font's cmap format 14 table, labelled with its
  selector code point.
- --text: render a plain string as an extra row (no IVS).
- Several fonts: one block per font, stacked vertically.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

LABEL_FONTS = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]


def label_font(size: int) -> ImageFont.FreeTypeFont:
    for path in LABEL_FONTS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def ivs_selectors(font_path: str) -> dict[int, list[int]]:
    """Map base code point -> sorted selectors that have a glyph."""
    font = TTFont(font_path, lazy=True)
    result: dict[int, list[int]] = {}
    for table in font["cmap"].tables:
        if table.format != 14:
            continue
        for selector, pairs in table.uvsDict.items():
            for base, _glyph in pairs:
                result.setdefault(base, []).append(selector)
    return {base: sorted(set(selectors)) for base, selectors in result.items()}


def render_block(font_path: str, chars: str, text: str | None, size: int):
    font = ImageFont.truetype(font_path, size)
    small = label_font(max(12, size // 6))
    title = label_font(max(14, size // 5))
    selectors = ivs_selectors(font_path)
    cell_w, cell_h = int(size * 1.8), int(size * 2.1)
    label_h = int(size * 0.35)

    rows: list[list[tuple[str, str]]] = []
    for ch in chars:
        # Label with the code point only: system label fonts lack rare hanzi.
        cells = [(ch, f"U+{ord(ch):04X} default")]
        for sel in selectors.get(ord(ch), []):
            cells.append((ch + chr(sel), f"U+{sel:04X}"))
        rows.append(cells)

    width = max([len(r) for r in rows] + [1]) * cell_w + 20
    text_w = int(font.getlength(text)) + 40 if text else 0
    width = max(width, text_w, 400)
    height = 40 + len(rows) * (cell_h + label_h) + (cell_h if text else 0)

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 8), Path(font_path).name, font=title, fill="#555")
    y = 40
    for cells in rows:
        for i, (s, label) in enumerate(cells):
            x = 10 + i * cell_w
            draw.text((x, y), s, font=font, fill="black")
            draw.text((x, y + cell_h - 4), label, font=small, fill="#666")
        y += cell_h + label_h
    if text:
        draw.text((10, y), text, font=font, fill="black")
    return img


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("fonts", nargs="+", help="font files (.ttf/.otf)")
    p.add_argument("--chars", default="", help="characters, one row each")
    p.add_argument("--text", help="extra plain-text row")
    p.add_argument("--size", type=int, default=90)
    p.add_argument("--out", default="glyph_sheet.png")
    args = p.parse_args(argv)
    if not args.chars and not args.text:
        p.error("give --chars and/or --text")

    blocks = [render_block(f, args.chars, args.text, args.size) for f in args.fonts]
    sheet = Image.new(
        "RGB",
        (max(b.width for b in blocks), sum(b.height for b in blocks)),
        "white",
    )
    y = 0
    for b in blocks:
        sheet.paste(b, (0, y))
        y += b.height
    sheet.save(args.out)
    print(Path(args.out).resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
