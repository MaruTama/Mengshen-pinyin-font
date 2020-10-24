# -*- coding: utf-8 -*-
#!/usr/bin/env python

import orjson
import pinyin_getter as pg
import shell
import utility


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

        with open(TAMPLATE_MAIN_JSON, "rb") as read_file:
            self.font_main = orjson.loads(read_file.read())
            self.cmap_table = self.font_main["cmap"]
        with open(ALPHABET_FOR_PINYIN_JSON, "rb") as read_file:
            self.pinyin_glyf = orjson.loads(read_file.read())

    
    
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
    def add_pronunciations_to_glyf_table(self):
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
            simpled_alphabet = utility.simplification_pronunciation( pronunciation[i] )
            x = width_positions[ i ]
            references.append( 
                {"glyph":"py_{}".format(simpled_alphabet),
                                "x": x,             "y": target_pinyin_canvas_base_line,
                                "a": pinyin_scale, "b": 0, 
                                "c": 0,            "d": pinyin_scale + 0.001}
            )

        # arranged_ と名前を変えているのは、一文字の発音のときに同じ名前のグリフができないようにするため。
        # 同じ名前のグリフがあると参照エラーになる。
        simpled_pronunciation = utility.simplification_pronunciation(pronunciation)
        pronunciation = {
            "arranged_{}".format(simpled_pronunciation) : {
                "advanceWidth"  : target_advance_width_of_hanzi,
                "advanceHeight" : target_pinyin_canvas_height,
                "verticalOrigin": 0, # 漢字へのマージ時に変更するから、今は 0 
                "references": references
            }
        }
        self.pinyin_glyf.update( pronunciation )


    def save(self, OUTPUT_JSON):
        with open(OUTPUT_JSON, "wb") as write_file:
            serialized_glyf = orjson.dumps(self.pinyin_glyf, option=orjson.OPT_INDENT_2)
            write_file.write(serialized_glyf)

    def get_pronunciations_to_glyf_table(self):
        return self.pinyin_glyf
    