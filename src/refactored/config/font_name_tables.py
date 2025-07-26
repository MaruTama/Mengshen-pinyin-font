# -*- coding: utf-8 -*-
# !/usr/bin/env python
# pylint: disable=line-too-long

"""
Font name table definitions migrated from legacy src/name_table.py

This module contains all font name table definitions with complete preservation
of original comments, copyright information, and Japanese documentation.
Migrated to work independently in the refactored architecture.
"""

from __future__ import annotations

from typing import List, TypedDict

from .. import __version__
from ..utils.version_utils import parse_version_to_float
from . import FontType

VERSION = parse_version_to_float(__version__)


class FontNameEntry(TypedDict):
    """Typed dictionary for font name table entries."""

    platformID: int
    encodingID: int
    languageID: int
    nameID: int
    nameString: str


# Font name table constants reference:
#
# platformID:
#   0: Unicode
#   1: Macintosh
#   2: ISO
#   3: Microsoft
#   4: カスタム
#
# encodingID:
#   0: シンボル
#   1: Unicode BMP面のみ
#
# nameID:
#   0:  著作権注釈
#   1:  フォントファミリ名
#   2:  フォントサブファミリ名
#   3:  フォント識別子
#   4:  完全なフォント名
#   5:  バージョン文字列
#   6:  PostScript名
#   7:  商標
#   8:  製造社名
#   9:  デザイナーの名前
#   10: 説明
#   11: ベンダーの URL
#   12: デザイナーの URL
#   13: ライセンス説明
#   14: ライセンス情報の URL

HAN_SERIF: List[FontNameEntry] = [
    # Macintosh
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 0,
        # 著作権注釈
        "nameString": "Copyright © 2017 Adobe Systems Incorporated (http://www.adobe.com/), with Reserved Font Name 'Source'.\n[萌神PROJECT] Copyright(c) 2020 mengshen project",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 1,
        # フォントファミリ名
        "nameString": "Mengshen-HanSerif",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 2,
        # フォントサブファミリ名
        "nameString": "Regular",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 3,
        # フォント識別子
        "nameString": f"{VERSION};MENGSHEN;Mengshen-HanSerif",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 4,
        # 完全なフォント名
        "nameString": "Mengshen-HanSerif",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 5,
        # バージョン文字列
        "nameString": f"Version {VERSION}",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 6,
        # PostScript名
        "nameString": "Mengshen-HanSerif-CN",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 7,
        # 商標
        "nameString": "Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 8,
        # 製造社名
        "nameString": "Adobe Systems Incorporated",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 9,
        # デザイナーの名前
        "nameString": "[Source Han Sans]\nRyoko NISHIZUKA  (kana & ideographs); Frank Grießhammer (Latin, Greek & Cyrillic); Wenlong ZHANG  (bopomofo); Sandoll Communications , Soohyun PARK , Yejin WE  & Donghoon HAN  (hangul elements, letters & syllables)\n[mengshen project] Yuya Maruyama",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 10,
        # 説明
        "nameString": "Dr. Ken Lunde (project architect, glyph set definition & overall production); Masataka HATTORI  (production & ideograph elements)",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 11,
        # ベンダーの URL
        "nameString": "http://www.mengshen-project.com/",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 13,
        # ライセンス説明
        "nameString": 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the SIL Open Font License for the specific language, permissions and limitations governing your use of this Font Software.',
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 14,
        # ライセンス情報の URL
        "nameString": "http://scripts.sil.org/OFL",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 0,
        # 著作権注釈
        "nameString": "Copyright © 2017 Adobe Systems Incorporated (http://www.adobe.com/), with Reserved Font Name 'Source'.\n[萌神PROJECT] Copyright(c) 2020 mengshen project",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 1,
        # フォントファミリ名
        "nameString": "Mengshen-Regular",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 2,
        # フォントサブファミリ名
        "nameString": "Regular",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 3,
        # フォント識別子
        "nameString": f"{VERSION};MENGSHEN;Mengshen-HanSerif",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 4,
        # 完全なフォント名
        "nameString": "Mengshen-HanSerif",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 5,
        # バージョン文字列
        "nameString": f"Version {VERSION}",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 6,
        # PostScript名
        "nameString": "Mengshen-HanSerif-CN",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 7,
        # 商標
        "nameString": "Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 9,
        # デザイナーの名前
        "nameString": "[Source Han Sans]\nRyoko NISHIZUKA 西塚涼子 (kana & ideographs); Paul D. Hunt (Latin, Greek & Cyrillic); Wenlong ZHANG 张文龙 (bopomofo); Sandoll Communication 산돌커뮤니케이션, Soo-young JANG 장수영 & Joo-yeon KANG 강주연 (hangul elements, letters & syllables)\n[mengshen project] Yuya Maruyama 丸山裕也 (Tama)",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 10,
        # 説明
        "nameString": "Dr. Ken Lunde (project architect, glyph set definition & overall production); Masataka HATTORI 服部正貴 (production & ideograph elements)",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 11,
        # ベンダーの URL
        "nameString": "http://www.mengshen-project.com/",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 13,
        # ライセンス説明
        "nameString": 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the SIL Open Font License for the specific language, permissions and limitations governing your use of this Font Software.',
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 14,
        # ライセンス情報の URL
        "nameString": "http://scripts.sil.org/OFL",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1041,
        "nameID": 1,
        "nameString": "萌神 明朝体 CN",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1041,
        "nameID": 4,
        "nameString": "萌神 明朝体 CN",
    },
]

