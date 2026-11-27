# -*- coding: utf-8 -*-
"""duoyinzi pattern テーブルと merged-mapping-table.txt の読み順整合性テスト。

規約: ssNN = merged-mapping-table.txt の読みリストの readings[NN-1]
（glyph_manager.py と同じ。ss01 = 標準読み = readings[0]）

- duoyinzi_pattern_one.txt の order 列は「読みの index + 1」でなければならない
- duoyinzi_exceptional_pattern.json の ss 番号も現行読み順に一致しなければならない
"""

import importlib
import json
import os
import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "res" / "phonics" / "duo_yin_zi" / "scripts"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def load_mapping_table():
    """outputs/merged-mapping-table.txt を {漢字: [読み,...]} で読み込む。"""
    table = {}
    with open(OUTPUTS_DIR / "merged-mapping-table.txt", encoding="utf-8") as f:
        for line in f:
            str_unicode = line.split(":")[0]
            hanzi = chr(int(str_unicode[2:], 16))
            pinyins = line.split(" ")[1].split(",")
            table[hanzi] = pinyins
    return table


@pytest.fixture(scope="module")
def mapping_table():
    return load_mapping_table()


@pytest.fixture(scope="module")
def make_pattern_table_module():
    """スクリプトを import する（相対パス依存のため cwd を切り替える）。"""
    old_cwd = os.getcwd()
    os.chdir(SCRIPTS_DIR)
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        module = importlib.import_module("make_pattern_table")
        yield module
    finally:
        sys.path.remove(str(SCRIPTS_DIR))
        os.chdir(old_cwd)


class TestExportPatternOneTable:
    """export_pattern_one_table の order 番号付けの単体テスト。"""

    def test_order_uses_true_reading_index(
        self, make_pattern_table_module, monkeypatch, tmp_path
    ):
        """パターンの無い読みを飛ばしても order は読みの index + 1 になる。

        例: 着 = [zháo, zhù, zhāo, zhuó, zhe, zhuo] で zhù にパターンが
        無い場合、zhāo は 2 ではなく 3（= index 2 + 1）でなければならない。
        """
        mpt = make_pattern_table_module
        fake_mapping = {"着": ["zháo", "zhù", "zhāo", "zhuó", "zhe", "zhuo"]}
        monkeypatch.setattr(mpt, "PINYIN_MAPPING_TABLE", fake_mapping)

        pattern_table = {
            "着": {
                "pinyin": fake_mapping["着"],
                "patterns": {
                    "zháo": ["~急"],
                    "zhāo": ["没~了"],
                    "zhuó": ["~陆"],
                    "zhe": ["穿~"],
                },
            }
        }
        out_file = tmp_path / "pattern_one.txt"
        mpt.export_pattern_one_table(pattern_table, str(out_file))

        lines = out_file.read_text(encoding="utf-8").splitlines()
        orders = {}
        for line in lines:
            order, hanzi, pinyin, _ = line.split(", ", 3)
            orders[pinyin] = int(order)

        assert orders == {"zháo": 1, "zhāo": 3, "zhuó": 4, "zhe": 5}


class TestCompressPatternOneTable:
    """compress_pattern_one_table: 読みが 1 種類だけの漢字の扱い。"""

    FAKE_MAPPING = {
        "个": ["ge", "gè", "gě"],
        "别": ["bié", "biè"],
        "累": ["lèi", "léi"],
    }

    def _table(self):
        return {
            "个": {
                "pinyin": self.FAKE_MAPPING["个"],
                "patterns": {"gè": ["~别"]},
            },
            "别": {
                "pinyin": self.FAKE_MAPPING["别"],
                "patterns": {"bié": ["个~"], "biè": ["~扭"]},
            },
        }

    def test_nonstandard_only_pattern_is_kept(
        self, make_pattern_table_module, monkeypatch
    ):
        """標準でない読み（个 の gè）だけのパターンは表に残す。

        消すと 个别 が標準の読み ge で描かれ、規則が失われる。
        """
        mpt = make_pattern_table_module
        monkeypatch.setattr(mpt, "PINYIN_MAPPING_TABLE", self.FAKE_MAPPING)

        result = mpt.compress_pattern_one_table(self._table())

        assert result["个"]["patterns"] == {"gè": ["~别"]}

    def test_partner_standard_pattern_does_not_absorb_it(
        self, make_pattern_table_module, monkeypatch
    ):
        """残した語句を、相手（别）の標準の読みのパターンへ移さない。"""
        mpt = make_pattern_table_module
        monkeypatch.setattr(mpt, "PINYIN_MAPPING_TABLE", self.FAKE_MAPPING)
        table = self._table()
        table["别"]["patterns"] = {"bié": ["~扭"], "biè": ["~字"]}

        result = mpt.compress_pattern_one_table(table)

        assert result["别"]["patterns"]["bié"] == ["~扭"]

    def test_standard_only_pattern_is_moved_to_partner(
        self, make_pattern_table_module, monkeypatch
    ):
        """標準の読みだけのパターンは従来どおり相手へ移して表から外す。"""
        mpt = make_pattern_table_module
        monkeypatch.setattr(mpt, "PINYIN_MAPPING_TABLE", self.FAKE_MAPPING)
        table = {
            "累": {
                "pinyin": self.FAKE_MAPPING["累"],
                "patterns": {"lèi": ["~别"]},
            },
            "别": {
                "pinyin": self.FAKE_MAPPING["别"],
                "patterns": {"bié": ["~扭"], "biè": ["~字"]},
            },
        }

        result = mpt.compress_pattern_one_table(table)

        assert "累" not in result
        assert "累~" in result["别"]["patterns"]["bié"]


