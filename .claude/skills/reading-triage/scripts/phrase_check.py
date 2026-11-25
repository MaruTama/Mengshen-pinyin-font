#!/usr/bin/env python
"""Build Mengshen fonts for two states and HarfBuzz-check phrase readings.

Subcommands (run from the repo root with the project venv python):

  build <ref|dir> --out DIR
      Build fonts from a git ref (temporary `git worktree` under DIR, removed
      afterwards unless --keep-worktree) or from an existing checkout dir.
      Writes DIR/<style>.ttf, DIR/build_<style>.log and a data snapshot
      DIR/data/ (merged table, phrase files) used by `compare`.
  compare --base DIR --head DIR
      For each style: numGlyphs (and spare to 65,535), sanity shaping (银行),
      standalone default of every char whose default/reading set changed, and
      every phrase of base+head phrase_of_pattern_one/two + phrase_testcase
      (+ --extra files). Prints newly broken (pass on base, fail on head) and
      fixed lists; exits 1 when something newly broke or numGlyphs changed
      (unless --allow-glyph-change).
  all --base <ref|dir> --head <ref|dir> --work DIR
      build both into DIR/base, DIR/head, then compare.

otfcc: the build needs otfcc-rs (caryll otfcc 0.10.4 breaks the big aalt
lookup). Pass --otfcc-bin <dir with otfccbuild/otfccdump> or set OTFCC_BIN.

Phrase file lines are "<word>: <py>/<py>/..."; only polyphonic chars (per the
font's own merged table) are compared. Readings are decoded from the
py_alphabet_* components of the shaped glyphs and NFC-normalized.

    .venv/bin/python .claude/skills/reading-triage/scripts/phrase_check.py all \\
        --base origin/master --head . --work <scratchpad>/pc --otfcc-bin <otfcc-rs>/target/release
"""

# cspell:words uharfbuzz maxp worktrees

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv lists, no shell
import sys
import time
import unicodedata
from pathlib import Path

STYLES = ("han_serif", "handwritten")
MERGED = "outputs/merged-mapping-table.txt"
DUO = "res/phonics/duo_yin_zi"
PHRASE_FILES = (
    "phrase_of_pattern_one.txt",
    "phrase_of_pattern_two.txt",
    "phrase_testcase.txt",
)
OVERWRITE = "res/phonics/unicode_mapping_table/overwrite.txt"
LINE = re.compile(r"^U\+([0-9A-Fa-f]+):\s*([^#]*?)\s*#")
TONE = {"1": "̄", "2": "́", "3": "̌", "4": "̀"}
LETTER = {"v": "ü", "eh": "ê"}
GLYPH_LIMIT = 65535


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s.strip())


def load_table(path: Path) -> dict[str, list[str]]:
    t = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = LINE.match(line)
        if m:
            t[chr(int(m.group(1), 16))] = [
                nfc(x) for x in m.group(2).split(",") if x.strip()
            ]
    return t


def load_phrases(path: Path) -> dict[str, list[str]]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ": " not in line or line.startswith("#"):
            continue
        w, p = line.split(": ", 1)
        w = w.strip()
        if " " in w or "->" in p or "," in p:
            continue
        out[w] = [nfc(x) for x in p.split("/")]
    return out


def run(argv, cwd=None, env=None, log=None):
    if log:
        with open(log, "w", encoding="utf-8") as f:
            return subprocess.run(
                argv, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT
            ).returncode  # nosec
    return subprocess.run(argv, cwd=cwd, env=env).returncode  # nosec B603


