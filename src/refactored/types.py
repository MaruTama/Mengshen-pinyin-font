# -*- coding: utf-8 -*-
"""Type definitions for the Mengshen font project."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict, Union

# More precise font JSON structure types
GlyphValue = Union[str, int, float]
GlyphInstruction = Dict[str, GlyphValue]
GlyphContour = List[GlyphInstruction]
GlyphData = Dict[str, Union[GlyphValue, List[GlyphInstruction], GlyphContour]]


# Font table types with specific structures
class CmapTableData(TypedDict):
    """Character mapping table structure."""

    format: int
    platformID: int
    encodingID: int
    languageID: int
    segCount: int


class GlyfTableData(TypedDict):
    """Glyph table data structure."""

    advanceWidth: int
    leftSideBearing: int
    contours: Optional[List[GlyphContour]]


class HeadTableData(TypedDict):
    """Font head table structure."""

    version: float
    fontRevision: float
    checkSumAdjustment: int
    magicNumber: int
    flags: int
    unitsPerEm: int


class HheaTableData(TypedDict):
    """Horizontal header table structure."""

    version: float
    ascent: int
    descent: int
    lineGap: int


class NameTableData(TypedDict):
    """Name table structure."""

    version: int
    count: int
    stringOffset: int
    nameRecords: List["FontNameEntry"]


# Font table union type with more flexible structure
FontTableValue = Union[
    Dict[str, Any],  # Primary type for complex table structures
    List[Dict[str, Any]],  # For array-based structures
    str,
    int,
    float,  # Simple values
]

# FontData type for the main font JSON structure
FontData = Dict[str, FontTableValue]

# FontTableData type for individual table data
FontTableData = Dict[
    str, Union[str, int, float, List[Dict[str, Union[str, int, float]]]]
]

# Complete font JSON structure with better typing
FontJson = Dict[str, Union[GlyphValue, FontTableValue, Dict[str, Any]]]


# Name table entry
class FontNameEntry(TypedDict):
    """Font name table entry structure."""

    platformID: int
    encodingID: int
    languageID: int
    nameID: int
    nameString: str


# GSUB table structures with better typing
class GSUBLookupSubtable(TypedDict, total=False):
    """GSUB lookup subtable structure."""

    substFormat: int
    coverage: Union[Dict[str, Any], List[str]]
    substituteGlyphIDs: Optional[List[str]]
    chainSubRuleSets: Optional[List[Dict[str, Any]]]


class GSUBLookup(TypedDict):
    """GSUB lookup table structure."""

    lookupType: int
    lookupFlag: int
    markFilteringSet: Optional[int]
    subtables: List[GSUBLookupSubtable]


class GSUBFeature(TypedDict):
    """GSUB feature structure."""

    featureParams: Optional[int]
    lookupListIndices: List[int]


class GSUBScript(TypedDict):
    """GSUB script structure."""

    defaultLangSys: Optional[Dict[str, Any]]
    langSysRecords: Dict[str, Dict[str, Any]]


class GSUBTable(TypedDict):
    """Complete GSUB table structure."""

    version: float
    scriptList: Dict[str, GSUBScript]
    featureList: Dict[str, GSUBFeature]
    lookupList: List[GSUBLookup]


# Character mappings
CmapTable = Dict[str, str]  # Unicode -> CID mapping
PinyinMappings = Dict[str, List[str]]  # Character -> Pinyin list

# Configuration types
FontPaths = Dict[str, str]
CanvasSize = Dict[str, int]
TrackingConfig = Dict[str, Union[int, float]]

# Glyph processing types
GlyphMetrics = Dict[str, Union[int, float]]
BoundingBox = List[int]  # [xMin, yMin, xMax, yMax]

# Statistics return types
StatsDict = Dict[str, Union[str, int, float, Dict[str, int]]]

# Font table access types
HheaTable = Dict[str, Union[str, int, float]]
HeadTable = Dict[str, Union[str, int, float]]
OS2Table = Dict[str, Union[str, int, float]]
NameTable = Union[Dict[str, Any], List[Dict[str, Any]]]


# Character data types
class CharacterInfo(TypedDict):
    """Character information structure."""

    character: str
    pronunciations: List[str]


# Font generation types
FontStyle = Union[str, int]  # 'han_serif' | 'handwritten' or enum values
ProcessingResult = Dict[str, Any]
