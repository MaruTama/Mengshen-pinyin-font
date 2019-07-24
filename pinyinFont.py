#!/usr/bin/env python
import json
import os
import xml.etree.ElementTree as ET

# [Python ElementTreeを使ってns0名前空間なしでSVG/XML文書を作成する](https://codeday.me/jp/qa/20190115/150044.html)
# 使用する名前空間を登録しないと、ns0: みたいな接頭語が勝手に付与される
ET.register_namespace("","http://www.w3.org/2000/svg")

# ピンインに使うアルファベットの大きさとか
PINYIN_ALPHABET_SIZE_JSON = "pinyin-alphabet-size.json"
# 中国語に使う漢字の一覧
PINYIN_JSON = "unicode-pinyin-mapping.json"
# マッピングテーブル
UNICODE_TO_CID_JSON = "unicode-cid-mapping.json"

# 漢字のSVGがあるディレクトリ
DIR_SVG = "./fonts/SVGs"
# 設定ファイルjsonのあるディレクトリ
DIR_JSN = "./jsons"



class PinyinFont(object):
    """
    コンストラクタ
    座標計算用に数値を設定する. [mm]が付いているのはAI上の座標

    Parameters
    ----------
    AI_CAV_W_mm : float
        AI上でのキャンバスの横幅[mm]
    SV_CAV_W : float
        SVG上でのキャンバスの横幅
    PY_SPC_W_mm : float
        ピンイン表示横幅[mm]
    PY_SPC_H_mm : float
        ピンイン表示縦幅[mm]
    PY_BSE_H_mm : float
        ピンイン表示のベースラインの下部からの高さ
    BRANK_W_mm : float
        ピンインの標準空白幅[mm]
    """
    def __init__(self, font_size_filename, AI_CAV_W_mm= 352.778, SV_CAV_W= 1000, PY_SPC_W_mm= 300, PY_SPC_H_mm = 82, PY_BSE_H_mm = -235, BRANK_W_mm = 18.72):
        super(PinyinFont, self).__init__()
        self.AI_CAV_W_mm = AI_CAV_W_mm
        self.SV_CAV_W    = SV_CAV_W
        self.PY_SPC_W_mm = PY_SPC_W_mm
        self.PY_SPC_H_mm = PY_SPC_H_mm
        self.PY_BSE_H_mm = PY_BSE_H_mm
        self.BRANK_W_mm  = BRANK_W_mm
        self.font_size_filename = font_size_filename

        self.__readPinyinSize()

        # AI[mm] -> SVG座標 の倍率
        self.DMGN = self.SV_CAV_W / self.AI_CAV_W_mm
        # 文字倍率 (一番大きい文字が収まるサイズにする)
        self.CMGN = self.PY_SPC_H_mm / self.__getMaxCharH()

    """
    文字サイズを読み込む
    """
    def __readPinyinSize(self):
        f = open(self.font_size_filename, 'r')
        self.dict_font_size = json.load(f)

    """
    文字で最も背の高いアルファベットを返す (多分 ǘ ǚ ǜ) の高さ[mm]を返す
    """
    def __getMaxCharH(self):
        return max([self.dict_font_size[alp]["Height"] for alp in self.dict_font_size])

    """
    各ピンインの座標を計算する
    """
    def __getPinyinPositions(self):
        # ピンインの各字の横幅のリスト
        pinyin_ws = [self.dict_font_size[alp]["Width"] for alp in self.pinyin]
        # 空白数 1文字のときは1，それ以外はlen(pinyin_ws)-1
        bnk_num = 1 if len(pinyin_ws)==1 else len(pinyin_ws)-1
        # 空白幅の設定 [mm]
        # self.BRANK_W_mm を空白幅の上限としている
        tmp = (self.PY_SPC_W_mm - sum(pinyin_ws) * self.CMGN) / bnk_num
        bnk_w = tmp if tmp < self.BRANK_W_mm else self.BRANK_W_mm
        # ピンイン全幅 [mm]
        all_pinyin_w = sum(pinyin_ws) * self.CMGN + bnk_num * bnk_w
        # 中央寄せ. x軸上の開始位置
        start_x = (self.AI_CAV_W_mm - all_pinyin_w) / 2
        # 最初の文字の右端とキャンバス左端までの距離
        pinyin_biase = (self.dict_font_size[self.pinyin[0]]["CanvasWidth"] - self.dict_font_size[self.pinyin[0]]["CanvasWidth"]) / 2

        pinyin_positions = []
        # 各文字の座標を計算する
        for idx in range(len(pinyin_ws)):
            pinyin_positions.append( ((start_x + (sum(pinyin_ws[:idx])-pinyin_biase) * self.CMGN) + idx * bnk_w) * self.DMGN / self.CMGN )
            # print( ((start_x + (sum(pinyin_ws[:idx])-pinyin_biase) * self.CMGN) + idx * bnk_w) * self.DMGN / self.CMGN )

        return pinyin_positions

    """
    漢字とピンインを設定する

    Parameters
    ----------
    cid : String
        漢字のcid。SVGファイル名
    pinyin : String
        ピンイン
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
        ピンイン
    """
    def createPinyinSVG(self, cid, pinyin):
        self.setHanzi(cid, pinyin)
        pinyin_positions = self.__getPinyinPositions()

        # xmlファイルの読み込み
        tree = ET.parse(os.path.join(DIR_SVG, "{}.svg".format(self.cid)))
        root = tree.getroot()

        # まだ拼音を追加していないとき. rootの要素はひとつのみ
        if len(root) == 1:

            # g要素を作る
            # 拼音と漢字を包むグループ
            g_char = ET.Element('g')
            g_char.set("transform", "scale(1, -1)")

            # root要素(漢字のパス)を取得
            hunzi = root[0]
            # 属性の追加
            hunzi.set("transform", "scale(0.85,0.75)translate(85,0)")
            g_char.append(hunzi)

            # 拼音のグループ
            g_pinyin = ET.Element('g')
            g_pinyin.set("transform", "scale(0.2396,0.2396)")
            # 各拼音のpathを取得して追加する
            for i in range(len(pinyin)):
                p_path = ET.parse("pinyin/{}.svg".format(pinyin[i])).getroot()[0]
                p_path.set( "transform", "translate({},{})".format(pinyin_positions[i], -(self.PY_BSE_H_mm * self.DMGN / self.CMGN)) )
                g_pinyin.append(p_path)
            g_char.append(g_pinyin)

            root.append(g_char)
            root.remove(hunzi)

            tree = ET.ElementTree(root)
            tree.write(os.path.join(DIR_SVG, "{}.svg".format(self.cid)), encoding="UTF-8")


