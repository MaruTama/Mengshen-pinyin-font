# -*- coding: utf-8 -*-
# !/usr/bin/env python

from __future__ import annotations

from typing import Dict, List, Union

# Pinyin glyph data types
GlyphReference = Dict[str, Union[str, int, float]]
PinyinGlyphData = Dict[str, Union[str, int, float, List[GlyphReference]]]

import orjson

from refactored.config.font_config import (
    METADATA_FOR_HAN_SERIF,
    METADATA_FOR_HANDWRITTEN,
    FontType,
)
from refactored.data.pinyin_data import get_pinyin_table_with_mapping_table

# advanceHeight に対する advanceHeight の割合 (適当に決めてるから調整)
VERTICAL_ORIGIN_PER_HEIGHT = 0.88
# ピンインの advanceHeight が無いときは決め打ちで advanceWidth の 1.4 倍にする
HEIGHT_RATE_OF_MONOSPACE = 1.4
# otfccbuild の仕様なのか opentype の仕様なのか分からないが a と d が同じ値だと、グリフが消失する。
# 少しでもサイズが違えば反映されるので、反映のためのマジックナンバー
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
        self.PINYIN_MAPPING_TABLE = get_pinyin_table_with_mapping_table()

        with open(template_main_json, "rb") as read_file:
            self.font_main = orjson.loads(read_file.read())
            self.cmap_table = self.font_main["cmap"]

        with open(alphabet_for_pinyin_json, "rb") as read_file:
            self.PY_ALPHABET_GLYF = orjson.loads(read_file.read())

        if font_type == FontType.HAN_SERIF:
            # 想定する漢字のサイズに対するピンイン表示部のサイズ
            # 前作より引用
            self.METADATA_FOR_PINYIN = METADATA_FOR_HAN_SERIF
        elif font_type == FontType.HANDWRITTEN:
            self.METADATA_FOR_PINYIN = METADATA_FOR_HANDWRITTEN
        else:
            raise ValueError(f"Unsupported font type: {font_type}")

        # 発音の参照をもつ e.g.: {"làng":ref}
        self.pronunciations: Dict[str, PinyinGlyphData] = {}

    def __get_advance_size_of_hanzi(self) -> tuple[int, int]:
        """マージ先のフォントの漢字サイズを返す"""
        # なんでもいいが、とりあえず漢字の「一」でサイズを取得する
        cid = self.font_main["cmap"][str(ord("一"))]
        advance_width = self.font_main["glyf"][cid]["advanceWidth"]
        if "advanceHeight" in self.font_main["glyf"][cid]:
            advance_height = self.font_main["glyf"][cid]["advanceHeight"]
        else:
            advance_height = advance_width * HEIGHT_RATE_OF_MONOSPACE
        return advance_width, advance_height

    def __get_advance_size_of_pinyin(self, pronunciation: str) -> tuple[int, int]:
        """ピンインの文字列のサイズを返す"""
        advance_width = 0
        advance_height = 0

        for char in pronunciation:
            if char in self.PY_ALPHABET_GLYF:
                glyph_info = self.PY_ALPHABET_GLYF[char]
                advance_width += glyph_info.get("advanceWidth", 0)
                char_height = glyph_info.get("advanceHeight", 0)
                if char_height > advance_height:
                    advance_height = char_height

        return advance_width, advance_height

    def get_pinyin_glyph_for_hanzi(self, hanzi: str) -> PinyinGlyphData:
        """漢字に対応するピンイングリフを生成"""
        pinyins = self.PINYIN_MAPPING_TABLE.get(hanzi, [])
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
        hanzi_width, hanzi_height = self.__get_advance_size_of_hanzi()
        pinyin_width, pinyin_height = self.__get_advance_size_of_pinyin(pronunciation)

        # キャンバスサイズの調整
        canvas_width = self.METADATA_FOR_PINYIN.pinyin_canvas.width
        canvas_height = self.METADATA_FOR_PINYIN.pinyin_canvas.height

        # スケールファクターの計算
        scale_x = canvas_width / pinyin_width if pinyin_width > 0 else 1.0
        scale_y = canvas_height / pinyin_height if pinyin_height > 0 else 1.0

        # 重なりを避けるモードの適用
        if (
            self.METADATA_FOR_PINYIN.is_avoid_overlapping_mode
            and len(pronunciation) >= 5
        ):
            scale_x *= (
                1.0 - self.METADATA_FOR_PINYIN.x_scale_reduction_for_avoid_overlapping
            )

        # グリフデータの構築
        glyph_data = {
            "advanceWidth": hanzi_width,
            "advanceHeight": hanzi_height,
            "contours": [],
            "references": [],
            "instructions": [],
        }

        # 各文字のグリフを配置
        x_offset = 0
        for char in pronunciation:
            if char in self.PY_ALPHABET_GLYF:
                char_glyph = self.PY_ALPHABET_GLYF[char]

                # 参照を追加
                if "references" in glyph_data and isinstance(
                    glyph_data["references"], list
                ):
                    glyph_data["references"].append(
                        {
                            "glyph": char,
                            "x": x_offset * scale_x,
                            "y": self.METADATA_FOR_PINYIN.pinyin_canvas.base_line,
                            "scaleX": scale_x,
                            "scaleY": scale_y,
                        }
                    )

                x_offset += char_glyph.get("advanceWidth", 0)

        return glyph_data

    def get_all_pinyin_glyphs(self) -> Dict[str, PinyinGlyphData]:
        """すべてのピンイングリフを取得"""
        all_glyphs = {}

        for hanzi, pinyins in self.PINYIN_MAPPING_TABLE.items():
            for pronunciation in pinyins:
                if pronunciation not in all_glyphs:
                    all_glyphs[pronunciation] = self._create_pinyin_glyph(pronunciation)

        return all_glyphs
