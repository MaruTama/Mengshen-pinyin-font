# -*- coding: utf-8 -*-
"""GSUB table generation with exact legacy compatibility."""

from __future__ import annotations

import orjson
import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Set

from ..config import FontConstants
from ..data import CharacterDataManager, MappingDataManager

# Add src directory to path for legacy utility import
_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Also try current working directory
import os
_cwd_src = os.path.join(os.getcwd(), 'src')
if _cwd_src not in sys.path:
    sys.path.insert(0, _cwd_src)

try:
    import utility as _legacy_utility
    print(f"DEBUG: Legacy utility imported successfully from {_legacy_utility.__file__}")
except ImportError as e:
    print(f"DEBUG: Failed to import legacy utility: {e}")
    print(f"DEBUG: Current working directory: {os.getcwd()}")
    print(f"DEBUG: Python path: {sys.path[:3]}")
    _legacy_utility = None


class GSUBTableGenerator:
    """Generates GSUB table matching legacy structure exactly."""
    
    def __init__(
        self,
        pattern_one_path: Path,
        pattern_two_path: Path,
        exception_pattern_path: Path,
        character_manager: CharacterDataManager,
        mapping_manager: MappingDataManager
    ):
        """Initialize with pattern files and data managers."""
        self.pattern_one_path = pattern_one_path
        self.pattern_two_path = pattern_two_path
        self.exception_pattern_path = exception_pattern_path
        self.character_manager = character_manager
        self.mapping_manager = mapping_manager
        
        # Track dynamically created lookups
        self.lookup_order = set()
        
        # Pattern data 
        self.pattern_one = [{}]
        self.pattern_two = {}
        self.exception_pattern = {}
        
        # Initialize base GSUB structure (matches legacy exactly)
        self.gsub_data = {
            "languages": {
                "DFLT_DFLT": {
                    "features": ["aalt_00000", "rclt_00002"]
                },
                "hani_DFLT": {
                    "features": ["aalt_00001", "rclt_00003"]
                }
            },
            "features": {
                "aalt_00000": ["lookup_aalt_0", "lookup_aalt_1"],
                "aalt_00001": ["lookup_aalt_0", "lookup_aalt_1"],
                "rclt_00002": ["lookup_rclt_2", "lookup_rclt_3", "lookup_rclt_4"],
                "rclt_00003": ["lookup_rclt_2", "lookup_rclt_3", "lookup_rclt_4"]
            },
            "lookups": {
                "lookup_aalt_0": {
                    "type": "gsub_single", 
                    "flags": {},
                    "subtables": [{}]
                },
                "lookup_aalt_1": {
                    "type": "gsub_alternate",
                    "flags": {},
                    "subtables": [{}]
                },
                "lookup_rclt_2": {
                    "type": "gsub_chaining",
                    "flags": {},
                    "subtables": []
                },
                "lookup_rclt_3": {
                    "type": "gsub_chaining", 
                    "flags": {},
                    "subtables": []
                },
                "lookup_rclt_4": {
                    "type": "gsub_chaining",
                    "flags": {},
                    "subtables": []
                }
            },
            "lookupOrder": ["lookup_aalt_0"]
        }
    
    def generate_gsub_table(self) -> Dict[str, Any]:
        """Generate complete GSUB table with legacy structure."""
        # Load pattern files
        self._load_pattern_data()
        
        # Generate features in legacy order
        self._make_aalt_feature()
        self._make_rclt0_feature()  # Pattern one -> creates lookup_11_*
        self._make_rclt1_feature()  # Pattern two -> updates lookup_rclt_3
        self._make_rclt2_feature()  # Exception pattern -> updates lookup_rclt_4
        
        # Set final lookup order (matches legacy)
        self._make_lookup_order()
        
        return self.gsub_data
    
    def _load_pattern_data(self) -> None:
        """Load pattern files."""
        # Pattern one (single character patterns)
        self.pattern_one = [{}]
        if self.pattern_one_path.exists():
            with open(self.pattern_one_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.rstrip('\n').split(', ')
                    if len(parts) >= 4:
                        str_order, hanzi, pinyin, patterns = parts
                        order = int(str_order)
                        
                        # Skip order 1 (standard pronunciation)
                        if order == 1:
                            continue
                        
                        # Order 2+ -> index 0+
                        idx = order - 2
                        while len(self.pattern_one) <= idx:
                            self.pattern_one.append({})
                        
                        self.pattern_one[idx][hanzi] = {
                            "variational_pronunciation": pinyin,
                            "patterns": patterns
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
        """Generate aalt feature (exact legacy compatibility)."""
        if not _legacy_utility:
            raise RuntimeError("Legacy utility module not available")
        
        utility = _legacy_utility
        
        aalt_0_subtables = self.gsub_data["lookups"]["lookup_aalt_0"]["subtables"][0]
        aalt_1_subtables = self.gsub_data["lookups"]["lookup_aalt_1"]["subtables"][0]
        
        # Single pronunciation characters -> lookup_aalt_0 (legacy method)
        for hanzi, _ in utility.get_has_single_pinyin_hanzi():
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            aalt_0_subtables[cid] = f"{cid}.ss00"
        
        self.lookup_order.add("lookup_aalt_0")
        
        # Multiple pronunciation characters -> lookup_aalt_1 (legacy method)
        for hanzi, pinyins in utility.get_has_multiple_pinyin_hanzi():
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            alternate_list = []
            # ss00 はピンインのないグリフなので、ピンインのグリフは ss01 から ss{len(pinyins)}まで
            for i in range(len(pinyins) + 1):
                alternate_list.append(f"{cid}.ss{i:02d}")
            
            aalt_1_subtables[cid] = alternate_list
        
        print(f"DEBUG: aalt_1 subtables populated with {len(aalt_1_subtables)} entries")
        
        self.lookup_order.add("lookup_aalt_1")
    
    def _make_rclt0_feature(self) -> None:
        """Generate pattern one -> creates lookup_11_* tables (legacy structure)."""
        if not _legacy_utility:
            raise RuntimeError("Legacy utility module not available")
        
        utility = _legacy_utility
        
        max_num_patterns = len(self.pattern_one)
        
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
                "subtables": [{}]
            }
            self.lookup_order.add(lookup_name)
        
        # Generate substitution rules for lookup_rclt_2
        rclt_2_subtables = lookups["lookup_rclt_2"]["subtables"]
        
        for idx in range(max_num_patterns):
            lookup_name = f"lookup_11_{idx + 2}"
            lookup_subtables = lookups[lookup_name]["subtables"][0]
            
            for hanzi, pattern_info in self.pattern_one[idx].items():
                if not self.mapping_manager.has_glyph_for_character(hanzi):
                    continue
                
                cid = utility.convert_str_hanzi_2_cid(hanzi)
                
                # Add to pattern lookup: cid -> cid.ss{XX} (legacy method)
                ss_index = FontConstants.SS_VARIATIONAL_PRONUNCIATION + idx
                lookup_subtables[cid] = f"{cid}.ss{ss_index:02d}"
                
                # Process context patterns for rclt_2
                patterns_str = pattern_info["patterns"]
                patterns = patterns_str.strip("[]").split('|')
                
                # Split patterns by type (same logic as legacy)
                left_match = [p for p in patterns if re.match("^~.$", p)]
                right_match = [p for p in patterns if re.match("^.~$", p)]
                other_match = [p for p in patterns if p not in (left_match + right_match)]
                
                # Left context patterns: [context] target'
                if left_match:
                    context_chars = [p.replace("~", "") for p in left_match]
                    context_cids = [utility.convert_str_hanzi_2_cid(char) for char in context_chars]
                    
                    if context_cids:
                        rclt_2_subtables.append({
                            "match": [[cid], context_cids],
                            "apply": [{
                                "at": 0,
                                "lookup": lookup_name
                            }],
                            "inputBegins": 0,
                            "inputEnds": 1
                        })
                
                # Right context patterns: target' [context]
                if right_match:
                    context_chars = [p.replace("~", "") for p in right_match]
                    context_cids = [utility.convert_str_hanzi_2_cid(char) for char in context_chars]
                    
                    if context_cids:
                        rclt_2_subtables.append({
                            "match": [context_cids, [cid]],
                            "apply": [{
                                "at": 1,
                                "lookup": lookup_name
                            }],
                            "inputBegins": 1,
                            "inputEnds": 2
                        })
                
                # Multi-character context patterns
                for pattern in other_match:
                    at_pos = pattern.index("~")
                    chars = list(pattern.replace("~", hanzi))
                    match_cids = [[utility.convert_str_hanzi_2_cid(char)] for char in chars]
                    
                    if match_cids:
                        rclt_2_subtables.append({
                            "match": match_cids,
                            "apply": [{
                                "at": at_pos,
                                "lookup": lookup_name
                            }],
                            "inputBegins": at_pos,
                            "inputEnds": at_pos + 1
                        })
    
    def _make_rclt1_feature(self) -> None:
        """Generate pattern two -> updates lookup_rclt_3 (legacy compatibility)."""
        if not self.pattern_two:
            return
        
        if not _legacy_utility:
            raise RuntimeError("Legacy utility module not available")
        
        utility = _legacy_utility
        
        lookups = self.gsub_data["lookups"]
        
        # Create additional lookup tables from pattern_two (legacy method)
        if "lookup_table" in self.pattern_two:
            for lookup_name, table in self.pattern_two["lookup_table"].items():
                lookups[lookup_name] = {
                    "type": "gsub_single",
                    "flags": {},
                    "subtables": [{}]
                }
                
                # Add substitutions using legacy logic
                lookup_subtables = lookups[lookup_name]["subtables"][0]
                for hanzi, target in table.items():
                    cid = utility.convert_str_hanzi_2_cid(hanzi)
                    # Replace hanzi with cid in target (exact legacy method)
                    target_cid = target.replace(hanzi, cid)
                    lookup_subtables[cid] = target_cid
                
                self.lookup_order.add(lookup_name)
        
        # Generate contextual rules for lookup_rclt_3 (legacy: lookup_rclt_1)
        if "patterns" in self.pattern_two:
            rclt_3_subtables = lookups["lookup_rclt_3"]["subtables"]
            
            for phrase, pattern_list in self.pattern_two["patterns"].items():
                applies = []
                ats = []
                
                for i, table in enumerate(pattern_list):
                    # Legacy: lookup_name = list(table.values())[0]
                    lookup_name = list(table.values())[0]
                    if lookup_name:
                        ats.append(i)
                        applies.append({
                            "at": i,
                            "lookup": lookup_name
                        })
                
                if applies:
                    match_cids = [[utility.convert_str_hanzi_2_cid(char)] for char in phrase]
                    
                    if match_cids:
                        rclt_3_subtables.append({
                            "match": match_cids,
                            "apply": applies,
                            "inputBegins": min(ats),
                            "inputEnds": max(ats) + 1
                        })
    
    def _make_rclt2_feature(self) -> None:
        """Generate exception patterns -> updates lookup_rclt_4."""
        if not self.exception_pattern:
            return
        
        if not _legacy_utility:
            raise RuntimeError("Legacy utility module not available")
        
        utility = _legacy_utility
        
        lookups = self.gsub_data["lookups"]
        
        # Create additional lookup tables from exception_pattern
        if "lookup_table" in self.exception_pattern:
            for lookup_name, table in self.exception_pattern["lookup_table"].items():
                lookups[lookup_name] = {
                    "type": "gsub_single",
                    "flags": {},
                    "subtables": [{}]
                }
                
                # Add substitutions
                lookup_subtables = lookups[lookup_name]["subtables"][0]
                for hanzi, target in table.items():
                    cid = utility.convert_str_hanzi_2_cid(hanzi)
                    # Replace hanzi with cid in target (exact legacy method)
                    target_cid = target.replace(hanzi, cid)
                    lookup_subtables[cid] = target_cid
                
                self.lookup_order.add(lookup_name)
        
        # Generate contextual rules for lookup_rclt_4
        if "patterns" in self.exception_pattern:
            rclt_4_subtables = lookups["lookup_rclt_4"]["subtables"]
            
            for phrase, setting in self.exception_pattern["patterns"].items():
                ignore_pattern = setting.get("ignore")
                pattern_list = setting.get("pattern", [])
                
                # Handle ignore patterns
                if ignore_pattern:
                    ignore_parts = ignore_pattern.split(' ')
                    target_char = None
                    at_pos = -1
                    
                    for i, part in enumerate(ignore_parts):
                        if part.endswith("'"):
                            target_char = part[:-1]
                            at_pos = i
                            break
                    
                    if target_char and at_pos >= 0:
                        ignore_phrase = ignore_pattern.replace(" ", "").replace("'", "")
                        match_cids = [[utility.convert_str_hanzi_2_cid(char)] for char in ignore_phrase]
                        
                        if match_cids:
                            rclt_4_subtables.append({
                                "match": match_cids,
                                "apply": [],
                                "inputBegins": at_pos,
                                "inputEnds": at_pos + 1
                            })
                
                # Handle normal patterns
                applies = []
                ats = []
                
                for i, table in enumerate(pattern_list):
                    lookup_name = list(table.values())[0]
                    if lookup_name:
                        ats.append(i)
                        applies.append({
                            "at": i,
                            "lookup": lookup_name
                        })
                
                if applies:
                    match_cids = [[utility.convert_str_hanzi_2_cid(char)] for char in phrase]
                    
                    if match_cids:
                        rclt_4_subtables.append({
                            "match": match_cids,
                            "apply": applies,
                            "inputBegins": min(ats),
                            "inputEnds": max(ats) + 1
                        })
    
    def _make_lookup_order(self) -> None:
        """Set final lookup order matching legacy structure."""
        # Convert set to sorted list (matches legacy order)
        order_list = list(self.lookup_order)
        order_list.sort()
        
        print(f"DEBUG: All lookups in order: {order_list}")
        
        # Always include base lookups
        final_order = ["lookup_aalt_0"]
        
        # Add lookup_aalt_1 if it exists
        if "lookup_aalt_1" in order_list:
            final_order.append("lookup_aalt_1")
        
        # Add lookup_11_* in order
        lookup_11_list = [name for name in order_list if name.startswith("lookup_11_")]
        final_order.extend(lookup_11_list)
        
        # Add rclt lookups
        final_order.extend(["lookup_rclt_2", "lookup_rclt_3", "lookup_rclt_4"])
        
        print(f"DEBUG: Final lookup order: {final_order}")
        self.gsub_data["lookupOrder"] = final_order