if __name__ == '__main__':
    # unicode -> cid の変換をするため
    f = open(os.path.join(DIR_JSN,UNICODE_TO_CID_JSON), 'r')
    dict_unicode2cid = json.load(f)
    # 中国語の漢字情報の一覧を取得する
    f = open(os.path.join(DIR_JSN,PINYIN_JSON), 'r')
    dict_pinyin_unicode = json.load(f)

    p = PinyinFont( font_size_filename=os.path.join(DIR_JSN,PINYIN_ALPHABET_SIZE_JSON) )
    p.createPinyinSVG(cid=dict_unicode2cid["U+4E58"], pinyin=dict_pinyin_unicode["SimplifiedChinese"]["U+4E58"]["Pinyin"])


    # 簡体字
    # for unicode in dict_pinyin_unicode["SimplifiedChinese"]:
    #     print( "{}: {}".format(dict_pinyin_unicode["SimplifiedChinese"][unicode]["Character"],dict_pinyin_unicode["SimplifiedChinese"][unicode]["Pinyin"]) )
    #     p.createPinyinSVG(cid=dict_unicode2cid[unicode], pinyin=dict_pinyin_unicode["SimplifiedChinese"][unicode]["Pinyin"])
    #
    # # 繁体字
    # for unicode in dict_pinyin_unicode["TraditionalChinese"]:
    #     print( "{}: {}".format(dict_pinyin_unicode["TraditionalChinese"][unicode]["Character"],dict_pinyin_unicode["TraditionalChinese"][unicode]["Pinyin"]) )
    #     p.createPinyinSVG(cid=dict_unicode2cid[unicode], pinyin=dict_pinyin_unicode["TraditionalChinese"][unicode]["Pinyin"])
