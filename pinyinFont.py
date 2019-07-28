#!/usr/bin/env python

import sys
import argparse
from io import open
import os
import glob
import json
import xml.etree.ElementTree as ET

# [Python ElementTreeを使ってns0名前空間なしでSVG/XML文書を作成する](https://codeday.me/jp/qa/20190115/150044.html)
# 使用する名前空間を登録しないと、ns0: みたいな接頭語が勝手に付与される
ET.register_namespace("","http://www.w3.org/2000/svg")



class PinyinFont(object):
    """
    コンストラクタ
    座標計算用に数値を設定する. [mm]が付いているのはAI上の座標

    Parameters
    ----------
    DIR_SVG_CHAR: float
        文字のsvgがあるディレクトリ
    DIR_SVG_PINYIN: float
        拼音のsvgがるディレクトリ
    AI_CAV_W_mm : float
        AI上でのキャンバスの横幅[mm]
    SV_BOX_W : float
        SVG上でのキャンバスの横幅
    PY_SPC_W_mm : float
        拼音表示横幅[mm]
    PY_SPC_H_mm : float
        拼音表示縦幅[mm]
    PY_BSE_H_mm : float
        拼音表示のベースラインの下部からの高さ
    PY_CAV_W_mm : float
        拼音表示用のアルファベットのキャンバスの横幅（等幅フォントなのですべて同じ）
    PY_MAX_H_mm : float
        拼音表示用のアルファベットので最も背の高いアルファベットの高さ (多分 ǘ ǚ ǜ)
    TRACKING_W_mm : float
        拼音の標準空白幅[mm]
        Tracking is about uniform spacing across a text selection.
    scale : float tuple
        文字のsvgのscale値
    translate : float tuple
        文字のsvgのtranslate値
    """
    def __init__(self, DIR_SVG_CHAR, DIR_SVG_PINYIN, \
                    AI_CAV_W_mm, SV_BOX_W, \
                    PY_SPC_W_mm, PY_SPC_H_mm, PY_BSE_H_mm, \
                    PY_CAV_W_mm, PY_MAX_H_mm, \
                    TRACKING_W_mm, \
                    scale, translate):

        super(PinyinFont, self).__init__()
        self.DIR_SVG_CHAR = DIR_SVG_CHAR
        self.DIR_SVG_PINYIN = DIR_SVG_PINYIN
        self.AI_CAV_W_mm = AI_CAV_W_mm
        self.SV_BOX_W    = SV_BOX_W
        self.PY_SPC_W_mm = PY_SPC_W_mm
        self.PY_SPC_H_mm = PY_SPC_H_mm
        self.PY_BSE_H_mm = PY_BSE_H_mm
        self.PY_CAV_W_mm = PY_CAV_W_mm
        self.PY_MAX_H_mm = PY_MAX_H_mm
        self.TRACKING_W_mm  = TRACKING_W_mm
        (self.scaleX, self.scaleY) = scale
        (self.translateX, self.translateY) = translate

        # AI[mm] -> SVG座標 の倍率
        self.DMGN = self.SV_BOX_W / self.AI_CAV_W_mm
        # 文字倍率 (一番大きい文字が収まるサイズにする)
        self.CMGN = self.PY_SPC_H_mm / self.PY_MAX_H_mm

    """
    各拼音の座標を計算する
    """
    def __getPinyinPositions(self):

        # 空白数 1文字のときは1，それ以外はlen(pinyin_ws)-1
        bnk_num = 1 if len(self.pinyin)==1 else len(self.pinyin)-1
        # 空白幅の設定 [mm]
        # self.TRACKING_W_mm を空白幅の上限としている
        tmp = (self.PY_SPC_W_mm - self.PY_CAV_W_mm * len(self.pinyin) * self.CMGN) / bnk_num
        trk_w = tmp if tmp < self.TRACKING_W_mm else self.TRACKING_W_mm
        # 拼音全幅 [mm]
        all_pinyin_w = self.PY_CAV_W_mm * len(self.pinyin) * self.CMGN + bnk_num * trk_w
        # 中央寄せ. x軸上の開始位置
        start_x = (self.AI_CAV_W_mm - all_pinyin_w) / 2

        pinyin_positions = []
        # 各文字の座標を計算する
        for idx in range(len(self.pinyin)):
            pinyin_positions.append( ((start_x + self.PY_CAV_W_mm * idx * self.CMGN) + idx * trk_w) * self.DMGN / self.CMGN )

        return pinyin_positions

    """
    漢字と拼音を設定する

    Parameters
    ----------
    cid : String
        漢字のcid。SVGファイル名
    pinyin : String
        拼音
    """
    def setHanzi(self, cid, pinyin):
        self.cid  = cid
        self.pinyin = pinyin

    """
    指定された漢字のSVGにpinyinを追加する

    Parameters
    ----------
    cid : String
        漢字のcid。SVGファイル名
    pinyin : String
        拼音
    """
    def createPinyinSVG(self, cid, pinyin):
        self.setHanzi(cid, pinyin)
        pinyin_positions = self.__getPinyinPositions()

        # xmlファイルの読み込み
        tree = ET.parse(os.path.join(self.DIR_SVG_CHAR, "{}.svg".format(self.cid)))
        root = tree.getroot()


        # まだ拼音を追加していないとき. root以下の要素は<path>ひとつのみ
        if len(root.findall('./{http://www.w3.org/2000/svg}path')) > 0:
            # g要素を作る
            # 拼音と漢字を包むグループ
            g_char = ET.Element('g')
            g_char.set("transform", "scale(1, -1)")

            # root要素(漢字のパス)を取得
            hunzi = root[0]
            # 属性の追加
            hunzi.set("transform", "scale({0},{1})translate({2},{3})".format(self.scaleX, self.scaleY, self.translateX, self.translateY))
            # hunzi.set("transform", "scale(0.85,0.75)translate(85,0)")
            g_char.append(hunzi)

            # 拼音のグループ
            g_pinyin = ET.Element('g')
            g_pinyin.set("transform", "scale({0:.2f},{0:.2f})".format(self.CMGN))
            # 各拼音のpathを取得して追加する
            for i in range(len(pinyin)):
                p_path = ET.parse( os.path.join(self.DIR_SVG_PINYIN, "{}.svg".format(pinyin[i])) ).getroot()[0]
                p_path.set( "transform", "translate({0:.2f},{1:.2f})".format(pinyin_positions[i], (self.PY_BSE_H_mm * self.DMGN / self.CMGN)) )
                g_pinyin.append(p_path)
            g_char.append(g_pinyin)

            root.append(g_char)
            root.remove(hunzi)

            tree = ET.ElementTree(root)
            tree.write(os.path.join(self.DIR_SVG_CHAR, "{}.svg".format(self.cid)), encoding="UTF-8")