HANDWRITTEN: List[FontNameEntry] = [
    # Macintosh
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 0,
        # 著作権注釈
        "nameString": "[萌神PROJECT] Copyright(c) 2020 mengshen project with Copyright © 2020 LXGW",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 1,
        # フォントファミリ名
        "nameString": "Mengshen-Handwritten",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 2,
        # フォントサブファミリ名
        "nameString": "Regular",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 3,
        # フォント識別子
        "nameString": f"{VERSION};MENGSHEN;Mengshen-Handwritten",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 4,
        # 完全なフォント名
        "nameString": "Mengshen-Handwritten",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 5,
        # バージョン文字列
        "nameString": f"Version {VERSION}",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 6,
        # PostScript名
        "nameString": "Mengshen-Handwritten-SC",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 7,
        # 商標
        "nameString": "萌神 手写体 SC",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 9,
        # デザイナーの名前
        "nameString": "Nozomi Seto \n Yuya Maruyama",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 11,
        # ベンダーの URL
        "nameString": "http://www.mengshen-project.com/",
    },
    # Microsoft
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 0,
        # 著作権注釈
        "nameString": "[萌神PROJECT] Copyright © 2020 mengshen project with Copyright © 2020 LXGW",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 1,
        # フォントファミリ名
        "nameString": "Mengshen-Handwritten",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 2,
        # フォントサブファミリ名
        "nameString": "Regular",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 3,
        # フォント識別子
        "nameString": f"{VERSION};MENGSHEN;Mengshen-Handwritten",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 4,
        # 完全なフォント名
        "nameString": "Mengshen-Handwritten",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 5,
        # バージョン文字列
        "nameString": f"Version {VERSION}",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 6,
        # PostScript名
        "nameString": "Mengshen-Handwritten-SC",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 7,
        # 商標
        "nameString": "萌神 手写体 SC",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 9,
        # デザイナーの名前
        "nameString": "Nozomi Seto 瀬戸のぞみ \n[mengshen project] Yuya Maruyama 丸山裕也",
    },
    {
        "platformID": 3,
        "encodingID": 0,
        "languageID": 1033,
        "nameID": 11,
        # ベンダーの URL
        "nameString": "http://www.mengshen-project.com/",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1041,
        "nameID": 1,
        "nameString": "萌神 手写体 CN",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1041,
        "nameID": 4,
        "nameString": "萌神 手写体 CN",
    },
]


class FontNameTableManager:
    """Manager for font name table operations with backward compatibility."""

    @staticmethod
    def get_han_serif_name_table() -> List[FontNameEntry]:
        """Get HAN_SERIF name table entries."""
        return HAN_SERIF

    @staticmethod
    def get_handwritten_name_table() -> List[FontNameEntry]:
        """Get HANDWRITTEN name table entries."""
        return HANDWRITTEN

    @staticmethod
    def get_name_table_by_font_type(
        font_type: FontType,
    ) -> List[FontNameEntry]:
        """Get name table entries by font type."""

        if font_type == FontType.HAN_SERIF:
            return HAN_SERIF
        if font_type == FontType.HANDWRITTEN:
            return HANDWRITTEN
        raise ValueError(f"Unknown font type: {font_type}")


# Legacy exports for backward compatibility
def get_han_serif_name_table() -> List[FontNameEntry]:
    """Legacy function wrapper."""
    return FontNameTableManager.get_han_serif_name_table()


def get_handwritten_name_table() -> List[FontNameEntry]:
    """Legacy function wrapper."""
    return FontNameTableManager.get_handwritten_name_table()
