#!/usr/bin/env python
import json
import os
import xml.etree.ElementTree as ET

# [Python ElementTreeを使ってns0名前空間なしでSVG/XML文書を作成する](https://codeday.me/jp/qa/20190115/150044.html)
# 使用する名前空間を登録しないと、ns0: みたいな接頭語が勝手に付与される
ET.register_namespace("","http://www.w3.org/2000/svg")

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
    """
    def __init__(self, AI_CAV_W_mm= 352.778, SV_CAV_W= 1000, PY_SPC_W_mm= 300, PY_SPC_H_mm = 100, PY_BSE_H_mm = 330, PY_CAV_W_mm = 176.389, PY_MAX_H_mm = 319.264, TRACKING_W_mm = 16):
        super(PinyinFont, self).__init__()
        self.AI_CAV_W_mm = AI_CAV_W_mm
        self.SV_CAV_W    = SV_CAV_W
        self.PY_SPC_W_mm = PY_SPC_W_mm
        self.PY_SPC_H_mm = PY_SPC_H_mm
        self.PY_BSE_H_mm = PY_BSE_H_mm
        self.PY_CAV_W_mm = PY_CAV_W_mm
        self.PY_MAX_H_mm = PY_MAX_H_mm
        self.TRACKING_W_mm  = TRACKING_W_mm

        # AI[mm] -> SVG座標 の倍率
        self.DMGN = self.SV_CAV_W / self.AI_CAV_W_mm
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
        tree = ET.parse(os.path.join(DIR_SVG, "{}.svg".format(self.cid)))
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
            hunzi.set("transform", "scale(1,1)")
            # hunzi.set("transform", "scale(0.85,0.75)translate(85,0)")
            g_char.append(hunzi)

            # 拼音のグループ
            g_pinyin = ET.Element('g')
            g_pinyin.set("transform", "scale({0:.2f},{0:.2f})".format(self.CMGN))
            # 各拼音のpathを取得して追加する
            for i in range(len(pinyin)):
                p_path = ET.parse("pinyin/{}.svg".format(pinyin[i])).getroot()[0]
                p_path.set( "transform", "translate({0:.2f},{1:.2f})".format(pinyin_positions[i], (self.PY_BSE_H_mm * self.DMGN / self.CMGN)) )
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

    p = PinyinFont()
    # 位置の計算のテスト
    # p.createPinyinSVG(cid=dict_unicode2cid["U+4E58"], pinyin=dict_pinyin_unicode["SimplifiedChinese"]["U+4E58"]["Pinyin"])


    # 簡体字
    for unicode in dict_pinyin_unicode["SimplifiedChinese"]:
        print( "{}: {}".format(dict_pinyin_unicode["SimplifiedChinese"][unicode]["Character"],dict_pinyin_unicode["SimplifiedChinese"][unicode]["Pinyin"]) )
        p.createPinyinSVG(cid=dict_unicode2cid[unicode], pinyin=dict_pinyin_unicode["SimplifiedChinese"][unicode]["Pinyin"])

    # 繁体字
    for unicode in dict_pinyin_unicode["TraditionalChinese"]:
        print( "{}: {}".format(dict_pinyin_unicode["TraditionalChinese"][unicode]["Character"],dict_pinyin_unicode["TraditionalChinese"][unicode]["Pinyin"]) )
        p.createPinyinSVG(cid=dict_unicode2cid[unicode], pinyin=dict_pinyin_unicode["TraditionalChinese"][unicode]["Pinyin"])