def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Convert SVG outlines to UFO glyphs (.glif)")
    parser.add_argument(
        "DIR_SVG_CHAR", metavar="DIRECTORY_OF_SVG_WITH_CHAR", help="Input folder containing SVG file of character")
    parser.add_argument(
        "DIR_SVG_PINYIN", metavar="DIRECTORY_OF_SVG_WITH_PINYIN", help="Input folder containing SVG file of pinyin ")
    parser.add_argument(
        "unicode2cid_json", metavar="unicode-cid-mapping.json",
        help="Json of unicode and cid mapping table")
    parser.add_argument(
        "hanzi_and_pinyin_json", metavar="unicode-pinyin-mapping.json",
        help="Json of hanzi and pinyin")
    parser.add_argument(
        "metadata_for_pinyin_json", metavar="metadata-for-pinyin.json",
        help="Json of metadata for pinyin")
    return parser.parse_args(args)

def main(args=None):

    options = parse_args(args)
    # 文字(漢字)のSVGがあるディレクトリ
    DIR_SVG_CHAR = options.DIR_SVG_CHAR
    # 拼音のSVGがあるディレクトリ
    DIR_SVG_PINYIN = options.DIR_SVG_PINYIN
    # 中国語に使う漢字の一覧
    HANZI_AND_PINYIN_JSON = options.hanzi_and_pinyin_json
    # unicodeとcidマッピングテーブル
    UNICODE_TO_CID_JSON = options.unicode2cid_json
    # 拼音表示のために設定値
    METADATA_FOR_PINYIN_JSON = options.metadata_for_pinyin_json


    # unicode -> cid の変換をするため
    f = open(UNICODE_TO_CID_JSON, 'r')
    dict_unicode2cid = json.load(f)
    # 中国語の漢字情報の一覧を取得する
    f = open(HANZI_AND_PINYIN_JSON, 'r')
    dict_hanzi_and_pinyin = json.load(f)
    # 拼音表示のために設定値
    f = open(METADATA_FOR_PINYIN_JSON, 'r')
    dict_metadata_for_pinyin = json.load(f)

    acw = dict_metadata_for_pinyin["AI"]["Canvas"]["Width"]
    sw = dict_metadata_for_pinyin["SVG"]["Width"]
    acpw = dict_metadata_for_pinyin["AI"]["Canvas"]["Pinyin"]["Width"]
    acph = dict_metadata_for_pinyin["AI"]["Canvas"]["Pinyin"]["Height"]
    acpb = dict_metadata_for_pinyin["AI"]["Canvas"]["Pinyin"]["BaseLine"]
    aaw = dict_metadata_for_pinyin["AI"]["Alphbet"]["Width"]
    aam = dict_metadata_for_pinyin["AI"]["Alphbet"]["MaxHeight"]
    acpd = dict_metadata_for_pinyin["AI"]["Canvas"]["Pinyin"]["DefaultTracking"]
    shsx = dict_metadata_for_pinyin["SVG"]["Hanzi"]["Scale"]["X"]
    shsy = dict_metadata_for_pinyin["SVG"]["Hanzi"]["Scale"]["Y"]
    shtx = dict_metadata_for_pinyin["SVG"]["Hanzi"]["Translate"]["X"]
    shty = dict_metadata_for_pinyin["SVG"]["Hanzi"]["Translate"]["Y"]

    p = PinyinFont(DIR_SVG_CHAR, DIR_SVG_PINYIN, \
                AI_CAV_W_mm = acw, SV_BOX_W = sw, \
                PY_SPC_W_mm = acpw, PY_SPC_H_mm = acph, PY_BSE_H_mm = acpb, \
                PY_CAV_W_mm = aaw, PY_MAX_H_mm = aam, \
                TRACKING_W_mm = acpd, \
                scale = (shsx,shsy), translate = (shtx,shty))
    # 位置の計算のテスト
    # p.createPinyinSVG(cid=dict_unicode2cid["U+4E58"], pinyin=dict_hanzi_and_pinyin["SimplifiedChinese"]["U+4E58"]["Pinyin"])

    # 簡体字
    for unicode in dict_hanzi_and_pinyin["SimplifiedChinese"]:
        print( "{}: {}".format(dict_hanzi_and_pinyin["SimplifiedChinese"][unicode]["Character"],dict_hanzi_and_pinyin["SimplifiedChinese"][unicode]["Pinyin"]) )
        p.createPinyinSVG(cid=dict_unicode2cid[unicode], pinyin=dict_hanzi_and_pinyin["SimplifiedChinese"][unicode]["Pinyin"])

    # 繁体字
    for unicode in dict_hanzi_and_pinyin["TraditionalChinese"]:
        print( "{}: {}".format(dict_hanzi_and_pinyin["TraditionalChinese"][unicode]["Character"],dict_hanzi_and_pinyin["TraditionalChinese"][unicode]["Pinyin"]) )
        p.createPinyinSVG(cid=dict_unicode2cid[unicode], pinyin=dict_hanzi_and_pinyin["TraditionalChinese"][unicode]["Pinyin"])


if __name__ == "__main__":
    sys.exit(main())
