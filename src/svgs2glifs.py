#!/usr/bin/env python
""" Convert SVG paths to UFO glyphs. """

from __future__ import print_function, absolute_import

__requires__ = ["FontTools", "ufoLib"]

from fontTools.misc.py23 import SimpleNamespace
from fontTools.svgLib import SVGPath

from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.ufoLib.glifLib import writeGlyphToString


__all__ = ["svgs2glifs"]


def svg2glif(svg, name, width=0, height=0, unicodes=None, transform=None,
             version=2):
    """ Convert an SVG outline to a UFO glyph with given 'name', advance
    'width' and 'height' (int), and 'unicodes' (list of int).
    Return the resulting string in GLIF format (default: version 2).
    If 'transform' is provided, apply a transformation matrix before the
    conversion (must be tuple of 6 floats, or a FontTools Transform object).
    """
    glyph = SimpleNamespace(width=width, height=height, unicodes=unicodes)
    outline = SVGPath.fromstring(svg, transform=transform)

    # writeGlyphToString takes a callable (usually a glyph's drawPoints
    # method) that accepts a PointPen, however SVGPath currently only has
    # a draw method that accepts a segment pen. We need to wrap the call
    # with a converter pen.
    def drawPoints(pointPen):
        pen = SegmentToPointPen(pointPen)
        outline.draw(pen)

    return writeGlyphToString(name,
                              glyphObject=glyph,
                              drawPointsFunc=drawPoints,
                              formatVersion=version)


def parse_args(args):
    import argparse

    def split(arg):
        return arg.replace(",", " ").split()

    def unicode_hex_list(arg):
        try:
            return [int(unihex, 16) for unihex in split(arg)]
        except ValueError:
            msg = "Invalid unicode hexadecimal value: %r" % arg
            raise argparse.ArgumentTypeError(msg)

    def transform_list(arg):
        try:
            return [float(n) for n in split(arg)]
        except ValueError:
            msg = "Invalid transformation matrix: %r" % arg
            raise argparse.ArgumentTypeError(msg)

    parser = argparse.ArgumentParser(
        description="Convert SVG outlines to UFO glyphs (.glif)")
    parser.add_argument(
        "dir_svg", metavar="DIRECTORY_OF_SVG", help="Input folder containing SVG file ")
    parser.add_argument(
        "unicode2cid_json", metavar="unicode-cid-mapping.json",
        help="Json of unicode and cid mapping table")
    parser.add_argument(
        "-w", "--width", help="The glyph advance width (default: 0)",
        type=int, default=0)
    parser.add_argument(
        "-H", "--height", help="The glyph vertical advance (optional if "
        '"width" is defined)', type=int, default=0)
    parser.add_argument(
        "-t", "--transform", help="Transformation matrix as a list of six "
        'float values (e.g. -t "0.1 0 0 -0.1 -50 200")', type=transform_list)
    parser.add_argument(
        "-f", "--format", help="UFO GLIF format version (default: 2)",
        type=int, choices=(1, 2), default=2)

    return parser.parse_args(args)


def main(args=None):
    from io import open
    import os
    import glob
    import json

    options = parse_args(args)

    DIR_SVG = options.dir_svg
    UNICODE_TO_CID_JSON = options.unicode2cid_json

    files = glob.glob(os.path.join(DIR_SVG,"*.svg"))
    # 全てのファイル名のセットを作る
    file_names = {os.path.basename(file) for file in files}

    # unicode -> cid の変換をするため
    f = open(UNICODE_TO_CID_JSON, 'r')
    dic = json.load(f)
    # unicodeとcidを反転させる。
    # 一つのcidに対して複数のunicodeが対応する場合がある
    dict_cid2unicodes = {}
    for unicode,cid in dic.items():
        if cid in dict_cid2unicodes:
            dict_cid2unicodes.update({cid: dict_cid2unicodes[cid] + [int(unicode[2:],16)]})
        else:
            # int(unicode[2:],16) -> U+XXXX なのでU+を外してintにする
            dict_cid2unicodes.update({cid: [int(unicode[2:],16)]})

    DIR_GLIFS = "./glyphs/"
    # すでにフォルダがある場合は無視する
    os.makedirs(DIR_GLIFS, exist_ok=True)

    for file_name in file_names:
        with open(os.path.join(DIR_SVG,file_name), "r", encoding="utf-8") as f:
            svg = f.read()
        cid, _ = os.path.splitext(file_name)
        glif = svg2glif(svg, cid,
                        width=options.width,
                        height=options.height,
                        transform=options.transform,
                        version=options.format,
                        unicodes=dict_cid2unicodes[cid])

        with open(os.path.join(DIR_GLIFS, "{}.glif".format(cid)), 'w', encoding='utf-8') as f:
            f.write(glif)


if __name__ == "__main__":
    import sys
    sys.exit(main())
