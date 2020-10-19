# -*- coding: utf-8 -*-
#!/usr/bin/env python

# python3 make_pinyin_glyph.py

import os
import json
import pinyin_getter as pg
import subprocess

SIMPLED_ALPHABET = {
    "a":"a", "ā":"a1", "á":"a2", "ǎ":"a3", "à":"a4",
    "b":"b",
    "c":"c",
    "d":"d",
    "e":"e", "ē":"e1", "é":"e2", "ě":"e3", "è":"e4",
    "f":"f",
    "g":"g",
    "h":"h",
    "i":"i", "ī":"i1", "í":"i2", "ǐ":"i3", "ì":"i4",
    "j":"j",
    "k":"k",
    "l":"l",
    "m":"m", "m̄":"m1", "ḿ":"m2", "m̀":"m4",
    "n":"n",           "ń":"n2", "ň":"n3", "ǹ":"n4",
    "o":"o", "ō":"o1", "ó":"o2", "ǒ":"o3", "ò":"o4",
    "p":"p",
    "q":"q",
    "r":"r",
    "s":"s",
    "t":"t",
    "u":"u", "ū":"u1", "ú":"u2" ,"ǔ":"u3", "ù":"u4", "ü":"v", "ǖ":"v1", "ǘ":"v2", "ǚ":"v3", "ǜ":"v4",
    "v":"v",
    "w":"w",
    "x":"x",
    "y":"y",
    "z":"z"
}

