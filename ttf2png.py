#!/usr/bin/env python
# [TTFの全グリフをPNGにしてみる](https://qiita.com/scrpgil/items/7c7c0a354b3688ddfc6b)
# [fontTools のペンを使ってグリフのアウトラインを取得する](https://shiromoji.hatenablog.jp/entry/2017/11/26/221902)
import os
import sys
import argparse
# ttf -> svg
from fontTools.ttLib import TTFont
from textwrap import dedent
from fontTools.pens.svgPathPen import SVGPathPen
# svg -> PNG
from cairosvg import svg2png
# resize
import glob
from PIL import Image


# PNGを 1/20 リサイズする  めっちゃ時間かかる
def resize_all_png():
    path = "output_png"
    files = os.listdir(path)
    files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]
    for fname in files_file:
        bname, ext =  os.path.splitext(fname)
        if ext != ".png":
            continue
        img = Image.open("./output_png/" + bname + ext)
        img_resize = img.resize((int(img.width/20), int(img.height/20)))
        img_resize.save("./output_resize/" + bname + "_herf" + ext)


# SVGをPNGに変換する  めっちゃ時間かかる
def convert_all_svg_to_png():
    path = "output_svg"
    files = os.listdir(path)
    files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]
    for fname in files_file:
        bname, ext =  os.path.splitext(fname)

        try:
            svg2png(url='output_svg/' + bname + '.svg', write_to='output_png/' + bname + '.png')
        except:
            print(fname)
    return

# GlyphをSVGに変換
def save_all_glyph_as_svg(font):
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()

    output_path = "output_svg/"
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
        content = dedent(f'''\
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-ascender} {width} {height}">
                <g transform="scale(1, -1)">
                    <path d="{svg_path_pen.getCommands()}"/>
                </g>
            </svg>
        ''')
        # 4桁0パディング
        with open(output_path + format(c, '05x') + ".svg", 'w') as f:
            f.write(content)


def main(args=None):
    parser = argparse.ArgumentParser(description='this script is to convert ttf to png')
    parser.add_argument('font_name')
    arg = parser.parse_args(args)

    font = TTFont(arg.font_name)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()

    # すでにフォルダがある場合は無視する
    os.makedirs("output_svg", exist_ok=True)
    os.makedirs("output_png", exist_ok=True)
    os.makedirs("output_resize", exist_ok=True)

    save_all_glyph_as_svg(font)
    # convert_all_svg_to_png()
    # resize_all_png()


if __name__ == '__main__':
    sys.exit(main())
