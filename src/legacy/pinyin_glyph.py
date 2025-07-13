# -*- coding: utf-8 -*-
#!/usr/bin/env python

import config
import orjson
import pinyin_getter as pg
import shell
import utility

# advanceHeight に対する advanceHeight の割合 (適当に決めてるから調整)
VERTICAL_ORIGIN_PER_HEIGHT = 0.88
# ピンインの advanceHeight が無いときは決め打ちで advanceWidth の 1.4 倍にする
HEIGHT_RATE_OF_MONOSPACE = 1.4
# otfccbuild の仕様なのか opentype の仕様なのか分からないが a と d が同じ値だと、グリフが消失する。
# 少しでもサイズが違えば反映されるので、反映のためのマジックナンバー
DELTA_4_REFLECTION = 0.001


class PinyinGlyph:

    # マージ先のフォントのメインjson（フォントサイズを取得するため）, ピンイン表示に使うためのglyfのjson, ピンインのグリフを追加したjson(出力ファイル)
    def __init__(self, TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON, FONT_TYPE):
        self.PINYIN_MAPPING_TABLE = pg.get_pinyin_table_with_mapping_table()

        with open(TAMPLATE_MAIN_JSON, "rb") as read_file:
            self.font_main = orjson.loads(read_file.read())
            self.cmap_table = self.font_main["cmap"]
        with open(ALPHABET_FOR_PINYIN_JSON, "rb") as read_file:
            self.PY_ALPHABET_GLYF = orjson.loads(read_file.read())

        if FONT_TYPE == config.HAN_SERIF_TYPE:
            # 想定する漢字のサイズに対するピンイン表示部のサイズ
            # # 前作より引用
            self.METADATA_FOR_PINYIN = config.METADATA_FOR_HAN_SERIF
        elif FONT_TYPE == config.HANDWRITTEN_TYPE:
            self.METADATA_FOR_PINYIN = config.METADATA_FOR_HANDWRITTEN
        else:
            pass

        # 発音の参照をもつ e.g.: {"làng":ref}
        self.pronunciations = {}

    # マージ先のフォントの漢字サイズを返す
    def __get_advance_size_of_hanzi(self):
        # なんでもいいが、とりあえず漢字の「一」でサイズを取得する
        cid = self.font_main["cmap"][str(ord("一"))]
        advanceWidth = self.font_main["glyf"][cid]["advanceWidth"]
        advanceHeight = (
            self.font_main["glyf"][cid]["advanceHeight"]
            if "advanceHeight" in self.font_main["glyf"][cid]
            else advanceWidth
        )
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
    def add_references_of_pronunciation(self):
        (target_advance_width_of_hanzi, target_advance_height_of_hanzi) = (
            self.__get_advance_size_of_hanzi()
        )
        pronunciations = self.__get_pronunciations()

        """
        a-d ってなんだ？
        > The transformation entries determine the values of an affine transformation applied to 
        the component prior to its being incorporated into the parent glyph. 
        Given the component matrix [a b c d e f], the transformation applied to the component is:

        [The 'glyf' table](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6glyf.html)
        [FontConfigの​matrix​フォント​プロパティを​利用して​字体を​変化させる​方法](http://ie.pcgw.pgw.jp/2015/10/17/fontconfig-matrix.html)


        otfccbuild の仕様なのか opentype の仕様なのか分からないが
        a と d が同じ値だと、グリフが消失する。 少しでもサイズが違えば反映される。
        なので、90% にするなら、a=0.9, d=0.91 とかにする。
        """
        # 追加したいフォントのサイズに合わせるために scale を求める
        hanzi_canvas_width_scale = (
            target_advance_width_of_hanzi
            / self.METADATA_FOR_PINYIN["expected_hanzi_canvas"]["width"]
        )
        hanzi_canvas_height_scale = (
            target_advance_height_of_hanzi
            / self.METADATA_FOR_PINYIN["expected_hanzi_canvas"]["height"]
        )

        # 追加したいフォント上でのピンイン表示部サイズを求める
        target_pinyin_canvas_width = (
            self.METADATA_FOR_PINYIN["pinyin_canvas"]["width"]
            * hanzi_canvas_width_scale
        )
        target_pinyin_canvas_height = (
            self.METADATA_FOR_PINYIN["pinyin_canvas"]["height"]
            * hanzi_canvas_height_scale
        )
        target_pinyin_canvas_base_line = (
            self.METADATA_FOR_PINYIN["pinyin_canvas"]["base_line"]
            * hanzi_canvas_height_scale
        )
        target_pinyin_canvas_tracking = (
            self.METADATA_FOR_PINYIN["pinyin_canvas"]["tracking"]
            * hanzi_canvas_width_scale
        )

        # ピンインがキャンバスに収まる scale を求める.
        # 等幅フォントであれば大きさは同じなのでどんな文字でも同じだと思うが、一応最も背の高い文字を指定する (多分 ǘ ǚ ǜ)
        py_alphablet_v3_of_glyf = self.PY_ALPHABET_GLYF["py_alphablet_v3"]
        advanceHeight = (
            py_alphablet_v3_of_glyf["advanceHeight"]
            if "advanceHeight" in py_alphablet_v3_of_glyf
            else py_alphablet_v3_of_glyf["advanceWidth"] * HEIGHT_RATE_OF_MONOSPACE
        )
        pinyin_scale = target_pinyin_canvas_height / advanceHeight

        # ピンイン表示部に文字を詰めていく
        # 各文字の配置を計算する
        pinyin_width = (
            self.PY_ALPHABET_GLYF["py_alphablet_v3"]["advanceWidth"] * pinyin_scale
        )

        for pronunciation in pronunciations:
            # 引数多いから、クラス内のローカル変数にしようかと思ったけど、明示的にコメント入れておいて役割を示すのもいいかな
            # ピンイン表示部(target_pinyin_canvas_width)に収まるように等間隔に配置する
            width_positions = self.__get_pinyin_position_on_canvas(
                pronunciation,
                pinyin_width,
                target_pinyin_canvas_width,
                target_pinyin_canvas_tracking,
                target_advance_width_of_hanzi,
            )
            self.__add_pronunciation(
                pronunciation,
                width_positions,
                target_advance_width_of_hanzi,
                pinyin_scale,
                target_pinyin_canvas_height,
                target_pinyin_canvas_base_line,
            )

    """
    各文字の座標を計算する
    """

    def __get_pinyin_position_on_canvas(
        self,
        pronunciation,  # pinyin の発音 (e.g.: láng)
        pinyin_width,  # ピンインに使用する一文字の幅（等幅なので全て同じはず）
        canvas_width,  # 表示部の幅（METADATA_FOR_PINYINで指定）
        canvas_tracking,  # 最大文字間幅（METADATA_FOR_PINYINで指定）
        target_advance_width_of_hanzi,
    ):  # マージ先のフォントの幅（漢字なら正方形のはず）
        is_avoid_overlapping_mode = self.METADATA_FOR_PINYIN[
            "is_avoid_overlapping_mode"
        ]
        # 文字数が 6 なら横幅最大にする
        if is_avoid_overlapping_mode and len(pronunciation) >= 6:
            canvas_width = target_advance_width_of_hanzi
        # 空白数 1文字のときは1，それ以外はlen(pinyin)
        blank_num = 1 if len(pronunciation) == 1 else len(pronunciation) - 1
        # 空白幅の設定
        # canvas_tracking を空白幅の上限としている
        tmp = (canvas_width - pinyin_width * len(pronunciation)) / blank_num
        blank_width = tmp if tmp < canvas_tracking else canvas_tracking
        # 拼音全幅 [mm]
        arranged_pinyin_width = (len(pronunciation) * pinyin_width) + (
            blank_num * blank_width
        )
        # 中央寄せ. x軸上の開始位置
        start_x = (target_advance_width_of_hanzi - arranged_pinyin_width) / 2

        pinyin_positions = []
        # 各文字の座標を計算する
        for idx in range(len(pronunciation)):
            pinyin_positions.append(
                round(((start_x + pinyin_width * idx) + idx * blank_width), 2)
            )

        return pinyin_positions

    def __add_pronunciation(
        self,
        pronunciation,  # pinyin の発音 (e.g.: láng)
        width_positions,  # ピンインの各文字の座標のリスト
        target_advance_width_of_hanzi,  # マージ先のフォントの漢字の幅
        pinyin_scale,  # ピンインのグリフの縮小率
        target_pinyin_canvas_height,  # ピンイン表示部の高さ
        target_pinyin_canvas_base_line,
    ):  # 基準点からピンイン表示部までの高さ
        references = []
        for i in range(len(pronunciation)):
            simpled_alphabet = utility.simplification_pronunciation(pronunciation[i])
            x_position = width_positions[i]
            y_position = target_pinyin_canvas_base_line
            is_avoid_overlapping_mode = self.METADATA_FOR_PINYIN[
                "is_avoid_overlapping_mode"
            ]
            x_scale_reduction_for_avoid_overlapping = self.METADATA_FOR_PINYIN[
                "x_scale_reduction_for_avoid_overlapping"
            ]
            x_scale = round(pinyin_scale, 3)
            if is_avoid_overlapping_mode and len(pronunciation) >= 5:
                x_scale -= x_scale_reduction_for_avoid_overlapping

            y_scale = round(pinyin_scale + DELTA_4_REFLECTION, 3)
            references.append(
                {
                    "glyph": "py_alphablet_{}".format(simpled_alphabet),
                    "x": x_position,
                    "y": y_position,
                    "a": x_scale,
                    "b": 0,
                    "c": 0,
                    "d": y_scale,
                }
            )

        (_, target_advance_height_of_hanzi) = self.__get_advance_size_of_hanzi()
        simpled_pronunciation = utility.simplification_pronunciation(pronunciation)
        advanceHeight = round(
            target_advance_height_of_hanzi + target_pinyin_canvas_height, 2
        )
        pronunciation = {
            simpled_pronunciation: {
                "advanceWidth": target_advance_width_of_hanzi,
                "advanceHeight": advanceHeight,
                "verticalOrigin": advanceHeight * VERTICAL_ORIGIN_PER_HEIGHT,
                "references": references,
            }
        }
        self.pronunciations.update(pronunciation)

    # 確認のために使う。生成時には利用しない。
    def save_json(self, OUTPUT_JSON):
        tmp_pinyin_glyf = self.PY_ALPHABET_GLYF
        # 発音のグリフも確認するために出力する. 一文字の発音のときに重複しないように名前に arranged_ と付ける。
        for simpled_pronunciation, data in self.pronunciations.items():
            tmp_pinyin_glyf.update({"arranged_{}".format(simpled_pronunciation): data})

        with open(OUTPUT_JSON, "wb") as write_file:
            serialized_glyf = orjson.dumps(tmp_pinyin_glyf, option=orjson.OPT_INDENT_2)
            write_file.write(serialized_glyf)
        print("ピンイン確認用jsonを出力！")

    def get_py_alphablet_glyf_table(self):
        return self.PY_ALPHABET_GLYF

    def get_pronunciation_glyf_table(self):
        return self.pronunciations
