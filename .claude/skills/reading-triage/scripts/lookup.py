#!/usr/bin/env python
"""Show everything needed to triage one character's readings.

For each character: the pinyin-data line (res/pinyin-data/pinyin.txt), the
overwrite.txt line, the merged table line, which pinyin-data source files attest
each reading, Unihan kMandarin / kHanyuPinlu, optional Taiwan MOE (moedict.tw)
order, a category, the 通用规范汉字表 level and a decision hint.

Run from the repo root (stdlib only):

    python .claude/skills/reading-triage/scripts/lookup.py 似 尽 冠
    python .claude/skills/reading-triage/scripts/lookup.py --moe 茄 括
    python .claude/skills/reading-triage/scripts/lookup.py --all-overwrite --tsv

Readings are compared NFC-normalized.
"""

# cspell:words Hanyu Pinlu TGHZ cedict moedict

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path.cwd()
PD_DIR = ROOT / "res" / "pinyin-data"
PINYIN_TXT = PD_DIR / "pinyin.txt"
OVERWRITE = ROOT / "res" / "phonics" / "unicode_mapping_table" / "overwrite.txt"
MERGED = ROOT / "outputs" / "merged-mapping-table.txt"
LIST_8105 = PD_DIR / "tools" / "china-8105-06062014.txt"
UNIHAN_URL = "https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip"
MOE_URL = "https://www.moedict.tw/a/{}.json"
DEFAULT_CACHE = Path.home() / ".cache" / "mengshen-reading-triage"

# Readings kept on purpose (never upstream): issue #30, PR #54, issue #18
PROJECT_SPECIFIC = {
    "诶": "#30 诶 éi,ēi,ěi,èi",
    "地": "#18 地 dì first",
    "呣": "PR #54 ḿ/ń/ê restore",
    "哏": "PR #54 ḿ/ń/ê restore",
    "哽": "PR #54 ḿ/ń/ê restore",
    "唔": "PR #54 ḿ/ń/ê restore",
    "嗯": "PR #54 ḿ/ń/ê restore",
    "嘸": "PR #54 ḿ/ń/ê restore",
    "欸": "PR #54 ḿ/ń/ê restore",
    "誒": "PR #54 ḿ/ń/ê restore",
}
# Order fixes kept in overwrite.txt as upstream candidates (#75 comment 7101813255)
UPSTREAM_KEPT = set(
    "子泊茸粘琢椎嗦嘛瘩澎嚼虺珩菟豉摒嘬擘扞芘柷峿堲桲婤葰楪暿孅轘似茄伺尽藉俟柞葚切"
)
SYLLABIC = re.compile(r"^(ê|[mn]g?)$")
LINE = re.compile(r"^U\+([0-9A-Fa-f]+):\s*([^#]*?)\s*(?:#(.*))?$")

# Source files of pinyin-data shown first; any other *.txt is appended
PD_ORDER = [
    "pinyin.txt",
    "kMandarin.txt",
    "kMandarin_8105.txt",
    "kMandarin_overwrite.txt",
    "kTGHZ2013.txt",
    "kXHC1983.txt",
    "kHanyuPinyin.txt",
    "kHanyuPinlu.txt",
    "zdic.txt",
    "cc_cedict.txt",
    "overwrite.txt",
]


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s.strip())


def strip_tone(s: str) -> str:
    d = unicodedata.normalize("NFD", s)
    return "".join(c for c in d if unicodedata.category(c) != "Mn" or c == "̂")


def load_table(path: Path) -> dict[str, tuple[list[str], str]]:
    """{char: (readings, comment)} for files in "U+XXXX: a,b  # c" format."""
    table: dict[str, tuple[list[str], str]] = {}
    if not path.exists():
        return table
    for line in path.read_text(encoding="utf-8").splitlines():
        m = LINE.match(line.strip())
        if not m:
            continue
        readings = [nfc(x) for x in m.group(2).split(",") if x.strip()]
        table[chr(int(m.group(1), 16))] = (readings, (m.group(3) or "").strip())
    return table


def load_8105() -> dict[str, int]:
    serial: dict[str, int] = {}
    if not LIST_8105.exists():
        return serial
    for line in LIST_8105.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].startswith("U+"):
            serial[chr(int(parts[0][2:], 16))] = int(parts[1])
    return serial


