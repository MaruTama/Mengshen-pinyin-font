#!/usr/bin/env python

# OTF,TTF -> SVG
# $ python otf2svg.py fonts/SourceHanSerifSC-Regular.otf

# [TTFの全グリフをPNGにしてみる](https://qiita.com/scrpgil/items/7c7c0a354b3688ddfc6b)
# [fontTools のペンを使ってグリフのアウトラインを取得する](https://shiromoji.hatenablog.jp/entry/2017/11/26/221902)
import os
import sys
import argparse
# otf -> svg
from fontTools.ttLib import TTFont
from textwrap import dedent
from fontTools.pens.svgPathPen import SVGPathPen

DIR_SVG = "./fonts/SVGs"

# GlyphをSVGに変換
def save_all_glyph_as_svg(font):
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()

    for c in cmap:
        glyph_name = cmap[c]
        glyph = glyph_set[glyph_name]
        svg_path_pen = SVGPathPen(glyph_set)
        glyph.draw(svg_path_pen)

        ascender = font['OS/2'].sTypoAscender
        descender = font['OS/2'].sTypoDescender
        width = glyph.width
        height = ascender - descender

        # この書き方は f-strings
        # font は y 軸方向が svg と反対なので、反転する
        content = dedent(f'''\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-ascender} {width} {height}">
                <g transform="scale(1, -1)">
                    <path d="{svg_path_pen.getCommands()}"/>
                </g>
            </svg>
        ''')
        # 4桁0パディング
        with open(os.path.join(DIR_SVG, "{}.svg".format(glyph_name)), 'w') as f:
            f.write(content)


def main(args=None):
    parser = argparse.ArgumentParser(description='this script is to convert otf to svg')
    parser.add_argument('font_name')
    arg = parser.parse_args(args)

    font = TTFont(arg.font_name)

    # すでにフォルダがある場合は無視する
    os.makedirs(DIR_SVG, exist_ok=True)
    save_all_glyph_as_svg(font)


if __name__ == '__main__':
    sys.exit(main())
