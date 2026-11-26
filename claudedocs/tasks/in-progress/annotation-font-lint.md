# Task: 注釈フォント検証ツール（yomilint、仮称）

## 状態

設計中（設計書の案を作成。実装は未着手）

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
- [ ] 設計書のレビューと、未決定の点（設計書 9 章）の決定
- [ ] 🔴 試験用フォントを作る仕組み（FontBuilder）と、最初の検査の失敗するテスト
- [ ] 🟢 中核（読み込み、シェーピング）、resolver（components、names）
- [ ] 🟢 最小版の検査（設計書 5 章の ○）、端末と JSON の報告、baseline
- [ ] 🔵 Mengshen の 2 書体で実行し、既存の `test_built_font_gsub.py` と
      `gsub_checker.py` の検証を置き換える
- [ ] 拡張（静的解析、HTML の報告、diff、source/ の検査）
- [ ] 公開（別リポジトリへの切り出し、PyPI、fontbakery プロファイル）

## 関連

- issue #19（拼音を下に表示）: 注釈の位置を仮定しない設計が要る理由
- issue #20（日本語ルビフォント）: 読みの単位を 1 文字と仮定しない設計が要る理由
- issue #40（壊れた GSUB）: `format/tables-parse` と `select/aalt-covers-readings`