def git(*args, cwd=None) -> str:
    out = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True
    )  # nosec B603 B607
    if out.returncode:
        sys.exit(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout.strip()


def main_checkout() -> Path:
    common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir"))
    return common.parent


def otfcc_dir(arg: str | None) -> Path:
    d = arg or os.environ.get("OTFCC_BIN")
    if not d:
        sys.exit(
            "otfcc-rs not given: pass --otfcc-bin <dir containing otfccbuild> or set OTFCC_BIN "
            "(see docs/HOW_TO_MAKE_JP.md 'otfcc（otfcc-rs）'; caryll otfcc 0.10.4 breaks aalt)"
        )
    p = Path(d).expanduser().resolve()
    if not (p / "otfccbuild").exists():
        sys.exit(f"{p}/otfccbuild not found")
    return p


def stale_lines(tree: Path) -> list[str]:
    ow, mt = load_table(tree / OVERWRITE), load_table(tree / MERGED)
    return [c for c, r in ow.items() if c in mt and mt[c] != r]


def prepare_templates(
    tree: Path, py: str, env: dict, styles, cache: Path, temp_tree: bool
) -> None:
    """Fresh worktrees lack the untracked tmp/json/template_glyf_*.json.

    Link a valid copy (template cache, then the main checkout's tmp/json); a stub
    (< 1 MB, e.g. main's handwritten one) does not count. Otherwise run
    make_template_jsons in the tree, restore the tracked template_main json it
    rewrites, and keep a copy in the cache for the next build.
    """
    for st in styles:
        dst = tree / "tmp" / "json" / f"template_glyf_{st}.json"
        if dst.exists() and dst.stat().st_size > 1_000_000:
            continue
        candidates = [cache / dst.name, main_checkout() / "tmp" / "json" / dst.name]
        src = next(
            (c for c in candidates if c.exists() and c.stat().st_size > 1_000_000), None
        )
        if src and src.resolve() != dst.resolve():
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(src.resolve(), dst)
            print(f"  linked {dst.name} from {src.parent}")
            continue
        print(f"  generating {dst.name} (make_template_jsons --style {st})")
        rc = run(
            [py, "-m", "src.refactored.scripts.make_template_jsons", "--style", st],
            cwd=tree,
            env=env,
        )
        if rc or not dst.exists():
            sys.exit(f"make_template_jsons --style {st} failed")
        if temp_tree:
            run(
                ["git", "checkout", "--", f"tmp/json/template_main_{st}.json"], cwd=tree
            )
        cache.mkdir(parents=True, exist_ok=True)
        shutil.copy(dst, cache / dst.name)


def cmd_build(args) -> Path:
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    styles = args.styles.split(",")
    bin_dir = otfcc_dir(args.otfcc_bin)
    py = args.python or sys.executable
    src = args.src
    worktree = None
    if os.path.isdir(src):
        tree = Path(src).resolve()
        sha = git("rev-parse", "HEAD", cwd=tree) + " (+ working tree)"
    else:
        sha = git("rev-parse", src)
        worktree = out / "wt"
        if worktree.exists():
            git("worktree", "remove", "--force", str(worktree))
        git("worktree", "add", "--detach", "-q", str(worktree), sha)
        tree = worktree
    print(f"build {src} ({sha}) in {tree}")
    stale = stale_lines(tree)
    if stale and not args.force:
        sys.exit(
            f"{len(stale)} overwrite.txt lines differ from {MERGED}: regenerate first "
            f"(make_unicode_pinyin_map_table.py then make_pattern_table.py) or pass --force: {''.join(stale[:20])}"
        )
    env = dict(
        os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}", PYTHONPATH="src"
    )
    try:
        prepare_templates(
            tree,
            py,
            env,
            styles,
            (
                Path(args.template_cache)
                if args.template_cache
                else out.parent / "templates"
            ),
            worktree is not None,
        )
        for st in styles:  # sequential: builds share tmp/json intermediates
            t0 = time.time()
            ttf = out / f"{st}.ttf"
            rc = run(
                [py, "-m", "refactored.cli.main", "-t", st, "-o", str(ttf)],
                cwd=tree,
                env=env,
                log=out / f"build_{st}.log",
            )
            print(f"  {st}: rc={rc} {time.time() - t0:.0f}s -> {ttf}")
            if rc:
                sys.exit(f"build failed, see {out / f'build_{st}.log'}")
        data = out / "data"
        data.mkdir(exist_ok=True)
        shutil.copy(tree / MERGED, data / "merged-mapping-table.txt")
        for f in PHRASE_FILES:
            shutil.copy(tree / DUO / f, data / f)
        (out / "info.json").write_text(
            json.dumps({"src": src, "sha": sha, "styles": styles}), encoding="utf-8"
        )
        if worktree is None:
            st = git("status", "--short", "--", "tmp/json", cwd=tree)
            if st:
                print(
                    f"  NOTE tracked tmp/json changed in {tree} (restore with git checkout --):\n{st}"
                )
    finally:
        if worktree is not None and not args.keep_worktree:
            git("worktree", "remove", "--force", str(worktree))
            print(f"  removed worktree {worktree}")
    return out


