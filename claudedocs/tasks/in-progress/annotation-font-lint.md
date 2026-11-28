# Task: 注釈フォント検証ツール（yomilint、仮称）

## 状態

実装中（最小版の検査 19 個、baseline、寸法の残り 4 個まで。静的解析などの拡張は未着手）

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
- [x] 最小版の残り: `context/phrase-in-sentence`、`geometry/` の 4 個、`format/ots`、
      `format/no-circular-reference`、baseline。`context/exception` は
      `context/phrase` と同じ検査になるので、設計書の一覧から外した
- [ ] 既存の検証の置き換え（保留）。`gsub_checker.py` は webapp がビルド前の
      テンプレートを見る機能で、完成したフォントを見る yomilint では置き換えられない。
      `test_built_font_gsub.py` は `tests/` から `tools/` を import しない方針と合わない。
      置き換えるなら、CI でフォントをビルドして yomilint を走らせる形になる
- [ ] 設計書 9 章の未決定の点の決定
- [ ] 寸法のキーの単位をそろえる（`min_gap` などを em に対する比にするか）。別の変更で
- [x] 拡張: 寸法の残り 4 個（`geometry/centered`、`baseline-aligned`、`min-scale`、
      `line-gap`）。左右の注釈は見ない
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
- **原因 2・3 は案 A（`make_exceptional_pattern` の辞書に追記）で修正した。** 例外パターンは
  `make_pattern_table.py` の `make_exceptional_pattern` に手書きされた辞書で、
  `phrase_of_exceptional_pattern.txt` は yomilint と gsub_checker が読む期待値の表にすぎない
  （生成コードは読まない）。GSUB 側の `_make_rclt2_feature`（`gsub_table_generator.py`）は、
  1 つの語句に複数の置換位置を持てて、規則は書かれた順に試され、最初に一致した規則だけが働く。
  そこで次の 3 点を足した（ジェネレータは変更なし）。
  1. `lookup_pattern_20` に `"子": "子.ss02"` を足し、大轴子・压轴子の 子 も替える。
  2. 着 → zhe 用に `lookup_pattern_21 = {"着": "着.ss05"}` を足す。
  3. `背着手` を `着手` より前に置く。
  結果は HanSerif の `context/phrase` が 0 件、GSUB は 18 lookup・19 subtable、123,916 バイト。
  Handwritten も同じ GSUB（18 / 19 / 123,916 バイト）で、`context/phrase` は 差点儿
  （chà/diǎn/ér、期待は r）の 1 件だけ残る。これは Handwritten のみの残件。
  ほかの Handwritten の失敗は修正前と同じ。
  ビルドしたフォントで `tests/integration/test_built_font_gsub.py` も通った。
  Homebrew の otfccbuild（0.10.4）でビルドすると GSUB が壊れるので、otfcc-rs でビルドした。
- **リリース版の HanSerif は、寸法の検査をすべて通る。** 注釈付きのグリフ 31,748 個で、
  注釈と親字のすき間は最小 19.6、注釈の上端は最大 2,439（usWinAscent は 2,628）。
- **検査の速さ。** 異体字セレクタの対応を漢字ごとに全件走査していたのをやめ、
  一度だけ漢字ごとにまとめるようにした。HanSerif で 43 秒が 10 秒になった。
- **寸法の残り 4 個をリリース版で実行した結果。**
  - `geometry/baseline-aligned`、`min-scale` は両書体で 0 件（`line-gap` は下の PR #88
    のレビュー対応で全グリフを見るようにして、1 件ずつ出る）。HanSerif は
    ベースラインが 1914 だけ、字母の倍率は 0.58 だけ（縮小なし）。Handwritten は
    長い読みで横だけ 0.319（ほかは 0.419）に縮め、比は 0.76。行間のすき間は最小 69
    （HanSerif は 558）。
  - `geometry/centered`（許容 0.01 em）は HanSerif で 128 文字（207 グリフ）、ずれは
    0.0100 から 0.0124 em（20.6 から 25.3 ユニット）。すべて字母 1 つ（è、é など声調付き）
    の読みで、字母の置き位置（x = 856）が送り幅の中央より約 23 左にある。見た目には小さい。
    Handwritten は 9,809 文字。字母を送り幅で並べると中央にそろっており、字母の輪郭の
    左右の余白の違いを輪郭の bbox で測っているためのずれ。ずれ（em 比）の中央値は 0.0113、
    最大 0.0506。許容を 0.01 / 0.02 / 0.03 / 0.04 / 0.05 にすると、文字数は
    9,809 / 7,472 / 1,323 / 386 / 33。
- **決めたこと（オーナー）。** `centered` は輪郭の bbox で測る。`center_tolerance` と
  `baseline_tolerance` は em に対する比（UPM で割った値）にする。既定は 0.01 と 0.001
  （HanSerif の 20 ユニット、1 ユニットに相当）。

- **PR #88 のレビュー対応（実フォントでの結果）。**
  - `geometry/centered` の指摘は、フォントごとの baseline（`tools/yomilint/baselines/`）に
    登録した（HanSerif 128 件、Handwritten 9,809 件。`baseline --select geometry/centered`。
    `line-gap` の 1 件ずつも同じファイルに登録）。
    許容の 0.01 em はそのまま。
  - `geometry/line-gap` を、注釈付きの漢字だけでなく cmap の全グリフで見るようにした。
    両書体で 1 件ずつ出る。HanSerif は U+3031（縦書き用の繰り返し記号）の下端が -1116 で
    すき間 -341、Handwritten は U+0326（下に付く結合コンマ）の下端が -258 ですき間 -40。
    漢字だけで見たときの最小すき間は 558 と 69 で、変わらない。オーナー決定で、この 2 件は
    baseline に登録した（検査は全グリフのまま）。登録後の結果は、HanSerif が
    `context/phrase` の 58 件だけ、Handwritten は既存の指摘だけ。`line-gap` は `glyf` が
    ない（CFF）フォントでは何も報告しない。
  - 字母が合成グリフ（本体と声調記号）でも、字母ごとに 1 つの部品として扱う
    （`FontUnderTest.parts` の `stop`）。`min-scale` の基準は最頻の倍率にした。

## 関連

- issue #19（拼音を下に表示）: 注釈の位置を仮定しない設計が要る理由
- issue #20（日本語ルビフォント）: 読みの単位を 1 文字と仮定しない設計が要る理由
- issue #40（壊れた GSUB）: `format/tables-parse` と `select/aalt-covers-readings`
