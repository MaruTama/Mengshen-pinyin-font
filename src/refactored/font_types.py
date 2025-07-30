# -*- coding: utf-8 -*-
"""Font-specific type definitions for the Mengshen font project."""

from __future__ import annotations

from typing import Dict, List, Optional, TypedDict, Union

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


class HeadTableData(TypedDict, total=False):
    """Font head table structure."""

    version: float
    fontRevision: float
    checkSumAdjustment: int
    magicNumber: int
    flags: int
    unitsPerEm: int
    yMax: Union[int, float]


class HheaTableData(TypedDict, total=False):
    """Horizontal header table structure."""

    version: float
    ascent: int
    descent: int
    lineGap: int
    ascender: Union[int, float]


class NameTableData(TypedDict):
    """Name table structure."""

    version: int
    count: int
    stringOffset: int
    nameRecords: List["FontNameEntry"]


# Character mappings (defined early for FontTableValue)
CmapTable = Dict[str, str]  # Unicode -> CID mapping
PinyinMappings = Dict[str, List[str]]  # Character -> Pinyin list

# Font table union type with specific structures
FontTableValue = Union[
    "GlyfTable",  # For glyf table structures
    "HeadTable",  # For head table structures
    "HheaTable",  # For hhea table structures
    "NameTable",  # For name table structures
    List[str],  # For glyph_order and similar string lists
    CmapTable,  # For cmap table structures
    "OTFCCGSUBTable",  # For GSUB table structures
    Dict[str, Union[str, int, float]],  # For simple table structures
    str,
    int,
    float,  # Simple values
]

# Fallback for truly complex structures
ComplexFontTable = Dict[str, Union[str, int, float, List[Union[str, int, float]]]]

# Glyf table structure
GlyfTable = Dict[str, "GlyphData"]

# FontData type for the main font JSON structure
FontData = Dict[str, FontTableValue]

# FontTableData type for individual table data
FontTableData = Dict[
    str, Union[str, int, float, List[Dict[str, Union[str, int, float]]]]
]

# Complete font JSON structure with better typing
FontJson = Dict[str, Union[GlyphValue, FontTableValue, ComplexFontTable]]


# Name table entry
class FontNameEntry(TypedDict):
    """Font name table entry structure."""

    platformID: int
    encodingID: int
    languageID: int
    nameID: int
    nameString: str


# Pattern data structures for GSUB generation
class PatternOneEntry(TypedDict):
    """Single pattern entry for pattern one data."""

    variational_pronunciation: str
    patterns: str


PatternOneData = List[Dict[str, PatternOneEntry]]


class PatternTwoLookupTable(TypedDict, total=False):
    """Lookup table structure for pattern two."""

    lookup_table: Optional[Dict[str, Dict[str, str]]]
    patterns: Optional[Dict[str, List[Dict[str, str]]]]


PatternTwoData = Dict[str, Union[Dict[str, str], List[Dict[str, str]]]]


class ExceptionPatternEntry(TypedDict, total=False):
    """Exception pattern entry structure."""

    ignore: Optional[str]
    pattern: Optional[List[Dict[str, str]]]


ExceptionPatternData = Dict[str, Dict[str, ExceptionPatternEntry]]


# GSUB table structures with better typing
CoverageTable = Union[Dict[str, Union[str, int, List[str]]], List[str]]
ChainSubRuleSet = Dict[str, Union[str, int, List[Union[str, int]]]]


class GSUBLookupSubtable(TypedDict, total=False):
    """GSUB lookup subtable structure."""

    substFormat: int
    coverage: CoverageTable
    substituteGlyphIDs: Optional[List[str]]
    chainSubRuleSets: Optional[List[ChainSubRuleSet]]


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


# Language system structure
LangSysRecord = Dict[str, Union[str, int, List[int]]]


class GSUBScript(TypedDict):
    """GSUB script structure."""

    defaultLangSys: Optional[LangSysRecord]
    langSysRecords: Dict[str, LangSysRecord]


# Custom types for OTFCC GSUB structure
class ChainingRuleApply(TypedDict):
    """A rule for applying a lookup in a chaining contextual substitution."""

    at: int
    lookup: str


class ChainingRule(TypedDict):
    """A chaining contextual substitution rule."""

    match: List[List[str]]
    apply: List[ChainingRuleApply]
    inputBegins: int
    inputEnds: int


# GSUB lookup flags structure
GSUBLookupFlags = Dict[str, Union[str, int, bool]]


class GsubSingleLookup(TypedDict):
    """A 'gsub_single' lookup table."""

    type: str  # Should be 'gsub_single'
    flags: GSUBLookupFlags
    subtables: List[Dict[str, str]]


class GsubAlternateLookup(TypedDict):
    """A 'gsub_alternate' lookup table."""

    type: str  # Should be 'gsub_alternate'
    flags: GSUBLookupFlags
    subtables: List[Dict[str, List[str]]]


class GsubChainingLookup(TypedDict):
    """A 'gsub_chaining' lookup table."""

    type: str  # Should be 'gsub_chaining'
    flags: GSUBLookupFlags
    subtables: List[ChainingRule]


OTFCCGSUBLookup = Union[GsubSingleLookup, GsubAlternateLookup, GsubChainingLookup]


# OTFCC-style GSUB table structure (matches our implementation)
class OTFCCGSUBTable(TypedDict):
    """OTFCC-style GSUB table structure used in font generation."""

    languages: Dict[str, Dict[str, List[str]]]  # Script-language mappings
    features: Dict[str, List[str]]  # Feature-lookup mappings
    lookups: Dict[str, OTFCCGSUBLookup]  # Use the union type for more specific lookups
    lookupOrder: List[str]  # Lookup execution order


# Standard OpenType GSUB table structure (for reference)
class StandardGSUBTable(TypedDict):
    """Standard OpenType GSUB table structure."""

    version: float
    scriptList: Dict[str, GSUBScript]
    featureList: Dict[str, GSUBFeature]
    lookupList: List[GSUBLookup]


# Alias for current implementation
GSUBTable = OTFCCGSUBTable


# (CmapTable and PinyinMappings moved to earlier in file)

# Configuration types
FontPaths = Dict[str, str]
CanvasSize = Dict[str, int]
TrackingConfig = Dict[str, Union[int, float]]

# Glyph processing types
GlyphMetrics = Dict[str, Union[int, float]]
BoundingBox = List[int]  # [xMin, yMin, xMax, yMax]


# Statistics structures
class UnicodeRangeStats(TypedDict):
    """Unicode range statistics structure."""

    start: int
    end: int
    count: int


class GlyphGenerationStats(TypedDict, total=False):
    """Glyph generation statistics structure."""

    total_glyphs: int
    pinyin_alphabets: Optional[int]
    substance_glyphs: Optional[int]
    template_glyphs: Optional[int]
    unicode_range: Optional[UnicodeRangeStats]
    uvs_mappings: Optional[int]


# Statistics return types (flexible for various uses)
StatsDict = Dict[str, Union[str, int, float, Dict[str, int]]]

# Font table access types
HheaTable = Dict[str, Union[str, int, float]]
HeadTable = Dict[str, Union[str, int, float]]
OS2Table = Dict[str, Union[str, int, float]]
NameTable = Union[Dict[str, Union[str, int, List[FontNameEntry]]], List[FontNameEntry]]


# Character data types
class CharacterInfo(TypedDict):
    """Character information structure."""

    character: str
    pronunciations: List[str]


# Font generation types
FontStyle = Union[str, int]  # 'han_serif' | 'handwritten' or enum values
ProcessingResult = Dict[str, Union[str, int, float, bool, List[str]]]
