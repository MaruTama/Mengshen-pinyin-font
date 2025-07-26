# -*- coding: utf-8 -*-
# !/usr/bin/env python

from __future__ import annotations

from typing import Dict, List, Union

import orjson

from refactored.config.font_config import (
    METADATA_FOR_HAN_SERIF,
    METADATA_FOR_HANDWRITTEN,
    FontType,
)
from refactored.data.pinyin_data import get_pinyin_table_with_mapping_table

# Pinyin glyph data types
GlyphReference = Dict[str, Union[str, int, float]]
PinyinGlyphData = Dict[str, Union[str, int, float, List[GlyphReference]]]


# レガシーコードコメント:
# > advanceHeight に対する advanceHeight の割合 (適当に決めてるから調整)
VERTICAL_ORIGIN_PER_HEIGHT = 0.88
# レガシーコードコメント:
# > ピンインの advanceHeight が無いときは決め打ちで advanceWidth の 1.4 倍にする
HEIGHT_RATE_OF_MONOSPACE = 1.4
# レガシーコードコメント:
# > otfccbuild の仕様なのか opentype の仕様なのか分からないが a と d が同じ値だと、グリフが消失する。
# > 少しでもサイズが違えば反映されるので、反映のためのマジックナンバー
DELTA_4_REFLECTION = 0.001


