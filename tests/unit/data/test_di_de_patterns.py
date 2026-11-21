# -*- coding: utf-8 -*-
"""地 の構造助詞 de（状語マーカー）の文脈パターンのテスト（issue #18）。

地 の既定の読みは dì。副詞的修飾語 + 地（慢慢地・认真地 など）の文脈だけ
de に置換し、名詞用法（土地・草地・当地・地铁 など）は dì のまま残す。

GSUB の lookup_rclt_0（pattern one）/ lookup_rclt_1（pattern two）が
生成済みテーブル（outputs/）から作られるのと同じ規則で、文字列上の
地 が de パターンに一致するかをシミュレートして検証する。
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DI = "地"
DE = "de"


def load_mapping_table() -> Dict[str, List[str]]:
    table = {}
    with open(OUTPUTS_DIR / "merged-mapping-table.txt", encoding="utf-8") as f:
        for line in f:
            hanzi = chr(int(line.split(":")[0][2:], 16))
            table[hanzi] = line.split(" ")[1].strip().split(",")
    return table


def load_pattern_one() -> Dict[Tuple[str, str], Tuple[int, List[str]]]:
    """{(漢字, 読み): (order, [パターン...])}"""
    table = {}
    with open(OUTPUTS_DIR / "duoyinzi_pattern_one.txt", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            order, hanzi, pinyin, patterns = line.split(", ", 3)
            table[(hanzi, pinyin)] = (int(order), patterns.strip("[]").split("|"))
    return table


def load_pattern_two() -> dict:
    return json.loads(
        (OUTPUTS_DIR / "duoyinzi_pattern_two.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def mapping_table():
    return load_mapping_table()


@pytest.fixture(scope="module")
def de_rules(mapping_table):
    """地 を de グリフに置換する文脈（地 を含むフレーズ, 地 の位置）の一覧。"""
    de_ss = mapping_table[DI].index(DE) + 1
    rules: List[Tuple[str, int]] = []

    # pattern one: 2, 地, de, [慢慢~|...]
    entry = load_pattern_one().get((DI, DE))
    if entry is not None:
        order, patterns = entry
        assert order == de_ss
        for pattern in patterns:
            rules.append((pattern.replace("~", DI), pattern.index("~")))

    # pattern two: {"悄悄地": [{"悄": lookup}, {"悄": lookup}, {"地": lookup}]}
    data = load_pattern_two()
    de_lookups = {
        name
        for name, subs in data["lookup_table"].items()
        if subs.get(DI) == f"{DI}.ss{de_ss:02d}"
    }
    for phrase, cells in data["patterns"].items():
        for i, cell in enumerate(cells):
            if cell.get(DI) in de_lookups:
                rules.append((phrase, i))
    return rules


def di_reads_de(sentence: str, rules: List[Tuple[str, int]]) -> List[bool]:
    """文中の各 地 が de パターンに一致するか（出現順）。"""
    results = []
    for pos, char in enumerate(sentence):
        if char != DI:
            continue
        hit = False
        for phrase, at in rules:
            start = pos - at
            if start >= 0 and sentence[start : start + len(phrase)] == phrase:
                hit = True
                break
        results.append(hit)
    return results


class TestDiDefaultReading:
    def test_default_reading_is_di_and_de_exists(self, mapping_table):
        assert mapping_table[DI][0] == "dì"
        assert DE in mapping_table[DI]


# 構造助詞（状語マーカー）の 地 → de
DE_SENTENCES = [
    "他慢慢地走了",
    "天渐渐地黑了",
    "她悄悄地离开了",
    "湖水静静地流着",
    "他轻轻地关上门",
    "他默默地点头",
    "你要好好地学习",
    "他偷偷地看了一眼",
    "她紧紧地抱着孩子",
    "我深深地吸了一口气",
    "他狠狠地踢了一脚",
    "我远远地看见他",
    "他稳稳地站着",
    "请牢牢地记住",
    "他久久地望着",
    "船缓缓地开动了",
    "他匆匆地走了",
    "我暗暗地下决心",
    "他早早地起床了",
    "这大大地提高了效率",
    "他高高地举起手",
    "他认真地学习",
    "请仔细地检查",
    "他努力地工作",
    "老师耐心地讲解",
    "雨不停地下着",
    "他飞快地跑过去",
    "火迅速地蔓延",
    "他们热情地欢迎客人",
    "他拼命地跑",
    "她激动地哭了",
    "天气逐渐地变冷",
]

# 名詞用法などの 地 → dì のまま
DI_SENTENCES = [
    "这块土地很大",
    "他在草地上",
    "我是本地人",
    "天地之间",
    "大地回春",
    "当地人很热情",
    "场地不够大",
    "陆地上的动物",
    "这个地方很好",
    "我坐地铁上班",
    "他回家种地",
    "他在扫地",
    "背地里说坏话",
    "小心地滑",
    "很快地铁就通了",
    "特别地区",
    "这里不断地震",
    "地壳运动",
]


class TestDiDeContextualPatterns:
    @pytest.mark.parametrize("sentence", DE_SENTENCES)
    def test_particle_di_reads_de(self, sentence, de_rules):
        assert di_reads_de(sentence, de_rules) == [True]

    @pytest.mark.parametrize("sentence", DI_SENTENCES)
    def test_noun_di_keeps_di(self, sentence, de_rules):
        assert di_reads_de(sentence, de_rules) == [False]

    def test_di_anchor_keeps_pattern_one_entry(self):
        """地 に dì のパターンが無いと compress_pattern_one_table が
        de パターンを標準読みとして他の漢字へ移してしまうため、dì 側の
        アンカー（土地）が残っていること。"""
        table = load_pattern_one()
        assert (DI, "dì") in table
        assert "土~" in table[(DI, "dì")][1]