class TestExceptionalPattern:
    """make_exceptional_pattern の ss 番号の単体テスト。"""

    def test_ss_numbers_match_current_mapping_table(
        self, make_pattern_table_module, mapping_table, tmp_path
    ):
        """着手の 着 は zhuó、轴子の 轴 は zhòu を指す ss 番号であること。"""
        mpt = make_pattern_table_module
        out_file = tmp_path / "exceptional.json"
        mpt.make_exceptional_pattern(str(out_file))
        data = json.loads(out_file.read_text(encoding="utf-8"))

        lookup = data["lookup_table"]["lookup_pattern_20"]
        expected_zhuo_ss = mapping_table["着"].index("zhuó") + 1
        expected_zhou_ss = mapping_table["轴"].index("zhòu") + 1
        assert lookup["着"] == f"着.ss{expected_zhuo_ss:02d}"
        assert lookup["轴"] == f"轴.ss{expected_zhou_ss:02d}"


class TestGeneratedOutputConsistency:
    """outputs/ の生成済みファイルが現行 mapping table と整合しているか。"""

    def test_pattern_one_orders_match_mapping_table(self, mapping_table):
        """duoyinzi_pattern_one.txt の全行: order == 読みの index + 1。"""
        mismatches = []
        path = OUTPUTS_DIR / "duoyinzi_pattern_one.txt"
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                order, hanzi, pinyin, _ = line.split(", ", 3)
                expected = mapping_table[hanzi].index(pinyin) + 1
                if int(order) != expected:
                    mismatches.append(
                        f"{hanzi} {pinyin}: order={order}, expected={expected}"
                    )
        assert mismatches == []

    def test_pattern_two_ss_numbers_within_reading_range(self, mapping_table):
        """duoyinzi_pattern_two.json の ssNN が読み数の範囲内であること。"""
        path = OUTPUTS_DIR / "duoyinzi_pattern_two.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for lookup_name, subs in data["lookup_table"].items():
            for hanzi, glyph in subs.items():
                m = re.fullmatch(re.escape(hanzi) + r"\.ss(\d{2})", glyph)
                assert m, f"{lookup_name}: 不正なグリフ名 {glyph}"
                ss = int(m.group(1))
                assert 2 <= ss <= len(mapping_table[hanzi]), (
                    f"{lookup_name}: {hanzi} の ss{ss:02d} が"
                    f" 読み数 {len(mapping_table[hanzi])} を超過"
                )

    def test_exceptional_pattern_ss_numbers_match_mapping_table(self, mapping_table):
        """duoyinzi_exceptional_pattern.json: 着手→zhuó, 轴子→zhòu。"""
        path = OUTPUTS_DIR / "duoyinzi_exceptional_pattern.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        lookup = data["lookup_table"]["lookup_pattern_20"]
        expected_zhuo_ss = mapping_table["着"].index("zhuó") + 1
        expected_zhou_ss = mapping_table["轴"].index("zhòu") + 1
        assert lookup["着"] == f"着.ss{expected_zhuo_ss:02d}"
        assert lookup["轴"] == f"轴.ss{expected_zhou_ss:02d}"
