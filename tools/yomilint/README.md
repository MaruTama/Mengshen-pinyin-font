# yomilint

親字に読みの注釈を付けるフォント（拼音、注音、ふりがななど）を検証するツールです。
完成したフォントファイルと仕様ファイルだけを見て、「正しい読みが付くか」を確かめます。

設計は [docs/ANNOTATION_FONT_LINT_DESIGN.md](../../docs/ANNOTATION_FONT_LINT_DESIGN.md)
にあります。`yomilint` は仮の名前です。

## 使い方

`fonttools` と `uharfbuzz` が要ります（Python 3.11 以上）。`opentype-sanitizer` を
入れると、`format/ots` の検査も走ります。

```bash
cd tools/yomilint
python -m yomilint check ../../outputs/Mengshen-HanSerif.ttf --spec mengshen.toml
python -m yomilint check FONT --spec SPEC --format json
python -m yomilint check FONT --spec SPEC --select context/
python -m yomilint check FONT --spec SPEC --fail-on warn
```

終了コードは、ERROR が 1 件でもあれば 1、仕様ファイルやデータが読めなければ 2 です。

### 既知の問題を除く

古い問題が残っているフォントでも、新しく増えた問題だけを失敗にできます。

```bash
python -m yomilint baseline FONT --spec SPEC -o known.json
python -m yomilint check FONT --spec SPEC --baseline known.json
```

`known.json` に載っている指摘（検査 ID と対象の組）は数えません。載っているのに出なく
なった指摘は「known but no longer found」と表示するので、一覧から消してください。
仕様ファイルの `[ignore] path` に書いておくこともできます。

一覧にはフォントの名前が入らないので、フォントごとに別のファイルにしてください。
1 つの一覧で 2 つのフォントを検査すると、片方にしかない指摘が、もう片方で
「no longer found」と表示されます。

`--select` を付けると、その検査の指摘だけを一覧にします。

```bash
python -m yomilint baseline FONT --spec SPEC --select geometry/centered -o known.json
```

Mengshen のリリース版は、`geometry/centered` の指摘（許容の 0.01 em を超える字母の
置き方）を `baselines/` に登録してあります。2 つの書体は同じ仕様ファイルを使うので、
`[ignore] path` ではなく `--baseline` で渡します。

```bash
python -m yomilint check FONT --spec mengshen.toml --baseline baselines/Mengshen-HanSerif.json
python -m yomilint check FONT --spec mengshen.toml --baseline baselines/Mengshen-Handwritten.json
```

`centered` 以外の指摘は登録していないので、残ります（HanSerif の `context/phrase`
など）。フォントを作り直して `centered` の指摘が変わったら、`baseline --select
geometry/centered` で作り直してください。

## 今ある検査

| ID | 重大度 | 検査すること |
| --- | --- | --- |
| `coverage/charset-has-glyph` | ERROR | 辞書の文字がすべてフォントにある |
| `coverage/charset-has-reading` | ERROR | 既定のグリフに注釈がある |
| `coverage/default-reading` | ERROR | 既定の読みが辞書の先頭の読みと一致する |
| `coverage/all-readings-reachable` | ERROR | 辞書の読みすべてに、切り替えで届くグリフがある |
| `context/phrase` | ERROR | 語句をシェーピングした結果の読みが期待どおりである |
| `context/phrase-in-sentence` | ERROR | 語句の前後にほかの文字を置いても、読みが変わらない |
| `context/isolated-default` | ERROR | 多音字を単独で置くと既定の読みになる |
| `select/ivs-order` | ERROR | 異体字セレクタの n 番目が、辞書の n 番目の読みを表示する |
| `select/ivs-none` | WARN | 注釈なしを選ぶセレクタがある |
| `select/aalt-covers-readings` | ERROR | `aalt` の候補が、注釈なしと全部の読みを辞書の順に並べている |
| `resolve/methods-agree` | WARN | 部品から求めた読みと、グリフ名から求めた読みが一致する |
| `geometry/no-clipping` | ERROR | 注釈が usWinAscent と usWinDescent の範囲に収まる |
| `geometry/no-overlap` | ERROR | 注釈が親字と重ならず、`[geometry] min_gap` 以上離れている |
| `geometry/advance-matches-base` | ERROR | 読みを切り替えても送り幅が変わらない |
| `geometry/annotation-within-advance` | WARN | 注釈が送り幅からはみ出さない |
| `geometry/centered` | WARN | 注釈の中央が送り幅の中央から `[geometry] center_tolerance`（em に対する比、既定 0.01）以内にある |
| `geometry/baseline-aligned` | WARN | 注釈のベースラインがグリフ間でそろっている（許容 `baseline_tolerance`、em に対する比、既定 0.001） |
| `geometry/min-scale` | WARN | 長い読みの縮小率が `[geometry] min_scale`（既定 0.6）以上である（基準は最も多い大きさ） |
| `geometry/line-gap` | WARN | hhea の行送りで、隣の行の注釈と、フォントのどのグリフ（英字の下に出る部分も）も `min_gap` 以上離れている |
| `format/glyph-count` | WARN | グリフ数に余裕がある |
| `format/tables-parse` | ERROR | fontTools が全テーブルを読める |
| `format/no-circular-reference` | ERROR | 複合グリフに循環参照がない |
| `format/ots` | ERROR | OpenType Sanitizer を通る（入っていなければ走らない） |

寸法の検査（`geometry/`）は、複合グリフの部品を親字と注釈に分けて測ります。
仕様ファイルに `[resolver.letters]` がなく、注釈の字母が cmap にもないフォントでは、
分けられないので何も報告しません。字母が本体と声調記号などの合成グリフでも、1 つの字母として
扱います。`centered`、`baseline-aligned`、`line-gap` は注釈が親字の上か下にあるとき
（`position` が `top` か `bottom`）だけ見ます。`center_tolerance` と
`baseline_tolerance` は em に対する比（0 以上 1 未満）で、範囲外の値は仕様ファイルの
エラーです。
各検査の定義は設計書の 5 章にあります。

検査が例外で止まったときは、その検査の指摘として「the check could not run」を出し、
ほかの検査は続けます。壊れたテーブルが 1 つあっても、残りの結果は得られます。

設計書の最小版の検査と、寸法の検査（`geometry/`）は、これで全部です。拡張（規則の
静的解析、HTML の報告、リリース間の差分、元のフォントとの差分）はまだありません。

## 開発

テストは、fontTools で作る小さな試験用フォント（`tests/fontmaker.py`）を使います。
検査ごとに、通るフォントと、その検査だけが落ちるように壊したフォントを用意します。

```bash
cd tools/yomilint
python -m pytest
```

このリポジトリの `pytest.ini`（`--cov=src`）とは別の設定で動きます。`src/` とは互いに
import しません。
