# -*- coding: utf-8 -*-
"""ビルド済みフォントの GSUB 回帰テスト（issue #40）。

aalt の lookup_aalt_1（全多音字の Alternate Substitution）は caryll otfcc
0.10.4 では壊れたバイナリになり GSUB 全体が無効化されていた。otfcc-rs で
ビルドしたフォントの GSUB が fontTools で読めること、AlternateSubst が
多音字の ss00..ss{N} を網羅していることを確認する。

フォントが未ビルド（outputs/*.ttf が無い）の場合は skip する。
環境変数 MENGSHEN_FONT_DIR でフォントのあるディレクトリを差し替えられる。
"""

import os
from pathlib import Path
from typing import Dict, List

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FONT_DIR = Path(os.environ.get("MENGSHEN_FONT_DIR", OUTPUTS_DIR))
FONT_FILES = ["Mengshen-HanSerif.ttf", "Mengshen-Handwritten.ttf"]


def load_multiple_pronunciations() -> Dict[int, List[str]]:
    """merged-mapping-table.txt から {codepoint: [読み...]}（読みが複数のもの）。"""
    table = {}
    with open(OUTPUTS_DIR / "merged-mapping-table.txt", encoding="utf-8") as f:
        for line in f:
            codepoint = int(line.split(":")[0][2:], 16)
            pinyins = line.split(" ")[1].strip().split(",")
            if len(pinyins) > 1:
                table[codepoint] = pinyins
    return table


@pytest.fixture(scope="module", params=FONT_FILES)
def font(request):
    font_tools = pytest.importorskip("fontTools.ttLib")
    path = FONT_DIR / request.param
    if not path.exists():
        pytest.skip(f"{path} is not built")
    return font_tools.TTFont(str(path))


def collect_alternates(font) -> Dict[str, List[str]]:
    gsub = font["GSUB"].table  # parses the whole GSUB table
    alternates: Dict[str, List[str]] = {}
    for lookup in gsub.LookupList.Lookup:
        for subtable in lookup.SubTable:
            if lookup.LookupType == 7:  # Extension
                subtable = subtable.ExtSubTable
            if subtable.LookupType == 3:  # AlternateSubst
                alternates.update(subtable.alternates)
    return alternates


@pytest.mark.integration
def test_gsub_has_aalt_and_rclt(font):
    gsub = font["GSUB"].table
    tags = {record.FeatureTag for record in gsub.FeatureList.FeatureRecord}
    assert {"aalt", "rclt"} <= tags


@pytest.mark.integration
def test_alternate_subst_covers_homographs(font):
    alternates = collect_alternates(font)
    glyph_names = set(font.getGlyphOrder())
    cmap = font.getBestCmap()

    covered = 0
    for codepoint, pinyins in load_multiple_pronunciations().items():
        cid = cmap.get(codepoint)
        if cid is None:
            continue
        expected = [f"{cid}.ss{i:02d}" for i in range(len(pinyins) + 1)]
        if not all(name in glyph_names for name in expected):
            # 読みグリフ自体が無い文字（データ欠損）は aalt からも落ちる
            continue
        assert alternates.get(cid) == expected, cid
        covered += 1

    assert covered > 1000

    hang = cmap[ord("行")]
    assert alternates[hang] == [f"{hang}.ss{i:02d}" for i in range(6)]