class Shaper:
    def __init__(self, font: Path, table: dict[str, list[str]]):
        import uharfbuzz as hb
        from fontTools.ttLib import TTFont

        self.hb = hb
        self.tt = TTFont(str(font))
        self.glyf = self.tt["glyf"]
        self.order = self.tt.getGlyphOrder()
        self.font = hb.Font(hb.Face(hb.Blob.from_file_path(str(font))))
        self.table = table
        self.num_glyphs = self.tt["maxp"].numGlyphs

    def reading_of(self, name: str, depth: int = 0) -> str | None:
        g = self.glyf[name]
        if not g.isComposite():
            return None
        out = ""
        for c in g.components:
            n = c.glyphName
            if n.startswith("py_alphabet_"):
                body = n[len("py_alphabet_") :]
                tone = body[-1] if body[-1] in TONE else ""
                letters = body[:-1] if tone else body
                out += LETTER.get(letters, letters) + TONE.get(tone, "")
            elif depth < 3 and not out:
                r = self.reading_of(n, depth + 1)
                if r:
                    return r
        return unicodedata.normalize("NFC", out) if out else None

    def shape(self, text: str) -> list[str | None]:
        buf = self.hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        self.hb.shape(self.font, buf, {})
        return [self.reading_of(self.order[i.codepoint]) for i in buf.glyph_infos]

    def ok(self, word: str, exp: list[str]) -> tuple[bool, list[str | None]]:
        got = self.shape(word)
        if len(got) != len(exp):
            return False, got
        for c, e, g in zip(word, exp, got):
            if len(self.table.get(c, [])) > 1 and g != e:
                return False, got
        return True, got


