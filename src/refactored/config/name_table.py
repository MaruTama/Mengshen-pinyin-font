# -*- coding: utf-8 -*-
"""Font name table configuration for OpenType name table generation."""

from __future__ import annotations

from typing import List, TypedDict

from .. import __version__
from ..utils.version_utils import parse_version_to_float


class FontNameEntry(TypedDict):
    """Typed dictionary for font name table entries."""

    platformID: int
    encodingID: int
    languageID: int
    nameID: int
    nameString: str


VERSION = parse_version_to_float(__version__)


# Font name table data for han_serif font
HAN_SERIF: List[FontNameEntry] = [
    # Macintosh Platform
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 0,
        "nameString": "Copyright © 2017 Adobe Systems Incorporated (http://www.adobe.com/), with Reserved Font Name 'Source'.\n[萌神PROJECT] Copyright(c) 2020 mengshen project",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 1,
        "nameString": "Mengshen-HanSerif",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 2,
        "nameString": "Regular",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 3,
        "nameString": f"{VERSION};MENGSHEN;Mengshen-HanSerif",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 4,
        "nameString": "Mengshen-HanSerif",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 5,
        "nameString": f"Version {VERSION}",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 6,
        "nameString": "Mengshen-HanSerif-CN",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 7,
        "nameString": "Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 8,
        "nameString": "Adobe Systems Incorporated",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 9,
        "nameString": "[Source Han Sans]\nRyoko NISHIZUKA (kana & ideographs); Frank Grießhammer (Latin, Greek & Cyrillic); Wenlong ZHANG (bopomofo); Sandoll Communications, Soohyun PARK, Yejin WE & Donghoon HAN (hangul elements, letters & syllables)\n[mengshen project] Yuya Maruyama",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 10,
        "nameString": "Dr. Ken Lunde (project architect, glyph set definition & overall production); Masataka HATTORI (production & ideograph elements)",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 11,
        "nameString": "http://www.mengshen-project.com/",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 13,
        "nameString": 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the SIL Open Font License for the specific language, permissions and limitations governing your use of this Font Software.',
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 14,
        "nameString": "http://scripts.sil.org/OFL",
    },
    # Microsoft Platform
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 0,
        "nameString": "Copyright © 2017 Adobe Systems Incorporated (http://www.adobe.com/), with Reserved Font Name 'Source'.\n[萌神PROJECT] Copyright(c) 2020 mengshen project",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 1,
        "nameString": "Mengshen-Regular",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 2,
        "nameString": "Regular",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 3,
        "nameString": f"{VERSION};MENGSHEN;Mengshen-HanSerif",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 4,
        "nameString": "Mengshen-HanSerif",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 5,
        "nameString": f"Version {VERSION}",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 6,
        "nameString": "Mengshen-HanSerif-CN",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 7,
        "nameString": "Source is a trademark of Adobe Systems Incorporated in the United States and/or other countries.",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 9,
        "nameString": "[Source Han Sans]\nRyoko NISHIZUKA 西塚涼子 (kana & ideographs); Paul D. Hunt (Latin, Greek & Cyrillic); Wenlong ZHANG 张文龙 (bopomofo); Sandoll Communication 산돌커뮤니케이션, Soo-young JANG 장수영 & Joo-yeon KANG 강주연 (hangul elements, letters & syllables)\n[mengshen project] Yuya Maruyama 丸山裕也 (Tama)",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 10,
        "nameString": "Dr. Ken Lunde (project architect, glyph set definition & overall production); Masataka HATTORI 服部正貴 (production & ideograph elements)",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 11,
        "nameString": "http://www.mengshen-project.com/",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 13,
        "nameString": 'This Font Software is licensed under the SIL Open Font License, Version 1.1. This Font Software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the SIL Open Font License for the specific language, permissions and limitations governing your use of this Font Software.',
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 14,
        "nameString": "http://scripts.sil.org/OFL",
    },
    # Japanese names
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


# Font name table data for handwritten font
HANDWRITTEN: List[FontNameEntry] = [
    # Macintosh Platform
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 0,
        "nameString": "[萌神PROJECT] Copyright(c) 2020 mengshen project with Copyright © 2020 LXGW",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 1,
        "nameString": "Mengshen-Handwritten",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 2,
        "nameString": "Regular",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 3,
        "nameString": f"{VERSION};MENGSHEN;Mengshen-Handwritten",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 4,
        "nameString": "Mengshen-Handwritten",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 5,
        "nameString": f"Version {VERSION}",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 6,
        "nameString": "Mengshen-Handwritten-SC",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 7,
        "nameString": "萌神 手写体 SC",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 9,
        "nameString": "Nozomi Seto \n Yuya Maruyama",
    },
    {
        "platformID": 1,
        "encodingID": 0,
        "languageID": 0,
        "nameID": 11,
        "nameString": "http://www.mengshen-project.com/",
    },
    # Microsoft Platform
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 0,
        "nameString": "[萌神PROJECT] Copyright © 2020 mengshen project with Copyright © 2020 LXGW",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 1,
        "nameString": "Mengshen-Handwritten",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 2,
        "nameString": "Regular",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 3,
        "nameString": f"{VERSION};MENGSHEN;Mengshen-Handwritten",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 4,
        "nameString": "Mengshen-Handwritten",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 5,
        "nameString": f"Version {VERSION}",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 6,
        "nameString": "Mengshen-Handwritten-SC",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 7,
        "nameString": "萌神 手写体 SC",
    },
    {
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "nameID": 9,
        "nameString": "Nozomi Seto 瀬戸のぞみ \n[mengshen project] Yuya Maruyama 丸山裕也",
    },
    {
        "platformID": 3,
        "encodingID": 0,
        "languageID": 1033,
        "nameID": 11,
        "nameString": "http://www.mengshen-project.com/",
    },
    # Japanese names
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
