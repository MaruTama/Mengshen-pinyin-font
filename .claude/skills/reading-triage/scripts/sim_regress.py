#!/usr/bin/env python
"""Estimate common-word regressions between two states of the reading data.

Approximates the font's lookup (phrase_of_pattern_two.txt -> duoyinzi_pattern_one.txt
-> default = first reading of merged-mapping-table.txt) for every word of
pypinyin's phrases_dict (<= --max-len chars) and compares the result with the
word's pypinyin reading. A word is "regressed" when base renders it correctly
and head does not, "improved" for the opposite. Only chars whose default or
patterns differ between base and head are evaluated (--all-chars: every char).

This is an approximation (no chain-context interaction, no exceptional
patterns); confirm findings with phrase_check.py (HarfBuzz on built fonts).

    python .claude/skills/reading-triage/scripts/sim_regress.py --base origin/master
    python .claude/skills/reading-triage/scripts/sim_regress.py \\
        --base origin/data/overwrite-remove-identical \\
        --head origin/data/overwrite-order-only-63 --chars 似尽据
    python .claude/skills/reading-triage/scripts/sim_regress.py --base HEAD --head .   # working tree

--base / --head take a git ref (read via `git show <ref>:<path>`) or a directory
(a worktree / checkout root). --head defaults to the current directory.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import re
import subprocess  # nosec B404 - fixed git argv, no shell
import sys
import unicodedata
from collections import Counter
from pathlib import Path

MERGED = "outputs/merged-mapping-table.txt"
P1 = "outputs/duoyinzi_pattern_one.txt"
P2 = "res/phonics/duo_yin_zi/phrase_of_pattern_two.txt"
OVERWRITE = "res/phonics/unicode_mapping_table/overwrite.txt"
LIST_8105 = "res/pinyin-data/tools/china-8105-06062014.txt"
LINE = re.compile(r"^U\+([0-9A-Fa-f]+):\s*([^#]*?)\s*#")
P1_LINE = re.compile(r"^(\d+), (.), ([^,]+), \[(.*)\]$")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s.strip())


def read_src(src: str, path: str) -> str:
    if os.path.isdir(src):
        return Path(src, path).read_text(encoding="utf-8")
    out = subprocess.run(  # nosec B603 B607
        ["git", "show", f"{src}:{path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if out.returncode:
        sys.exit(f"git show {src}:{path} failed: {out.stderr.strip()}")
    return out.stdout


def parse_table(text: str) -> dict[str, list[str]]:
    d = {}
    for line in text.splitlines():
        m = LINE.match(line)
        if m:
            d[chr(int(m.group(1), 16))] = [
                nfc(x) for x in m.group(2).split(",") if x.strip()
            ]
    return d


def parse_p1(text: str) -> dict[str, list[tuple[int, str, list[str]]]]:
    d: dict[str, list] = {}
    for line in text.splitlines():
        m = P1_LINE.match(line.strip())
        if m:
            d.setdefault(m.group(2), []).append(
                (int(m.group(1)), nfc(m.group(3)), m.group(4).split("|"))
            )
    return d


def parse_p2(text: str) -> dict[str, list[str]]:
    d = {}
    for line in text.splitlines():
        if ":" in line and not line.startswith("#"):
            w, r = line.split(":", 1)
            d[w.strip()] = [nfc(x) for x in r.strip().split("/")]
    return d


class State:
    def __init__(self, src: str):
        self.src = src
        self.table = parse_table(read_src(src, MERGED))
        self.p1 = parse_p1(read_src(src, P1))
        self.p2 = parse_p2(read_src(src, P2))
        self.overwrite = parse_table(read_src(src, OVERWRITE))

    def stale(self) -> list[str]:
        """overwrite.txt lines whose merged-table entry differs (outputs not regenerated)."""
        return [
            c
            for c, r in self.overwrite.items()
            if c in self.table and self.table[c] != r
        ]

    def render(self, word: str, i: int) -> tuple[str | None, str]:
        for w, r in self.p2.items():
            if len(r) != len(w):
                continue
            st = 0
            while (j := word.find(w, st)) >= 0:
                if j <= i < j + len(w):
                    return r[i - j], "p2"
                st = j + 1
        c = word[i]
        for _order, reading, pats in self.p1.get(c, []):
            for pat in pats:
                if "~" not in pat:
                    continue
                k = pat.index("~")
                full = pat.replace("~", c)
                s = i - k
                if s >= 0 and word[s : s + len(full)] == full:
                    return reading, "p1"
        return (self.table[c][0] if c in self.table else None), "def"


def find_phrases(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    spec = importlib.util.find_spec("pypinyin")
    candidates = []
    if spec and spec.origin:
        candidates.append(Path(spec.origin).with_name("phrases_dict.json"))
    candidates.append(
        Path(".venv/lib/python3.11/site-packages/pypinyin/phrases_dict.json")
    )
    candidates += [
        Path(p)
        for p in glob.glob(
            os.path.expanduser("~/.cache/uv/archive-v0/*/pypinyin/phrases_dict.json")
        )
    ]
    for c in candidates:
        if c.exists():
            return c
    sys.exit(
        "pypinyin phrases_dict.json not found: pass --phrases or `uv pip install pypinyin`"
    )


def load_levels(src_dirs: list[str]) -> dict[str, int]:
    for d in src_dirs + ["."]:
        p = Path(d) / LIST_8105
        if os.path.isdir(d) and p.exists():
            lv = {}
            for line in p.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[0].startswith("U+"):
                    n = int(parts[1])
                    lv[chr(int(parts[0][2:], 16))] = (
                        1 if n <= 3500 else 2 if n <= 6500 else 3
                    )
            return lv
    return {}


def affected_chars(base: State, head: State) -> set[str]:
    chars = {
        c
        for c in head.table
        if c in base.table and head.table[c][0] != base.table[c][0]
    }
    chars |= {
        c for c in set(base.p1) | set(head.p1) if base.p1.get(c) != head.p1.get(c)
    }
    p2_changed = (set(base.p2) ^ set(head.p2)) | {
        w for w in base.p2 if head.p2.get(w) not in (None, base.p2[w])
    }
    for w in p2_changed:
        chars |= set(w)
    return chars


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--base", required=True, help="git ref or directory")
    ap.add_argument("--head", default=".", help="git ref or directory (default: cwd)")
    ap.add_argument("--phrases", help="pypinyin phrases_dict.json (auto-detected)")
    ap.add_argument("--chars", default="", help="only report these chars")
    ap.add_argument(
        "--all-chars",
        action="store_true",
        help="evaluate every char, not only changed ones",
    )
    ap.add_argument("--max-len", type=int, default=4)
    ap.add_argument(
        "--levels",
        default="1,2",
        help="8105 levels to list (1,2,3,0=表外); counts cover all",
    )
    ap.add_argument("--limit", type=int, default=25, help="words listed per char")
    ap.add_argument("--json", help="write {regressed, improved} per char to this file")
    args = ap.parse_args(argv)

    base, head = State(args.base), State(args.head)
    for st, name in ((base, "base"), (head, "head")):
        s = st.stale()
        if s:
            print(
                f"WARNING {name}: {len(s)} overwrite lines differ from {MERGED} (regenerate?): {''.join(s[:30])}"
            )
    changed_default = {
        c
        for c in head.table
        if c in base.table and head.table[c][0] != base.table[c][0]
    }
    set_changed = {
        c
        for c in head.table
        if c in base.table and set(head.table[c]) != set(base.table[c])
    }
    print(
        f"default changed: {len(changed_default)} chars; reading set changed: {len(set_changed)} chars"
    )

    targets = None if args.all_chars else affected_chars(base, head)
    focus = set(args.chars) if args.chars else None
    phrases = json.loads(find_phrases(args.phrases).read_text(encoding="utf-8"))
    lv = load_levels([args.head, args.base])
    want = {int(x) for x in args.levels.split(",") if x}

    reg: dict[str, list[str]] = {}
    imp: dict[str, list[str]] = {}
    checked = 0
    for w, rs in phrases.items():
        if len(w) != len(rs) or len(w) > args.max_len:
            continue
        for i, c in enumerate(w):
            if targets is not None and c not in targets:
                continue
            if focus and c not in focus:
                continue
            if c not in head.table or len(head.table[c]) < 2:
                continue
            exp = nfc(rs[i][0])
            b, _ = base.render(w, i)
            h, how = head.render(w, i)
            checked += 1
            if b == exp and h != exp:
                reg.setdefault(c, []).append(f"{w}({exp}->{h}/{how})")
            elif b != exp and h == exp:
                imp.setdefault(c, []).append(f"{w}({b}->{exp})")

    print(f"evaluated {checked} (word, char) positions")
    for name, dd in (("REGRESSED", reg), ("IMPROVED", imp)):
        total = sum(len(v) for v in dd.values())
        by_lv = Counter()
        for c, v in dd.items():
            by_lv[lv.get(c, 0)] += len(v)
        print(
            f"===== {name}: {total} words in {len(dd)} chars  (by level: {dict(sorted(by_lv.items()))})"
        )
        for c in sorted(dd, key=lambda c: (lv.get(c, 9) or 9, -len(dd[c]))):
            if lv.get(c, 0) not in want and not focus:
                continue
            tag = {1: "一级", 2: "二级", 3: "三级"}.get(lv.get(c, 0), "表外")
            print(f"{tag} {c} {len(dd[c])}: {' '.join(dd[c][: args.limit])}")
    if args.json:
        Path(args.json).write_text(
            json.dumps(
                {"regressed": reg, "improved": imp}, ensure_ascii=False, indent=1
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