def cmd_compare(args) -> int:
    base_dir, head_dir = Path(args.base), Path(args.head)
    bt = load_table(base_dir / "data" / "merged-mapping-table.txt")
    ht = load_table(head_dir / "data" / "merged-mapping-table.txt")
    phrases: dict[str, list[str]] = {}
    for d in (base_dir, head_dir):  # head expectations win
        for f in PHRASE_FILES:
            phrases.update(load_phrases(d / "data" / f))
    for f in args.extra or []:
        phrases.update(load_phrases(Path(f)))
    changed = sorted(
        c for c in ht if c in bt and (ht[c][0] != bt[c][0] or set(ht[c]) != set(bt[c]))
    )
    singles = {c: [ht[c][0]] for c in changed + [c for c in args.chars if c in ht]}
    print(
        f"phrases: {len(phrases)}; standalone chars (default/set changed + --chars): {len(singles)}"
    )

    status = 0
    styles = [
        s
        for s in args.styles.split(",")
        if (base_dir / f"{s}.ttf").exists() and (head_dir / f"{s}.ttf").exists()
    ]
    if not styles:
        sys.exit("no style built in both dirs")
    for st in styles:
        b, h = Shaper(base_dir / f"{st}.ttf", bt), Shaper(head_dir / f"{st}.ttf", ht)
        print(f"\n== {st}")
        print(
            f"numGlyphs base {b.num_glyphs} (spare {GLYPH_LIMIT - b.num_glyphs}) / "
            f"head {h.num_glyphs} (spare {GLYPH_LIMIT - h.num_glyphs})"
        )
        if b.num_glyphs != h.num_glyphs:
            print(f"  numGlyphs changed by {h.num_glyphs - b.num_glyphs:+d}")
            if not args.allow_glyph_change:
                status = 1
        for s in (b, h):
            got = s.shape("银行")
            if got[1:] != ["háng"]:
                print(f"  SANITY FAIL: 银行 -> {got} (GSUB broken? otfcc-rs used?)")
                status = 1
        for label, items in (("standalone", singles), ("phrases", phrases)):
            broken, fixed, still = [], [], 0
            for w, exp in items.items():
                ok_h, got_h = h.ok(w, exp)
                ok_b, _ = b.ok(w, exp)
                if not ok_h and ok_b:
                    broken.append(
                        f"{w}\texp={'/'.join(exp)}\tgot={'/'.join(str(x) for x in got_h)}"
                    )
                elif ok_h and not ok_b:
                    fixed.append(w)
                elif not ok_h:
                    still += 1
            print(
                f"  {label}: {len(items)} checked, newly broken {len(broken)}, fixed {len(fixed)}, failing in both {still}"
            )
            for x in broken[: args.limit]:
                print(f"    BROKEN {x}")
            if fixed:
                print(f"    fixed: {' '.join(fixed[: args.limit])}")
            if broken:
                status = 1
            if args.out:
                Path(args.out).mkdir(parents=True, exist_ok=True)
                Path(args.out, f"{st}_{label}_broken.txt").write_text(
                    "".join(x + "\n" for x in broken), encoding="utf-8"
                )
    print("\nRESULT:", "OK" if status == 0 else "CHECK FAILED")
    return status


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    def build_opts(p):
        p.add_argument("--styles", default=",".join(STYLES))
        p.add_argument(
            "--otfcc-bin", help="dir with otfcc-rs otfccbuild/otfccdump (or $OTFCC_BIN)"
        )
        p.add_argument(
            "--python", help="python for the build (default: this interpreter)"
        )
        p.add_argument("--keep-worktree", action="store_true")
        p.add_argument(
            "--force", action="store_true", help="build even if outputs look stale"
        )
        p.add_argument(
            "--template-cache",
            help="dir to keep generated template_glyf_*.json (default: <out>/../templates)",
        )

    def compare_opts(p):
        p.add_argument("--extra", nargs="*", help="more phrase files (word: py/py)")
        p.add_argument(
            "--chars",
            default="",
            help="also check these chars standalone (head default)",
        )
        p.add_argument("--allow-glyph-change", action="store_true")
        p.add_argument("--limit", type=int, default=40)

    pb = sub.add_parser("build")
    pb.add_argument("src", help="git ref or checkout dir")
    pb.add_argument("--out", required=True)
    build_opts(pb)

    pc = sub.add_parser("compare")
    pc.add_argument("--base", required=True, help="build dir")
    pc.add_argument("--head", required=True, help="build dir")
    pc.add_argument("--styles", default=",".join(STYLES))
    pc.add_argument("--out", help="write <style>_<kind>_broken.txt here")
    compare_opts(pc)

    pa = sub.add_parser("all")
    pa.add_argument("--base", required=True, help="git ref or checkout dir")
    pa.add_argument("--head", required=True, help="git ref or checkout dir")
    pa.add_argument("--work", required=True)
    build_opts(pa)
    compare_opts(pa)

    args = ap.parse_args(argv)
    if args.cmd == "build":
        cmd_build(args)
        return 0
    if args.cmd == "compare":
        return cmd_compare(args)
    work = Path(args.work).resolve()
    for name in ("base", "head"):
        ns = argparse.Namespace(
            **vars(args), src=getattr(args, name), out=str(work / name)
        )
        cmd_build(ns)
    ns = argparse.Namespace(
        **{
            **vars(args),
            "base": str(work / "base"),
            "head": str(work / "head"),
            "out": str(work),
        }
    )
    return cmd_compare(ns)


if __name__ == "__main__":
    sys.exit(main())