class PinyinGlyph():
    # 想定する漢字のサイズに対するピンイン表示部のサイズ
    # 前作より引用
    METADATA_FOR_PINYIN = {
        "pinyin_canvas":{
            "width"    : 850,   # ピンイン表示部の幅
            "height"   : 283.3, # ピンイン表示部の高さ
            "base_line": 935,   # ベースラインからの高さ
            "tracking" : 22.145 # 拼音の標準空白幅： Tracking is about uniform spacing across a text selection.
        },
        "expected_hanzi_canvas":{
            "width" : 1000, # 基準にする漢字の表示部の幅
            "height": 1000, # 基準にする漢字の表示部の高さ
        }
    }

    # マージ先のフォントのメインjson（フォントサイズを取得するため）, ピンイン表示に使うためのglyfのjson, ピンインのグリフを追加したjson(出力ファイル)
    def __init__(self, TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON):
        self.PINYIN_MAPPING_TABLE = pg.get_pinyin_table_with_mapping_table()
        with open(TAMPLATE_MAIN_JSON, mode='r', encoding='utf-8') as read_file:
            self.font_main = json.load(read_file)
            self.cmap_table = self.font_main["cmap"]
        with open(ALPHABET_FOR_PINYIN_JSON, mode='r', encoding='utf-8') as read_file:
            self.pinyin_glyf = json.load(read_file)

    # ピンイン表記の簡略化、e.g.: wěi -> we3i
    def __simplification_pinyin(self, pinyin):
        return  "".join( [SIMPLED_ALPHABET[c] for c in pinyin] )
    
    # マージ先のフォントの漢字サイズを返す
    def __get_advance_size_of_hanzi(self):
        # なんでもいいが、とりあえず漢字の「一」でサイズを取得する
        cid = self.font_main["cmap"][str(ord("一"))]
        advanceWidth  = self.font_main["glyf"][cid]["advanceWidth"]
        advanceHeight = self.font_main["glyf"][cid]["advanceHeight"]
        return (advanceWidth, advanceHeight)

    # PINYIN_MAPPING_TABLE から全発音を取り出して返す
    def __get_pronunciations(self):
        set_pronunciations = set()
        for _, pinyins in self.PINYIN_MAPPING_TABLE.items():
            set_pronunciations = set_pronunciations | set(pinyins)
        pronunciations = list(set_pronunciations)
        pronunciations.sort()
        return pronunciations

    # pinyin の発音をマージ先の大きさを取得して調整、追加する
    def marge_pronunciations_to_glyf_table(self):
        (target_advance_width_of_hanzi, target_advance_height_of_hanzi) = self.__get_advance_size_of_hanzi()
        pronunciations = self.__get_pronunciations()

        """
        a-d ってなんだ？
        > The transformation entries determine the values of an affine transformation applied to the component prior to its being incorporated into the parent glyph. Given the component matrix [a b c d e f], the transformation applied to the component is:

        [The 'glyf' table](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6glyf.html)
        [FontConfigの​matrix​フォント​プロパティを​利用して​字体を​変化させる​方法](http://ie.pcgw.pgw.jp/2015/10/17/fontconfig-matrix.html)


        otfccbuild の仕様なのか opentype の仕様なのか分からないが
        a と d が同じ値だと、グリフが消失する。 少しでもサイズが違えば反映される。
        なので、90% にするなら、a=0.9, d=0.91 とかにする。
        """
        # 追加したいフォントのサイズに合わせるために scale を求める
        hanzi_canvas_width_scale  = target_advance_width_of_hanzi  / self.METADATA_FOR_PINYIN["expected_hanzi_canvas"]["width"]
        hanzi_canvas_height_scale = target_advance_height_of_hanzi / self.METADATA_FOR_PINYIN["expected_hanzi_canvas"]["height"]

        # 追加したいフォント上でのピンイン表示部サイズを求める
        target_pinyin_canvas_width     = self.METADATA_FOR_PINYIN["pinyin_canvas"]["width"]     * hanzi_canvas_width_scale
        target_pinyin_canvas_height    = self.METADATA_FOR_PINYIN["pinyin_canvas"]["height"]    * hanzi_canvas_height_scale
        target_pinyin_canvas_base_line = self.METADATA_FOR_PINYIN["pinyin_canvas"]["base_line"] * hanzi_canvas_height_scale
        target_pinyin_canvas_tracking  = self.METADATA_FOR_PINYIN["pinyin_canvas"]["tracking"]  * hanzi_canvas_width_scale

        # ピンインがキャンバスに収まる scale を求める. 
        # 等幅フォントであれば大きさは同じなのでどんな文字でも同じだと思うが、一応最も背の高い文字を指定する (多分 ǘ ǚ ǜ)
        pinyin_scale  = target_pinyin_canvas_height / self.pinyin_glyf["py_v3"]["advanceHeight"]

        # ピンイン表示部に文字を詰めていく
        # 各文字の配置を計算する
        pinyin_width  = self.pinyin_glyf["py_v3"]["advanceWidth"] * pinyin_scale
        
        for pronunciation in pronunciations:
            # 引数多いから、クラス内のローカル変数にしようかと思ったけど、明示的にコメント入れておいて役割を示すのもいいかな
            # ピンイン表示部(target_pinyin_canvas_width)に収まるように等間隔に配置する
            width_positions =  self.__get_pinyin_position_on_canvas( pronunciation, 
                                        pinyin_width, 
                                        target_pinyin_canvas_width, 
                                        target_pinyin_canvas_tracking, 
                                        target_advance_width_of_hanzi )
            self.__add_pronunciations( pronunciation,
                                        width_positions, 
                                        target_advance_width_of_hanzi, 
                                        pinyin_scale, 
                                        target_pinyin_canvas_height,
                                        target_pinyin_canvas_base_line )

    """
    各文字の座標を計算する
    """
    def __get_pinyin_position_on_canvas( self, 
                                        pronunciation,                  # pinyin の発音 (e.g.: láng)
                                        pinyin_width,                   # ピンインに使用する一文字の幅（等幅なので全て同じはず）
                                        canvas_width,                   # 表示部の幅（METADATA_FOR_PINYINで指定）
                                        canvas_tracking,                # 最大文字間幅（METADATA_FOR_PINYINで指定）
                                        target_advance_width_of_hanzi): # マージ先のフォントの幅（漢字なら正方形のはず）
        # 空白数 1文字のときは1，それ以外はlen(pinyin) 
        blank_num = 1 if len(pronunciation)==1 else len(pronunciation)-1
        # 空白幅の設定
        # canvas_tracking を空白幅の上限としている
        tmp = (canvas_width - pinyin_width * len(pronunciation)) / blank_num
        blank_width = tmp if tmp < canvas_tracking else canvas_tracking
        # 拼音全幅 [mm]
        arranged_pinyin_width = (len(pronunciation) * pinyin_width) + (blank_num * blank_width)
        # 中央寄せ. x軸上の開始位置
        start_x = (target_advance_width_of_hanzi - arranged_pinyin_width) / 2

        pinyin_positions = []
        # 各文字の座標を計算する
        for idx in range(len(pronunciation)):
            pinyin_positions.append( round( ((start_x + pinyin_width * idx) + idx * blank_width), 2 ) )

        return pinyin_positions


    def __add_pronunciations(self, 
                            pronunciation,                    # pinyin の発音 (e.g.: láng)
                            width_positions,                  # ピンインの各文字の座標のリスト
                            target_advance_width_of_hanzi,    # マージ先のフォントの漢字の幅
                            pinyin_scale,                     # ピンインのグリフの縮小率
                            target_pinyin_canvas_height,      # ピンイン表示部の高さ
                            target_pinyin_canvas_base_line ): # 基準点からピンイン表示部までの高さ
        references = []
        for i in range(len(pronunciation)):
            alphabet = self.__simplification_pinyin( pronunciation[i] )
            x = width_positions[ i ]
            references.append( 
                {"glyph":"py_{}".format(alphabet),
                                "x": x,             "y": target_pinyin_canvas_base_line,
                                "a": pinyin_scale, "b": 0, 
                                "c": 0,            "d": pinyin_scale + 0.001}
            )

        # arranged_ と名前を変えているのは、一文字の発音のときに同じ名前のグリフができないようにするため。
        # 同じ名前のグリフがあると参照エラーになる。
        pronunciation = {
            "arranged_" + self.__simplification_pinyin(pronunciation): {
                "advanceWidth"  : target_advance_width_of_hanzi,
                "advanceHeight" : target_pinyin_canvas_height,
                "verticalOrigin": 0, # 漢字へのマージ時に変更するから、今は 0 
                "references": references
            }
        }
        self.pinyin_glyf.update( pronunciation )


    def save(self, OUTPUT_JSON):
        with open(OUTPUT_JSON, mode='w', encoding='utf-8') as write_file:
            json.dump(self.pinyin_glyf, write_file, indent=4, ensure_ascii=False)
    