def level_of(n: int | None) -> str:
    if n is None:
        return "表外"
    if n <= 3500:
        return f"一级 ({n})"
    if n <= 6500:
        return f"二级 ({n})"
    return f"三级 ({n})"


class Unihan:
    """kMandarin / kHanyuPinlu / kTraditionalVariant from Unihan.zip or a dir."""

    FIELDS = {"kMandarin", "kHanyuPinlu", "kTraditionalVariant"}

    def __init__(self, source: Path | None):
        self.data: dict[tuple[str, str], str] = {}
        self.source = source
        if source is None:
            return
        for name in ("Unihan_Readings.txt", "Unihan_Variants.txt"):
            for line in self._lines(source, name):
                if not line.startswith("U+"):
                    continue
                cp, field, value = line.rstrip("\n").split("\t", 2)
                if field in self.FIELDS:
                    self.data[(chr(int(cp[2:], 16)), field)] = value

    @staticmethod
    def _lines(source: Path, name: str):
        if source.is_dir():
            p = source / name
            if p.exists():
                yield from p.open(encoding="utf-8")
            return
        with zipfile.ZipFile(source) as z:
            with z.open(name) as f:
                yield from io.TextIOWrapper(f, encoding="utf-8")

    def get(self, ch: str, field: str) -> str | None:
        return self.data.get((ch, field))


def find_unihan(arg: str | None, cache: Path, download: bool) -> Path | None:
    candidates = [arg, os.environ.get("UNIHAN_PATH"), str(cache / "Unihan.zip")]
    for c in candidates:
        if c and Path(c).expanduser().exists():
            return Path(c).expanduser()
    if download:
        cache.mkdir(parents=True, exist_ok=True)
        dest = cache / "Unihan.zip"
        print(f"downloading {UNIHAN_URL} -> {dest}", file=sys.stderr)
        urllib.request.urlretrieve(UNIHAN_URL, dest)  # nosec B310 (fixed https URL)
        return dest
    return None


