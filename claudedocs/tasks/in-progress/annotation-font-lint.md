# Task: 注釈フォント検証ツール（yomilint、仮称）

## 状態

実装中（最小版の第 1 段: 中核、resolver、検査 12 個、CLI まで）

## 概要

拼音、注音、ふりがななど、親字に読みの注釈を付けるフォントを、完成したフォントの
バイナリだけを見て検証するツールを作る。fontbakery のように外部ツールとして公開する
ことを目標に、まずこのリポジトリの `tools/yomilint/` で育てる。

設計書: [docs/ANNOTATION_FONT_LINT_DESIGN.md](../../../docs/ANNOTATION_FONT_LINT_DESIGN.md)

## 決まったこと

- 言語は Python。独立したツールとして作り、後から fontbakery の外部プロファイルに
  対応する。
- 置き場所はこのリポジトリ。フォントの組み立て一般に通じる検査（OTS、元の
  フォントとの差分、計算値の照合）は otfcc-rs のリポジトリで育てる。
- 最初から注音やふりがなも視野に入れる（注釈の位置と読みの単位を仮定しない）。

## サブタスク

- [x] 設計書の案（仕様ファイルの書式、検査の一覧、プロファイル）
- [x] 設計書のレビュー（#84 でマージ）
- [x] 🔴 試験用フォントを作る仕組み（`tests/fontmaker.py`）と、失敗するテスト
- [x] 🟢 中核（読み込み、シェーピング）、resolver（components、names）
- [x] 🟢 検査 12 個（coverage 4、context 2、select 3、resolve 1、format 2）、
      端末と JSON の報告
- [x] 🔵 整形（black、isort）、flake8、mypy。Mengshen-HanSerif（リリース版）で実行
- [ ] 最小版の残り: `context/phrase-in-sentence`、`context/exception`、
      `geometry/` の 4 個、`format/ots`、`format/no-circular-reference`、baseline
- [ ] 既存の `test_built_font_gsub.py` と `gsub_checker.py` の検証を置き換える
- [ ] 設計書 9 章の未決定の点の決定
- [ ] 拡張（静的解析、HTML の報告、diff、source/ の検査）
- [ ] 公開（別リポジトリへの切り出し、PyPI、fontbakery プロファイル）

## 発見事項

- **Mengshen の字母は cmap にない。** `py_alphabet_*` という専用のグリフなので、
  部品を字母に戻すにはグリフ名の規則が要る（設計書 4 章に反映済み）。
- **1 つのグリフが複数の文字に対応する。** 康熙部首（U+2F00 など）と漢字が同じ
  グリフを共有する。グリフから文字を引くときは、対応する文字すべてを見る。
- **リリース版（v20261125）の HanSerif で `context/phrase` が 58 件落ちる。**
  ほかの 11 個の検査は、16,029 文字すべてで通る。原因は 3 つ。
  1. **55 件（漢字 39 個）: パターン表の生成で規則が落ちる。**
     `make_pattern_table.py` の `compress_pattern_one_table` は、パターンのある読みが
     1 種類だけの漢字を「標準の読みしかない」とみなして表から外す。その 1 種類が
     標準でない読み（个 の gè、屏 の bǐng など）でも外れるので、規則がなくなる。
     外した語句は、相手の漢字の標準の読みのパターンに移される（別 に「个~」）。
     条件に「その読みが標準の読みである」を足すと、39 個の漢字の行が表に出て、
     誤って移された語句が消えることを、コピー上で確かめた（フォントのビルドは未確認）。
  2. **1 件（背着手）: 例外の規則が既定の読みに戻すだけ。** `ignore` は 着手 の規則を
     止めるだけなので、着 は既定の zháo になる。語句表は zhe を期待している。
  3. **2 件（大轴子、压轴子）: 2 文字目の読みしか替えない。** 轴 は zhòu になるが、
     子 を軽声の zi にする規則がない。
- **原因 1 の修正と検証（ブランチ `fix/pattern-one-nonstandard-only`）。**
  `compress_pattern_one_table` が外す対象を「パターンのある読みが 1 種類で、かつそれが標準の
  読み」の漢字に絞った。再生成した `outputs/duoyinzi_pattern_one.txt` は +70/−31（39 文字の行が
  戻り、誤って移された語句が消える）。ほかの outputs は変わらない。HanSerif をビルドして
  yomilint を実行すると `context/phrase` が 58 件から 3 件（背着手、大轴子、压轴子）に減り、
  ほかの 11 個の検査は通ったまま。GSUB は 17 lookup・18 subtable のまま、サイズは
  122,434 → 123,858 バイト。Handwritten は 58 件から 4 件（上の 3 件と 差点儿）に減る。
  Handwritten には、修正前後で変わらない別の失敗が残る（`coverage/charset-has-reading`、
  `coverage/all-readings-reachable`、`context/isolated-default`、`select/ivs-order`、
  `select/aalt-covers-readings` が各 2 件、警告 `select/ivs-none`、`resolve/methods-agree` が各 2 件）。
- **原因 2・3 はデータの変更だけで直る（試験済み、未コミット）。** 例外パターンは
  `make_pattern_table.py` の `make_exceptional_pattern` に手書きされた辞書で、
  `phrase_of_exceptional_pattern.txt` は yomilint と gsub_checker が読む期待値の表にすぎない
  （生成コードは読まない）。GSUB 側の `_make_rclt2_feature`（`gsub_table_generator.py`）は、
  1 つの語句に複数の置換位置を持てて、規則は書かれた順に試され、最初に一致した規則だけが働く。
  このため次の 3 点で 3 件とも直った（HanSerif の `context/phrase` が 0 件、GSUB は 18 lookup・
  19 subtable、123,916 バイト）。
  1. `lookup_pattern_20` に `"子": "子.ss02"` を足し、大轴子・压轴子の 子 を
     `{"子": "lookup_pattern_20"}` にする。
  2. 着 → zhe 用に `lookup_pattern_21 = {"着": "着.ss05"}` を足す。
  3. `背着手` を `{背: None, 着: lookup_pattern_21, 手: None}` として `着手` より前に置く。
- **検査の速さ。** 異体字セレクタの対応を漢字ごとに全件走査していたのをやめ、
  一度だけ漢字ごとにまとめるようにした。HanSerif で 43 秒が 10 秒になった。

## 関連

- issue #19（拼音を下に表示）: 注釈の位置を仮定しない設計が要る理由
- issue #20（日本語ルビフォント）: 読みの単位を 1 文字と仮定しない設計が要る理由
- issue #40（壊れた GSUB）: `format/tables-parse` と `select/aalt-covers-readings`
