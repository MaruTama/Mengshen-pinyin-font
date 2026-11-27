# yomilint

親字に読みの注釈を付けるフォント（拼音、注音、ふりがななど）を検証するツールです。
完成したフォントファイルと仕様ファイルだけを見て、「正しい読みが付くか」を確かめます。

設計は [docs/ANNOTATION_FONT_LINT_DESIGN.md](../../docs/ANNOTATION_FONT_LINT_DESIGN.md)
にあります。`yomilint` は仮の名前です。

## 使い方

`fonttools` と `uharfbuzz` が要ります（Python 3.11 以上）。

```bash
cd tools/yomilint
python -m yomilint check ../../outputs/Mengshen-HanSerif.ttf --spec mengshen.toml
python -m yomilint check FONT --spec SPEC --format json
python -m yomilint check FONT --spec SPEC --select context/
python -m yomilint check FONT --spec SPEC --fail-on warn
```

終了コードは、ERROR が 1 件でもあれば 1、仕様ファイルやデータが読めなければ 2 です。

## 今ある検査

| ID | 重大度 | 検査すること |
| --- | --- | --- |
| `coverage/charset-has-glyph` | ERROR | 辞書の文字がすべてフォントにある |
| `coverage/charset-has-reading` | ERROR | 既定のグリフに注釈がある |
| `coverage/default-reading` | ERROR | 既定の読みが辞書の先頭の読みと一致する |
| `coverage/all-readings-reachable` | ERROR | 辞書の読みすべてに、切り替えで届くグリフがある |
| `context/phrase` | ERROR | 語句をシェーピングした結果の読みが期待どおりである |
| `context/isolated-default` | ERROR | 多音字を単独で置くと既定の読みになる |
| `select/ivs-order` | ERROR | 異体字セレクタの n 番目が、辞書の n 番目の読みを表示する |
| `select/ivs-none` | WARN | 注釈なしを選ぶセレクタがある |
| `select/aalt-covers-readings` | ERROR | `aalt` の候補が、注釈なしと全部の読みを辞書の順に並べている |
| `resolve/methods-agree` | WARN | 部品から求めた読みと、グリフ名から求めた読みが一致する |
| `format/glyph-count` | WARN | グリフ数に余裕がある |
| `format/tables-parse` | ERROR | fontTools が全テーブルを読める |

寸法の検査（`geometry/`）と、設計書にある残りの検査はまだありません。

## 開発

テストは、fontTools で作る小さな試験用フォント（`tests/fontmaker.py`）を使います。
検査ごとに、通るフォントと、その検査だけが落ちるように壊したフォントを用意します。

```bash
cd tools/yomilint
python -m pytest
```

このリポジトリの `pytest.ini`（`--cov=src`）とは別の設定で動きます。`src/` とは互いに
import しません。
