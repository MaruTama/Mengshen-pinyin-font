# -*- coding: utf-8 -*-
"""GSUB table generation with exact legacy compatibility."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, cast

import orjson

from ..config import FontConstants
from ..data import CharacterDataManager, MappingDataManager

# Import pattern data types from font_types
from ..font_types import (
    ChainingRule,
    ChainingRuleApply,
    CmapTable,
    ExceptionPatternData,
    GSUBTable,
    PatternOneData,
    PatternTwoData,
)

# Import utility functions
from ..utils.cmap_utils import convert_hanzi_to_cid_safe
from ..utils.logging_config import get_logger


class GSUBTableGenerator:
    """Generates GSUB table matching legacy structure exactly."""

    def __init__(
        self,
        pattern_one_path: Path,
        pattern_two_path: Path,
        exception_pattern_path: Path,
        character_manager: CharacterDataManager,
        mapping_manager: MappingDataManager,
        cmap_table: CmapTable,
    ):
        """Initialize with pattern files and data managers."""
        self.pattern_one_path = pattern_one_path
        self.pattern_two_path = pattern_two_path
        self.exception_pattern_path = exception_pattern_path
        self.character_manager = character_manager
        self.mapping_manager = mapping_manager
        self.cmap_table = cmap_table
        self.logger = get_logger("mengshen.gsub_table")

        # Track dynamically created lookups
        self.lookup_order: set[str] = set()

        # Pattern data with proper structure
        self.pattern_one: PatternOneData = [
            {}
        ]  # [index][hanzi] = {"variational_pronunciation": str, "patterns": str}
        self.pattern_two: PatternTwoData = {}
        self.exception_pattern: ExceptionPatternData = {}

        # レガシーコードコメント:
        # > calt も rclt も featute の数が多いと有効にならない。 feature には上限がある？ので、今は初期化して使う
        # > rclt は calt と似ていて、かつ無効にできないタグ

        # レガシーコードコメント:
        # > feature ごとに使用する lookup table を指定する
        # > rclt_00000/rclt_00001 は lookup_rclt_0, lookup_rclt_1, lookup_rclt_2 を使用
        self.gsub_data: GSUBTable = {
            # レガシーコードコメント:
            # > 文字体系 ごとに使用する feature を指定する
            "languages": {
                "DFLT_DFLT": {"features": ["aalt_00000", "rclt_00000"]},
                # レガシーコードコメント:
                # > 'hani' = CJK (中国語/日本語/韓国語)
                "hani_DFLT": {"features": ["aalt_00001", "rclt_00001"]},
            },
            # feature ごとに使用する lookup table を指定する
            "features": {
                "aalt_00000": ["lookup_aalt_0", "lookup_aalt_1"],
                "aalt_00001": ["lookup_aalt_0", "lookup_aalt_1"],
                "rclt_00000": ["lookup_rclt_0", "lookup_rclt_1", "lookup_rclt_2"],
                "rclt_00001": ["lookup_rclt_0", "lookup_rclt_1", "lookup_rclt_2"],
            },
            "lookups": {
                # aalt_0 は拼音が一つのみの漢字 + 記号とか。置き換え対象が一つのみのとき
                "lookup_aalt_0": {
                    "type": "gsub_single",
                    "flags": {},
                    "subtables": [{}],
                },
                # aalt_1 は拼音が複数の漢字
                "lookup_aalt_1": {
                    "type": "gsub_alternate",
                    "flags": {},
                    "subtables": [{}],
                },
                # pattern one
                "lookup_rclt_0": {
                    "type": "gsub_chaining",
                    "flags": {},
                    "subtables": [],
                },
                # pattern two
                "lookup_rclt_1": {
                    "type": "gsub_chaining",
                    "flags": {},
                    "subtables": [],
                },
                # exception pattern
                "lookup_rclt_2": {
                    "type": "gsub_chaining",
                    "flags": {},
                    "subtables": [],
                },
            },
            "lookupOrder": [
                "lookup_aalt_0",
                "lookup_aalt_1",
                "lookup_rclt_0",
                "lookup_rclt_1",
                "lookup_rclt_2",
            ],
        }

    def generate_gsub_table(self) -> GSUBTable:
        """Generate complete GSUB table."""
        # Load pattern files
        self._load_pattern_data()

        # Generate features in legacy order
        self._make_aalt_feature()
        self._make_rclt0_feature()  # Pattern one -> updates lookup_rclt_0
        self._make_rclt1_feature()  # Pattern two -> updates lookup_rclt_1
        self._make_rclt2_feature()  # Exception pattern -> updates lookup_rclt_2

        # Set final lookup order (matches legacy)
        self._make_lookup_order()

        return self.gsub_data

    def _load_pattern_data(self) -> None:
        """Load pattern files."""
        # Pattern one (single character patterns)
        self.pattern_one = [{}]
        if self.pattern_one_path.exists():
            with open(self.pattern_one_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.rstrip("\n").split(", ")
                    if len(parts) >= 4:
                        str_order, hanzi, pinyin, patterns = parts
                        order = int(str_order)

                        # Skip order 1 (standard pronunciation)
                        # レガシーコードコメント:
                        # > self.PATTERN_ONE_TXT の order = 1 は標準的なピンインなので無視する
                        if order == 1:
                            continue

                        # Order 2+ -> index 0+
                        # レガシーコードコメント:
                        # > 2 から異読のピンイン。添字に使うために -2 して 0 にする。
                        idx = order - 2
                        while len(self.pattern_one) <= idx:
                            self.pattern_one.append({})

                        self.pattern_one[idx][hanzi] = {
                            "variational_pronunciation": pinyin,
                            "patterns": patterns,
                        }

        # Pattern two (multiple character patterns)
        if self.pattern_two_path.exists():
            with open(self.pattern_two_path, "rb") as f:
                self.pattern_two = orjson.loads(f.read())

        # Exception patterns
        if self.exception_pattern_path.exists():
            with open(self.exception_pattern_path, "rb") as f:
                self.exception_pattern = orjson.loads(f.read())

    def _make_aalt_feature(self) -> None:
        """Generate aalt feature."""

        # レガシーコードコメント:
        # > e.g.:
        # > "lookups": {
        # >     "lookup_aalt_0": {
        # >         "type": "gsub_single",
        # >         "flags": {},
        # >         "subtables": [
        # >             {
        # >                 ...
        # >                 "uni4E01": "uni4E01.ss00",
        # >                 "uni4E03": "uni4E03.ss00",
        # >                 "uni4E08": "uni4E08.ss00",
        # >                 ...
        # >             }
        # >         ]
        # >     },
        # >     "lookup_aalt_1": {
        # >         "type": "gsub_alternate",
        # >         "flags": {},
        # >         "subtables": [
        # >             {
        # >                 "uni4E00": [
        # >                     "uni4E00.ss00",
        # >                     "uni4E00.ss01",
        # >                     "uni4E00.ss02"
        # >                 ],
        # >                 "uni4E07": [
        # >                     "uni4E07.ss00",
        # >                     "uni4E07.ss01"
        # >                 ],
        # >                 ...
        # >             }
        # >         ]
        # >     }
        # > }

        aalt_0_subtables = cast(
            Dict[str, str], self.gsub_data["lookups"]["lookup_aalt_0"]["subtables"][0]
        )
        aalt_1_subtables = cast(
            Dict[str, List[str]],
            self.gsub_data["lookups"]["lookup_aalt_1"]["subtables"][0],
        )

        # Single pronunciation characters -> lookup_aalt_0 (legacy method)
        single_pinyin_characters = (
            self.character_manager.get_single_pronunciation_characters()
        )
        for char_info in single_pinyin_characters:
            hanzi = char_info.character
            cid = convert_hanzi_to_cid_safe(hanzi, self.cmap_table)
            if cid:
                aalt_0_subtables[cid] = f"{cid}.ss00"

        self.lookup_order.add("lookup_aalt_0")

        # Multiple pronunciation characters -> lookup_aalt_1 (legacy method)
        multiple_pinyin_characters = (
            self.character_manager.get_multiple_pronunciation_characters()
        )
        for char_info in multiple_pinyin_characters:
            hanzi = char_info.character
            pinyins = char_info.pronunciations
            cid = convert_hanzi_to_cid_safe(hanzi, self.cmap_table)
            if not cid:
                continue
            alternate_list = []
            # ss00 はピンインのないグリフなので、ピンインのグリフは ss01 から ss{len(pinyins)}まで
            for i in range(len(pinyins) + 1):
                alternate_list.append(f"{cid}.ss{i:02d}")

            aalt_1_subtables[cid] = alternate_list

        self.logger.debug(
            "aalt_1 subtables populated with %d entries", len(aalt_1_subtables)
        )

        self.lookup_order.add("lookup_aalt_1")

    def _make_rclt0_feature(self) -> None:
        """Generate pattern one -> creates lookup_11_* tables."""

        # レガシーコードコメント:
        # > self.pattern_one の中身
        # > e.g.:
        # > [
        # >     {
        # >         "行":{
        # >             "variational_pronunciation":"háng",
        # >             "patterns":"[~当|~家|~间|~列|~情|~业|发~|同~|外~|银~|~话|~会|~距]"
        # >         },
        # >         "作":{
        # >             "variational_pronunciation":"zuō",
        # >             "patterns":"[~坊|~弄|~揖]"
        # >         }
        # >     },
        # >     {
        # >         "行":{
        # >             "variational_pronunciation":"hàng",
        # >             "patterns":"[树~子]"
        # >         },
        # >         "作":{
        # >             "variational_pronunciation":"zuó",
        # >             "patterns":"[~料]"
        # >         }
        # >     },
        # >     {
        # >         "行":{
        # >             "variational_pronunciation":"héng",
        # >             "patterns":"[道~]"
        # >         },
        # >         "作":{
        # >             "variational_pronunciation":"zuo",
        # >             "patterns":"[做~]"
        # >         }
        # >     }
        # > ]
        max_num_patterns = len(self.pattern_one)
        # レガシーコードコメント:
        # > ピンインは10通りまでしか対応していません
        if max_num_patterns > 10:
            raise ValueError("Maximum 10 pronunciation patterns supported")

        lookups = self.gsub_data["lookups"]

        # Create lookup_11_* tables (matches legacy naming exactly)
        # pattern_one[0] -> lookup_11_2, pattern_one[1] -> lookup_11_3, etc.
        for idx in range(max_num_patterns):
            lookup_name = f"lookup_11_{idx + 2}"  # Start from lookup_11_2
            lookups[lookup_name] = {
                "type": "gsub_single",
                "flags": {},
                "subtables": [{}],
            }
            self.lookup_order.add(lookup_name)

        # Generate substitution rules for lookup_rclt_0 (pattern one)
        rclt_0_subtables = cast(
            List[ChainingRule], lookups["lookup_rclt_0"]["subtables"]
        )

        for idx in range(max_num_patterns):
            lookup_name = f"lookup_11_{idx + 2}"
            lookup_subtables = cast(
                Dict[str, str], lookups[lookup_name]["subtables"][0]
            )

            for hanzi, pattern_info in self.pattern_one[idx].items():
                if not self.mapping_manager.has_glyph_for_character(hanzi):
                    continue

                cid = convert_hanzi_to_cid_safe(hanzi, self.cmap_table)
                if not cid:
                    continue

                # Add to pattern lookup: cid -> cid.ss{XX} (legacy method)
                ss_index = FontConstants.SS_VARIATIONAL_PRONUNCIATION + idx
                lookup_subtables[cid] = f"{cid}.ss{ss_index:02d}"

                # Process context patterns for rclt_0 (pattern one)
                if isinstance(pattern_info, dict) and "patterns" in pattern_info:
                    patterns_str = pattern_info["patterns"]
                    patterns = patterns_str.strip("[]").split("|")
                    # レガシーコードコメント:
                    # > まとめて記述できるもの
                    # > e.g.:
                    # > sub [uni4E0D uni9280] uni884C' lookup lookup_0 ;
                    # > sub uni884C' lookup lookup_0　[uni4E0D uni9280] ;
                    left_match = [p for p in patterns if p.endswith("~")]
                    right_match = [p for p in patterns if p.startswith("~")]
                    # レガシーコードコメント:
                    # > 一つ一つ記述するもの
                    # > e.g.:
                    # > sub uni85CF' lookup lookup_0 uni7D05 uni82B1 ;
                    other_match = [
                        p
                        for p in patterns
                        if "~" in p and p not in (left_match + right_match)
                    ]

                    # Left context patterns: [context] target'
                    for pattern in left_match:
                        context_char = pattern.replace("~", "")
                        context_cid = convert_hanzi_to_cid_safe(
                            context_char, self.cmap_table
                        )
                        if context_cid:
                            rclt_0_subtables.append(
                                {
                                    "match": [[context_cid], [cid]],
                                    "apply": [{"at": 1, "lookup": lookup_name}],
                                    "inputBegins": 1,
                                    "inputEnds": 2,
                                }
                            )

                    # Right context patterns: target' [context]
                    for pattern in right_match:
                        context_char = pattern.replace("~", "")
                        context_cid = convert_hanzi_to_cid_safe(
                            context_char, self.cmap_table
                        )
                        if context_cid:
                            rclt_0_subtables.append(
                                {
                                    "match": [[cid], [context_cid]],
                                    "apply": [{"at": 0, "lookup": lookup_name}],
                                    "inputBegins": 0,
                                    "inputEnds": 1,
                                }
                            )

                    # Multi-character context patterns
                    for pattern in other_match:
                        if "~" in pattern:
                            at_pos = pattern.index("~")
                            chars = list(pattern.replace("~", hanzi))
                            match_cids = []
                            for char in chars:
                                char_cid = convert_hanzi_to_cid_safe(
                                    char, self.cmap_table
                                )
                                if char_cid:
                                    match_cids.append([char_cid])

                            if match_cids:
                                rclt_0_subtables.append(
                                    {
                                        "match": match_cids,
                                        "apply": [
                                            {"at": at_pos, "lookup": lookup_name}
                                        ],
                                        "inputBegins": at_pos,
                                        "inputEnds": at_pos + 1,
                                    }
                                )

    def _make_rclt1_feature(self) -> None:
        """Generate pattern two -> updates lookup_rclt_1."""
        if not self.pattern_two:
            return

        lookups = self.gsub_data["lookups"]

        # Create additional lookup tables from pattern_two (legacy method)
        if "lookup_table" in self.pattern_two:
            lookup_table = cast(
                Dict[str, Dict[str, str]], self.pattern_two["lookup_table"]
            )
            for lookup_name, table in lookup_table.items():
                lookups[lookup_name] = {
                    "type": "gsub_single",
                    "flags": {},
                    "subtables": [{}],
                }

                # Add substitutions using legacy logic
                lookup_subtables = cast(
                    Dict[str, str], lookups[lookup_name]["subtables"][0]
                )
                for hanzi, target in table.items():
                    cid = convert_hanzi_to_cid_safe(hanzi, self.cmap_table)
                    if cid and isinstance(target, str):
                        # Replace hanzi with cid in target (exact legacy method)
                        target_cid = target.replace(hanzi, cid)
                        lookup_subtables[cid] = target_cid

                self.lookup_order.add(lookup_name)

        # Generate contextual rules for lookup_rclt_1 (pattern two)
        if "patterns" in self.pattern_two:
            rclt_1_subtables = cast(
                List[ChainingRule], lookups["lookup_rclt_1"]["subtables"]
            )
            patterns_dict = cast(
                Dict[str, List[Dict[str, str]]], self.pattern_two.get("patterns", {})
            )

            for phrase, pattern_list in patterns_dict.items():
                applies: List[ChainingRuleApply] = []
                ats = []

                for i, table in enumerate(pattern_list):
                    if isinstance(table, dict) and table:
                        # Legacy: lookup_name = list(table.values())[0]
                        lookup_name = list(table.values())[0]
                        if lookup_name:
                            ats.append(i)
                            applies.append({"at": i, "lookup": lookup_name})

                if applies:
                    match_cids: List[List[str]] = []
                    for char in phrase:
                        cid = convert_hanzi_to_cid_safe(char, self.cmap_table)
                        if cid:
                            match_cids.append([cid])

                    if match_cids:
                        rclt_1_subtables.append(
                            {
                                "match": match_cids,
                                "apply": applies,
                                "inputBegins": min(ats),
                                "inputEnds": max(ats) + 1,
                            }
                        )

    def _make_rclt2_feature(self) -> None:
        """Generate exception patterns -> updates lookup_rclt_2."""
        if not self.exception_pattern:
            return

        lookups = self.gsub_data["lookups"]

        # Create additional lookup tables from exception_pattern
        if "lookup_table" in self.exception_pattern:
            lookup_table = cast(
                Dict[str, Dict[str, str]], self.exception_pattern["lookup_table"]
            )
            for lookup_name, table in lookup_table.items():
                lookups[lookup_name] = {
                    "type": "gsub_single",
                    "flags": {},
                    "subtables": [{}],
                }

                # Add substitutions
                lookup_subtables = cast(
                    Dict[str, str], lookups[lookup_name]["subtables"][0]
                )
                for hanzi, target in table.items():
                    cid = convert_hanzi_to_cid_safe(hanzi, self.cmap_table)
                    if cid and isinstance(target, str):
                        # Replace hanzi with cid in target (exact legacy method)
                        target_cid = target.replace(hanzi, cid)
                        lookup_subtables[cid] = target_cid

                self.lookup_order.add(lookup_name)

        # Generate contextual rules for lookup_rclt_2 (exception pattern)
        if "patterns" in self.exception_pattern:
            rclt_2_subtables = cast(
                List[ChainingRule], lookups["lookup_rclt_2"]["subtables"]
            )
            patterns_dict = self.exception_pattern.get("patterns", {})

            for phrase, setting in patterns_dict.items():
                if not isinstance(setting, dict):
                    continue
                ignore_pattern = setting.get("ignore")
                pattern_list = setting.get("pattern") or []

                # Handle ignore patterns
                if ignore_pattern:
                    ignore_parts = ignore_pattern.split(" ")
                    target_char = None
                    at_pos = -1

                    for i, part in enumerate(ignore_parts):
                        if part.endswith("'"):
                            target_char = part[:-1]
                            at_pos = i
                            break

                    if target_char and at_pos >= 0:
                        ignore_phrase = ignore_pattern.replace(" ", "").replace("'", "")
                        ignore_match_cids: List[List[str]] = []
                        for char in ignore_phrase:
                            cid = convert_hanzi_to_cid_safe(char, self.cmap_table)
                            if cid:
                                ignore_match_cids.append([cid])

                        if ignore_match_cids:
                            rclt_2_subtables.append(
                                {
                                    "match": ignore_match_cids,
                                    "apply": [],
                                    "inputBegins": at_pos,
                                    "inputEnds": at_pos + 1,
                                }
                            )

                # Handle normal patterns
                applies: List[ChainingRuleApply] = []
                ats = []

                for i, table in enumerate(pattern_list):
                    if isinstance(table, dict) and table:
                        lookup_name = list(table.values())[0]
                        if lookup_name:
                            ats.append(i)
                            applies.append({"at": i, "lookup": lookup_name})

                if applies:
                    match_cids: List[List[str]] = []
                    for char in phrase:
                        cid = convert_hanzi_to_cid_safe(char, self.cmap_table)
                        if cid:
                            match_cids.append([cid])

                    if match_cids:
                        rclt_2_subtables.append(
                            {
                                "match": match_cids,
                                "apply": applies,
                                "inputBegins": min(ats),
                                "inputEnds": max(ats) + 1,
                            }
                        )

    def _make_lookup_order(self) -> None:
        """Set final lookup order."""
        # レガシーコードコメント:
        # > e.g.:
        # > "lookupOrder": [
        # >     "lookup_rclt_0",
        # >     "lookup_rclt_1",
        # >     "lookup_ccmp_2",
        # >     "lookup_11_3"
        # > ]
        # Convert set to sorted list (matches legacy order)
        self.logger.debug("lookup_order contents: %s", self.lookup_order)
        self.logger.debug(
            "lookup_order types: %s", [type(x) for x in self.lookup_order]
        )

        # Filter to ensure only strings are included
        string_lookups = [x for x in self.lookup_order if isinstance(x, str)]
        self.logger.debug("string_lookups: %s", string_lookups)

        order_list = list(string_lookups)
        order_list.sort()

        self.logger.debug("All lookups in order: %s", order_list)

        # Always include base lookups
        final_order = ["lookup_aalt_0"]

        # Add lookup_aalt_1 if it exists
        if "lookup_aalt_1" in order_list:
            final_order.append("lookup_aalt_1")

        # Add lookup_11_* in order
        lookup_11_list = [name for name in order_list if name.startswith("lookup_11_")]
        final_order.extend(lookup_11_list)

        # Add rclt lookups
        final_order.extend(["lookup_rclt_0", "lookup_rclt_1", "lookup_rclt_2"])

        self.logger.debug("Final lookup order: %s", final_order)
        self.gsub_data["lookupOrder"] = final_order
