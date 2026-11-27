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
  語句表（`phrase_of_pattern_one.txt`）にある語句が、生成されたパターン表
  （`outputs/duoyinzi_pattern_one.txt`）になく、フォントに規則がない。
  例: 个别（gè/bié のはずが ge/bié）、屏除、惜别、臭虫。原因の調査は未着手。
  ほかの 11 個の検査は、16,029 文字すべてで通る。

## 関連

- issue #19（拼音を下に表示）: 注釈の位置を仮定しない設計が要る理由
- issue #20（日本語ルビフォント）: 読みの単位を 1 文字と仮定しない設計が要る理由
- issue #40（壊れた GSUB）: `format/tables-parse` と `select/aalt-covers-readings`
