from pathlib import Path

from fontmaker import write_dictionary, write_phrases
from yomilint.readers import Phrase, read_dictionary, read_phrases


def test_dictionary_lists_readings_with_the_default_first(tmp_path: Path):
    path = write_dictionary(tmp_path / "d.txt", {"着": ["zhe", "zhuó"], "一": ["yī"]})
    assert read_dictionary(path, "mengshen") == {"着": ["zhe", "zhuó"], "一": ["yī"]}


def test_dictionary_skips_blank_lines_and_comments(tmp_path: Path):
    path = tmp_path / "d.txt"
    path.write_text("# a comment\n\nU+4E00: yī  #一\n", encoding="utf-8")
    assert read_dictionary(path, "mengshen") == {"一": ["yī"]}


def test_phrases_give_one_reading_per_character(tmp_path: Path):
    path = write_phrases(tmp_path / "p.txt", ["背离: bèi/lí"])
    assert read_phrases(path, "mengshen") == [Phrase("背离", ["bèi", "lí"], 1)]


def test_a_line_may_hold_a_phrase_and_its_exceptions(tmp_path: Path):
    path = write_phrases(
        tmp_path / "p.txt", ["# note", "着手: zhuó/shǒu, 背着手: bèi/zhe/shǒu"]
    )
    assert read_phrases(path, "mengshen") == [
        Phrase("着手", ["zhuó", "shǒu"], 2),
        Phrase("背着手", ["bèi", "zhe", "shǒu"], 2),
    ]