class PinyinGlyph:
    """Handles pinyin glyph generation and manipulation."""

    def __init__(
        self,
        template_main_json: str,
        alphabet_for_pinyin_json: str,
        font_type: FontType,
    ):
        """
        Initialize PinyinGlyph with required JSON files.

        Args:
            template_main_json: Path to main template JSON file
            alphabet_for_pinyin_json: Path to alphabet JSON file for pinyin
            font_type: Font type (HAN_SERIF or HANDWRITTEN)
        """
        self.pinyin_mapping_table = get_pinyin_table_with_mapping_table()

        with open(template_main_json, "rb") as read_file:
            self.font_main = orjson.loads(read_file.read())
            self.cmap_table = self.font_main["cmap"]

        with open(alphabet_for_pinyin_json, "rb") as read_file:
            self.py_alphabet_glyf = orjson.loads(read_file.read())

        if font_type == FontType.HAN_SERIF:
            # 想定する漢字のサイズに対するピンイン表示部のサイズ
            # 前作より引用
            self.metadata_for_pinyin = METADATA_FOR_HAN_SERIF
        elif font_type == FontType.HANDWRITTEN:
            self.metadata_for_pinyin = METADATA_FOR_HANDWRITTEN
        else:
            raise ValueError(f"Unsupported font type: {font_type}")

        # 発音の参照をもつ e.g.: {"làng":ref}
        self.pronunciations: Dict[str, PinyinGlyphData] = {}

    def __get_advance_size_of_hanzi(self) -> tuple[int, int]:
        """マージ先のフォントの漢字サイズを返す"""

        # レガシーコードコメント:
        # > マージ先のフォントの漢字サイズを返す
        # > なんでもいいが、とりあえず漢字の「一」でサイズを取得する
        reference_hanzi_unicode = str(ord("一"))
        reference_cid = self.font_main["cmap"][reference_hanzi_unicode]

        hanzi_advance_width = self.font_main["glyf"][reference_cid]["advanceWidth"]
        # レガシーコードコメント:
        # > ピンインがキャンバスに収まる scale を求める.
        # > 等幅フォントであれば大きさは同じなのでどんな文字でも同じだと思うが、一応最も背の高い文字を指定する (多分 ǘ ǚ ǜ)
        if "advanceHeight" in self.font_main["glyf"][reference_cid]:
            hanzi_advance_height = self.font_main["glyf"][reference_cid][
                "advanceHeight"
            ]
        else:
            hanzi_advance_height = hanzi_advance_width * HEIGHT_RATE_OF_MONOSPACE
        return hanzi_advance_width, hanzi_advance_height

    def __get_advance_size_of_pinyin(self, pronunciation: str) -> tuple[int, int]:
        """ピンインの文字列のサイズを返す"""
        total_pinyin_width = 0
        max_pinyin_height = 0

        for pinyin_char in pronunciation:
            if pinyin_char in self.py_alphabet_glyf:
                char_glyph_info = self.py_alphabet_glyf[pinyin_char]
                char_width = char_glyph_info.get("advanceWidth", 0)
                char_height = char_glyph_info.get("advanceHeight", 0)

                total_pinyin_width += char_width
                if char_height > max_pinyin_height:
                    max_pinyin_height = char_height

        return total_pinyin_width, max_pinyin_height

    def get_pinyin_glyph_for_hanzi(self, hanzi: str) -> PinyinGlyphData:
        """漢字に対応するピンイングリフを生成"""
        pinyins = self.pinyin_mapping_table.get(hanzi, [])
        if not pinyins:
            return {}

        # 最初の発音を使用（複数ある場合は別途GSUBで処理）
        pronunciation = pinyins[0]

        if pronunciation in self.pronunciations:
            result = self.pronunciations[pronunciation]
            if isinstance(result, dict):
                return result
            return {}

        # 新しい発音のグリフを作成
        glyph_data = self._create_pinyin_glyph(pronunciation)
        self.pronunciations[pronunciation] = glyph_data

        return glyph_data

    def _create_pinyin_glyph(self, pronunciation: str) -> PinyinGlyphData:
        """発音文字列からピンイングリフを作成"""
        # レガシーコードコメント:
        # pinyin_width は拼音に使用する一文字の幅（等幅なので全て同じはず）
        hanzi_width, hanzi_height = self.__get_advance_size_of_hanzi()
        pinyin_width, pinyin_height = self.__get_advance_size_of_pinyin(pronunciation)

        # キャンバスサイズの調整
        canvas_width = self.metadata_for_pinyin.pinyin_canvas.width
        canvas_height = self.metadata_for_pinyin.pinyin_canvas.height

        # スケールファクターの計算
        scale_x = canvas_width / pinyin_width if pinyin_width > 0 else 1.0
        scale_y = canvas_height / pinyin_height if pinyin_height > 0 else 1.0

        # TODO: レガシーコードと処理が違うので確認する
        # 　　pinyin_glyph.py の __get_pinyin_position_on_canvas()
        # レガシーコードコメント:
        # > 文字数が 6 なら横幅最大にする

        # 重なりを避けるモードの適用
        if (
            self.metadata_for_pinyin.is_avoid_overlapping_mode
            and len(pronunciation) >= 5
        ):
            scale_x *= (
                1.0 - self.metadata_for_pinyin.x_scale_reduction_for_avoid_overlapping
            )

        # グリフデータの構築
        composite_glyph_data: PinyinGlyphData = {
            "advanceWidth": hanzi_width,
            "advanceHeight": hanzi_height,
            "contours": [],
            "references": [],
            "instructions": [],
        }
        # レガシーコードコメント:
        # > a-d ってなんだ？
        # > > The transformation entries determine the values of an affine transformation applied to
        # > the component prior to its being incorporated into the parent glyph.
        # >
        # > Given the component matrix [a b c d e f], the transformation applied to the component is:
        # > [The 'glyf' table](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6glyf.html)
        # > [FontConfigの​matrix​フォント​プロパティを​利用して​字体を​変化させる​方法](http://ie.pcgw.pgw.jp/2015/10/17/fontconfig-matrix.html)
        # >
        # > otfccbuild の仕様なのか opentype の仕様なのか分からないが
        # > a と d が同じ値だと、グリフが消失する。 少しでもサイズが違えば反映される。
        # なので、90% にするなら、a=0.9, d=0.91 とかにする。

        # 各文字のグリフを配置
        current_x_position = 0
        for char in pronunciation:
            if char in self.py_alphabet_glyf:
                char_glyph_data = self.py_alphabet_glyf[char]

                # 参照を追加
                if "references" in composite_glyph_data and isinstance(
                    composite_glyph_data["references"], list
                ):
                    composite_glyph_data["references"].append(
                        {
                            "glyph": char,
                            "x": float(current_x_position * scale_x),
                            "y": float(
                                self.metadata_for_pinyin.pinyin_canvas.base_line
                            ),
                            "a": float(scale_x),
                            "b": 0.0,
                            "c": 0.0,
                            "d": float(scale_y),
                        }
                    )

                current_x_position += char_glyph_data.get("advanceWidth", 0)

        return composite_glyph_data

    def get_all_pinyin_glyphs(self) -> Dict[str, PinyinGlyphData]:
        """すべてのピンイングリフを取得"""
        all_glyphs = {}

        for hanzi, pinyins in self.pinyin_mapping_table.items():
            for pronunciation in pinyins:
                if pronunciation not in all_glyphs:
                    all_glyphs[pronunciation] = self._create_pinyin_glyph(pronunciation)

        return all_glyphs