def moe_readings(ch: str, cache: Path) -> list[str] | None:
    """Taiwan MOE (国语辞典) reading order: moedict.tw /a/<char>.json h[].p."""
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"moe_{ord(ch):X}.json"
    if not path.exists():
        url = MOE_URL.format(urllib.parse.quote(ch))
        req = urllib.request.Request(url, headers={"User-Agent": "reading-triage"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:  # nosec B310
                path.write_bytes(r.read())
        except Exception as e:  # noqa: BLE001 - network errors are reported only
            print(f"  (moedict {ch}: {e})", file=sys.stderr)
            return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    out = []
    for h in data.get("h", []):
        p = h.get("p")
        if p:
            for x in re.split(r"[\s　]+", p):
                x = nfc(re.sub(r"[（(].*?[)）]", "", x))
                if x and x not in out:
                    out.append(x)
    return out


def categorize(ow: list[str] | None, pd: list[str] | None) -> str:
    if pd is None:
        return "missing"
    if ow is None:
        return "no-overwrite"
    if ow == pd:
        return "identical"
    so, sp = set(ow), set(pd)
    if so == sp:
        return "order-only"
    if so < sp:
        return "subset"
    return "addition"  # refined to attested-addition / unattested by caller


def first_of(value: str | None) -> str | None:
    if not value:
        return None
    return nfc(re.sub(r"\(.*?\)", "", value.split()[0]))


def analyse(ch, tables, merged, serial, unihan, args):
    pd = tables["pinyin.txt"].get(ch, (None, ""))[0]
    ow_entry = load_overwrite().get(ch)
    ow = ow_entry[0] if ow_entry else None
    cat = categorize(ow, pd)
    readings = list(dict.fromkeys((ow or []) + (pd or [])))
    attest = {
        r: [
            f
            for f, t in tables.items()
            if f != "pinyin.txt" and r in t.get(ch, ([], ""))[0]
        ]
        for r in readings
    }
    extra = [r for r in (ow or []) if pd is not None and r not in pd]
    lacking = [r for r in (pd or []) if ow is not None and r not in ow]
    unattested = [r for r in extra if not attest[r]]
    if cat == "addition":
        cat = "unattested" if unattested else "attested-addition"

    km_u = unihan.get(ch, "kMandarin")
    freq = unihan.get(ch, "kHanyuPinlu")
    km_pd = tables["kMandarin.txt"].get(ch, (None, ""))[0]
    km_first = first_of(km_u) or (km_pd[0] if km_pd else None)
    freq_first = first_of(freq)
    if not freq_first and ch in tables["kHanyuPinlu.txt"]:
        freq_first = tables["kHanyuPinlu.txt"][ch][0][0]

    moe = None
    if args.moe:
        moe = {}
        targets = [ch]
        tv = unihan.get(ch, "kTraditionalVariant")
        if tv:
            targets = [chr(int(x[2:], 16)) for x in tv.split()]
        for t in targets:
            moe[t] = moe_readings(t, args.cache_dir)

    project = PROJECT_SPECIFIC.get(ch)
    if not project and any(SYLLABIC.match(strip_tone(r)) for r in (ow or [])):
        project = "syllabic ê/m/n reading (PR #54 type)"

    hint = decide(
        ch, cat, ow, pd, km_first, freq_first, extra, lacking, unattested, project
    )
    return {
        "char": ch,
        "cp": f"U+{ord(ch):04X}",
        "level": level_of(serial.get(ch)),
        "category": cat,
        "pinyin_data": pd,
        "overwrite": ow,
        "merged": merged.get(ch, (None, ""))[0],
        "attest": attest,
        "extra": extra,
        "lacking": lacking,
        "kMandarin": km_u or (",".join(km_pd) if km_pd else None),
        "kHanyuPinlu": freq
        or (
            ",".join(tables["kHanyuPinlu.txt"][ch][0])
            if ch in tables["kHanyuPinlu.txt"]
            else None
        ),
        "km_first": km_first,
        "freq_first": freq_first,
        "moe": moe,
        "project": project,
        "hint": hint,
        "files": {f: t[ch] for f, t in tables.items() if ch in t},
    }


def decide(ch, cat, ow, pd, km, freq, extra, lacking, unattested, project):
    if project:
        return f"KEEP: project-specific ({project}); never upstream"
    if ch in UPSTREAM_KEPT and cat == "order-only":
        return "KEEP reordered: listed as upstream candidate in #75 (delete once pinyin-data adopts it)"
    if cat == "missing":
        return "pinyin.txt has no entry: overwrite is the only source (upstream addition candidate)"
    if cat == "no-overwrite":
        return "no overwrite line: pinyin-data order applies"
    if cat == "identical":
        return "DELETE overwrite line (identical to pinyin-data)"
    if cat == "unattested":
        return (
            f"DELETE reading(s) {','.join(unattested)} (attested nowhere in pinyin-data; "
            f"glyphs -{len(unattested)}, later IVS numbers shift)"
        )
    if cat == "attested-addition":
        return (
            f"extra {','.join(extra)} attested elsewhere: if needed KEEP + upstream PR "
            "candidate (mozillazg/pinyin-data via MaruTama/pinyin-data); else delete it"
        )
    if cat == "subset":
        return (
            f"overwrite lacks {','.join(lacking)}: deleting the line adds "
            f"{len(lacking)} reading(s) (glyph count +); judge if they are wanted"
        )
    # order-only
    evidence = [x for x in (km, freq) if x]
    if not evidence:
        return (
            "order-only, no kMandarin/kHanyuPinlu evidence: judge manually (ask user)"
        )
    if all(x == pd[0] for x in evidence):
        return (
            f"likely DELETE overwrite line (pinyin-data first {pd[0]} = kMandarin/kHanyuPinlu); "
            "confirm it is the usual standalone reading, then run sim_regress"
        )
    if all(x == ow[0] for x in evidence):
        return (
            f"likely KEEP reordered (set = pinyin-data, first {ow[0]}) + upstream candidate "
            "(add to #75 comment)"
        )
    return f"order-only, evidence split (kMandarin={km}, Pinlu={freq}): judge manually"


_OW_CACHE: dict | None = None


def load_overwrite():
    global _OW_CACHE
    if _OW_CACHE is None:
        _OW_CACHE = load_table(OVERWRITE)
    return _OW_CACHE


def print_text(r):
    j = ",".join
    print(f"■ {r['char']} {r['cp']}  {r['level']}  [{r['category']}]")
    print(f"  pinyin.txt : {j(r['pinyin_data']) if r['pinyin_data'] else '-'}")
    print(f"  overwrite  : {j(r['overwrite']) if r['overwrite'] else '-'}")
    print(f"  merged     : {j(r['merged']) if r['merged'] else '-'}")
    print(f"  kMandarin  : {r['kMandarin'] or '-'}")
    print(f"  kHanyuPinlu: {r['kHanyuPinlu'] or '-'}")
    if r["moe"] is not None:
        for t, v in r["moe"].items():
            print(f"  MOE {t}     : {j(v) if v else '-'}")
    print("  attested by:")
    for reading, files in r["attest"].items():
        short = " ".join(f.removesuffix(".txt") for f in files) or "(nowhere)"
        print(f"    {reading:<8} {short}")
    print("  source lines:")
    for f, (rs, comment) in r["files"].items():
        print(
            f"    {f.removesuffix('.txt'):<18} {j(rs)}"
            + (f"  # {comment}" if comment else "")
        )
    print(f"  => {r['hint']}")
    print()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("chars", nargs="*", help="characters or U+XXXX")
    ap.add_argument(
        "--all-overwrite", action="store_true", help="every overwrite.txt line"
    )
    ap.add_argument(
        "--category", help="only print this category (with --all-overwrite)"
    )
    ap.add_argument(
        "--unihan", help="Unihan.zip or extracted dir (else $UNIHAN_PATH / cache)"
    )
    ap.add_argument(
        "--download-unihan",
        action="store_true",
        help=f"fetch {UNIHAN_URL} into the cache",
    )
    ap.add_argument(
        "--moe", action="store_true", help="fetch Taiwan MOE order from moedict.tw"
    )
    ap.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--tsv", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not PINYIN_TXT.exists():
        sys.exit(
            f"{PINYIN_TXT} not found: run from the repo root with the submodule checked out"
        )

    chars = []
    for a in args.chars:
        for tok in a.split(","):
            if tok.upper().startswith("U+"):
                chars.append(chr(int(tok[2:], 16)))
            else:
                chars.extend(c for c in tok if not c.isspace())
    if args.all_overwrite:
        chars.extend(load_overwrite())
    if not chars:
        ap.error("no characters")

    names = [f for f in PD_ORDER if (PD_DIR / f).exists()]
    names += sorted(p.name for p in PD_DIR.glob("*.txt") if p.name not in names)
    tables = {f: load_table(PD_DIR / f) for f in names}
    merged = load_table(MERGED)
    serial = load_8105()
    src = find_unihan(args.unihan, args.cache_dir, args.download_unihan)
    if src is None:
        print(
            f"note: Unihan not found (kHanyuPinlu counts unavailable). Pass --unihan <Unihan.zip|dir>, "
            f"set UNIHAN_PATH, or --download-unihan ({UNIHAN_URL}). Falling back to "
            "pinyin-data kMandarin.txt / kHanyuPinlu.txt.",
            file=sys.stderr,
        )
    unihan = Unihan(src)

    rows = [
        analyse(c, tables, merged, serial, unihan, args) for c in dict.fromkeys(chars)
    ]
    if args.category:
        rows = [r for r in rows if r["category"] == args.category]
    if args.json:
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=1)
        print()
    elif args.tsv:
        cols = [
            "char",
            "cp",
            "level",
            "category",
            "pinyin_data",
            "overwrite",
            "kMandarin",
            "kHanyuPinlu",
            "hint",
        ]
        print("\t".join(cols))
        for r in rows:
            print(
                "\t".join(
                    ",".join(r[c]) if isinstance(r[c], list) else str(r[c] or "")
                    for c in cols
                )
            )
    else:
        for r in rows:
            print_text(r)
    if args.all_overwrite or len(rows) > 5:
        from collections import Counter

        print(
            "categories:", dict(Counter(r["category"] for r in rows)), file=sys.stderr
        )


if __name__ == "__main__":
    main()