class Font():
    def __init__(self, TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON):

        self.TAMPLATE_JSON = "./tmp/json/template.json"

        with open(TAMPLATE_MAIN_JSON, mode='r', encoding='utf-8') as read_file:
            self.font_main = json.load(read_file)
        with open(ALPHABET_FOR_PINYIN_JSON, mode='r', encoding='utf-8') as read_file:
            self.pinyin_glyf = json.load(read_file)
        self.cmap_table = self.font_main["cmap"]
        self.pinyin_mapping_table = pg.get_pinyin_table_with_mapping_table()

    # とりあえず、ピンインだけ追加
    def add_glyph_order(self):
        # ピンインのグリフを追加 
        set_glyph_order = set(self.font_main["glyph_order"]) | set(self.pinyin_glyf.keys())
        new_glyph_order = list(set_glyph_order)
        new_glyph_order.sort()
        self.font_main["glyph_order"] = new_glyph_order
        print( len(self.font_main["glyph_order"]) )

    # とりあえず、ピンインだけ追加
    def add_glyf(self):
        new_glyf = self.font_main["glyf"]
        new_glyf.update( self.pinyin_glyf )
        self.font_main["glyf"] = new_glyf
        
        # ss00 - 0n をマージする

    def __save_tamplate_json(self, TAMPLATE_JSON):
        with open(TAMPLATE_JSON, mode='w', encoding='utf-8') as f:
            json.dump(self.font_main, f, indent=4, ensure_ascii=False)

    def build(self):
        self.add_glyph_order()
        self.add_glyf()
        self.__save_tamplate_json( self.TAMPLATE_JSON )
        self.convert_json2otf( self.TAMPLATE_JSON, "./pinyin_sample.otf" )
    
    # 以下、make_json2otf からコピペ
    def process_shell(self, cmd=""):
        print(cmd)
        completed_process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        if b'' != completed_process.stderr:
            raise Exception(completed_process.stderr)
        return completed_process.stdout

    def convert_json2otf(self, template_json, output_font):
        cmd = "otfccbuild {} -o {}".format(template_json, output_font)
        self.process_shell(cmd)


if __name__ == "__main__":
    DIR_OUTPUT = "./outputs/"
    DIR_JSON   = "./res/fonts/"
    DIR_TMP    = "./tmp/json"

    ALPHABET_FOR_PINYIN_JSON = os.path.join(DIR_JSON, "alphabet4pinyin.json")
    TAMPLATE_MAIN_JSON       = os.path.join(DIR_TMP, "template_main.json")
    TAMPLATE_GLYF_JSON       = os.path.join(DIR_TMP, "template_glyf.json")

    # build の前に ALPHABET_FOR_PINYIN_JSON に発音を入れる
    pinyin_glyph = PinyinGlyph(TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON)
    pinyin_glyph.marge_pronunciations_to_glyf_table()
    
    OUTPUT_JSON = "./tmp/json/template.json"
    pinyin_glyph.save(OUTPUT_JSON)

    font = Font(TAMPLATE_MAIN_JSON, OUTPUT_JSON)
    # font = Font(TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON)
    # # glyf に追加するpinyin の種類は、mapping_table に完全に依存する
    font.build()
