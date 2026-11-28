# 注釈フォント検証ツール 設計書（案）

親字に読みの注釈を付けるフォント（拼音、注音、粤拼、ふりがななど）を、
完成したフォントファイルだけを見て検証するツールの設計です。fontbakery のように
外部ツールとして公開することを目標に、まずこのリポジトリの中で育てます。

仮の名前は `yomilint` です（「読み」の lint）。名前は公開までに決め直します。

## 1. ねらいと方針

- **ねらい**: 「この文字列を表示したとき、正しい読みが、読める形で付くか」を
  機械的に確かめる。
- **方針 1: 構造ではなく振る舞いを検査する。** 文字列を HarfBuzz でシェーピングし、
  出てきたグリフが表示している読みを期待値と比べる。GSUB を自前で模擬実行しない。
  フォントが `rclt`、`calt`、合字のどれで実装されていても同じ検査が通る。
- **方針 2: 入力はフォントのバイナリと仕様ファイルだけ。** ビルド用のテンプレート
  JSON、グリフの命名規則、生成スクリプトには依存しない。
- **方針 3: フォントごとに違う部分は差し替え式にする。** 違うのは「グリフが
  どの読みを表示しているか」の求め方（4 章）と、注釈の種類ごとの規則（7 章）だけ。

### 今ある検証との関係

| 今あるもの | 置き換え先 |
| --- | --- |
| `tests/integration/test_built_font_gsub.py`（aalt が多音字を網羅するか） | `select/aalt-covers-readings` |
| `webapp/backend/services/gsub_checker.py`（rclt の模擬実行で語句を検証） | `context/phrase`（HarfBuzz で実行） |
| `scripts/validate_phrase.py`（語句表の静的な検査） | データ側の検査として残す。フォントは見ないので対象外 |
| `tools/find_circular_reference_gid.py` | `format/no-circular-reference` |

## 2. 全体の構成

```text
yomilint/
  core/        フォントの読み込み（fontTools）、シェーピング（uharfbuzz）
  resolve/     グリフ → 読み の求め方（4 章）
  spec/        仕様ファイルの読み込みと検証（3 章）
  checks/      検査。1 検査 = 1 関数。ID、重大度、根拠を持つ（5 章）
  profiles/    注釈の種類ごとの規則と検査の組み合わせ（7 章）
  report/      端末、JSON、Markdown、HTML、GitHub Actions の注釈（6 章）
  cli.py       yomilint check FONT... --spec yomilint.toml
```

- 言語は Python（3.11 以上）。依存は fontTools、uharfbuzz、任意で opentype-sanitizer。
- このリポジトリでは `tools/yomilint/` に置き、`src/` のビルド用コードからは
  import しない（逆向きの依存も作らない）。切り出すときにそのまま別リポジトリへ
  移せるようにする。
- テストも `tools/yomilint/tests/` に置き、専用の pytest 設定で動かす。この
  リポジトリの `pytest.ini`（`--cov=src`、カバレッジ 80% 以上）とは分ける。
- fontbakery には、公開の段階で外部プロファイルとして呼べる薄い層を足す。

## 3. 仕様ファイル（`yomilint.toml`）

```toml
[font]
profile = "pinyin"            # generic / pinyin / zhuyin / jyutping / furigana

[annotation]
position = "top"              # top / bottom / right / left（親字に対する位置）
script = "Latn"               # 注釈に使う文字の用字系（注音なら Bopo、ふりがななら Hira）
none_label = "ss00"           # 注釈なしの字形を指す呼び名（任意。レポート用）

[resolver]                    # グリフ → 読み の求め方（4 章）
kind = "components"           # components / names / sidecar
# kind = "names" のとき:
# pattern = '^(?P<base>.+)\.ss(?P<index>\d{2})$'   # index 0 は注釈なし

[resolver.letters]            # 注釈の部品 → 字母 の求め方（components のとき）
# cmap にある部品はそのまま文字に戻す。cmap にない専用のグリフは、名前か対応表で戻す。
pattern = '^py_alphabet_(?P<letter>.+)$'
encoding = "tone-number"      # 名前の中の字母の表し方。プロファイルが解く（a1 → ā、v3 → ǚ）
# table = "letters.json"      # 名前で決まらないときの対応表（グリフ名 → 字母）
# reference_font = "x.ttf"    # 名前がないときに、輪郭で照合する相手のフォント

[dictionary]                  # 文字 → 読みの並び（先頭が既定の読み）
path = "outputs/merged-mapping-table.txt"
format = "mengshen"           # mengshen / tsv / json / unihan
charset = "dictionary"        # 対象の文字集合。dictionary（辞書の全文字）か、別ファイル

[[phrases]]                   # 語句 → 期待する読み
path = "res/phonics/duo_yin_zi/phrase_of_pattern_one.txt"
format = "mengshen"           # 「語句: 読み/読み/…」
[[phrases]]
path = "res/phonics/duo_yin_zi/phrase_of_exceptional_pattern.txt"
format = "mengshen"

[selectors]                   # 手動で読みを切り替える異体字セレクタ
base = 0xE01E0                # base + n が n 番目（0 は注釈なし）
order = "dictionary"          # n 番目の意味。dictionary = 辞書の読みの並び順

[geometry]                    # 寸法の許容値（フォントの単位。省略時は既定値）
min_gap = 0                   # 親字と注釈の間の最小のすき間
center_tolerance = 0.01       # 注釈の中央と送り幅の中央のずれ（em に対する比）
baseline_tolerance = 0.001    # 注釈のベースラインの、最頻値からのずれ（em に対する比）
min_scale = 0.6               # 長い読みを縮めるときの下限（最大の読みに対する比）

[limits]
glyph_headroom = 500          # 65,535 に対して残しておくグリフ数

[ignore]                      # 既知の問題。新しく増えたものだけを失敗にする
path = "yomilint-baseline.json"
```

- 辞書と語句は、形式ごとの読み込み器を差し替えられる。`mengshen` 形式は
  このリポジトリの `merged-mapping-table.txt` と `phrase_of_*.txt` をそのまま読む。
- 読みは「注釈として表示される文字列」で比べる（拼音なら `zhuó`、注音なら `ㄓㄨㄛˊ`、
  ふりがななら `たく`）。正規化（NFC、声調記号の表し方）はプロファイルが決める。

## 4. グリフから読みを求める（resolver）

シェーピングの結果はグリフの並びなので、各グリフが表示している読みを求める必要が
ある。3 つの方式を用意し、仕様ファイルで選ぶ。

| 方式 | 求め方 | 向いているフォント |
| --- | --- | --- |
| `components` | 複合グリフを単純なグリフまで再帰的に展開し、注釈の領域にある部品を字母に戻して、位置の順に並べる | 親字と注釈の字母を部品として持つフォント（Mengshen） |
| `names` | グリフ名を正規表現で分け、番号を辞書の読みの並びに当てる | 命名規則が決まっているフォント |
| `sidecar` | グリフ名 → 読み の JSON を読む | 部品を持たない（輪郭を焼き込んだ）フォント |

- `components` を既定にする。注釈の領域は `annotation.position` と親字の部品の
  bbox から決める。
- 部品を字母に戻す方法は、次の順に試す（`[resolver.letters]`）。
  1. cmap の逆引き。注釈の字母がフォント自身の文字のグリフならこれで決まる。
  2. グリフ名の規則か対応表。Mengshen の字母は cmap にない専用のグリフ
     （`py_alphabet_a1`、`py_alphabet_v3` など）なので、この方法を使う。
     対応表が要る場合でも、字母の数（拼音なら数十）で済む。
  3. 輪郭の照合。グリフ名のないフォントで、拡大縮小をそろえた輪郭を、指定した
     フォントの文字のグリフと比べる。
- Mengshen の複合グリフは入れ子になっている（既定のグリフ → `.ss01` →
  字母と `.ss00`）。展開は `maxp` の深さの上限まで再帰し、循環があれば
  `format/no-circular-reference` の失敗として扱う。
- 2 と `names` はグリフ名に頼る。グリフ名を落としたフォント（`post` の
  version 3）では使えないので、その場合は 1、3、`sidecar` のどれかになる。
- 2 つの方式を両方使える場合（Mengshen）は、結果が一致するかも検査する
  （`resolve/methods-agree`）。命名や番号のずれを見つけられる。
- 1 つの語句が 1 つの合字グリフになるフォント（ふりがなで想定）は、HarfBuzz の
  クラスターごとに読みをまとめて比べる。

## 5. 検査の一覧

重大度は ERROR（読みが誤る、表示が壊れる）、WARN（品質の問題）、INFO（参考）。
「最小版」に ○ が付いたものから作る（- は後の段階）。

### 網羅と辞書（`coverage/`）

| ID | 重大度 | 最小版 | 検査すること |
| --- | --- | --- | --- |
| `coverage/charset-has-glyph` | ERROR | ○ | 対象の文字がすべて cmap にある |
| `coverage/charset-has-reading` | ERROR | ○ | 対象の文字の既定のグリフに注釈がある |
| `coverage/default-reading` | ERROR | ○ | 既定の読みが辞書の先頭の読みと一致する |
| `coverage/all-readings-reachable` | ERROR | ○ | 辞書の読みすべてに、切り替えで届くグリフがある |
| `coverage/valid-reading` | ERROR | - | 表示される読みが正しい形である（プロファイルが定義） |
| `coverage/annotation-letters` | ERROR | - | 注釈に要る字母がすべてフォントにある（拼音なら ǚ、ḿ、ê̄ など） |

### 文脈による読み分け（`context/`）

| ID | 重大度 | 最小版 | 検査すること |
| --- | --- | --- | --- |
| `context/phrase` | ERROR | ○ | 語句をシェーピングした結果の読みが期待どおりである。例外パターン（「着手」と「背着手」）は、語句表の同じ行から別々の語句として読むので、この検査が両方を見る |
| `context/phrase-in-sentence` | ERROR | ○ | 語句の前後にほかの文字を置いても結果が変わらない。置く文字には、どの語句テストにも出てこない文字を選ぶ |
| `context/isolated-default` | ERROR | ○ | 多音字を単独で置くと既定の読みになる |
| `context/rule-conflict` | WARN | - | 同じ文脈に違う結果を出す規則がない（GSUB の静的解析） |
| `context/unreachable-rule` | WARN | - | 前の規則に隠れて決して発動しない規則がない |
| `context/feature-always-on` | WARN | - | 読み分けが、既定で有効な機能（`rclt`、`calt` など）に入っている |

### 手動の切り替え（`select/`）

| ID | 重大度 | 最小版 | 検査すること |
| --- | --- | --- | --- |
| `select/ivs-order` | ERROR | ○ | 読みが複数ある文字で、異体字セレクタの n 番目が辞書の n 番目の読みを表示する。辞書の読みの数だけセレクタがある |
| `select/ivs-none` | WARN | ○ | 対象のすべての文字（読みが 1 つの文字を含む）に、注釈なしを選ぶセレクタがあり、注釈のない字形になる |
| `select/aalt-covers-readings` | ERROR | ○ | `aalt` の候補が、注釈なしと全部の読みを辞書の順に並べている |
| `select/ivs-after-context` | WARN | - | セレクタを付けた文字は、文脈による読み分けより優先される |

### 注釈の寸法（`geometry/`）

| ID | 重大度 | 最小版 | 検査すること |
| --- | --- | --- | --- |
| `geometry/no-clipping` | ERROR | ○ | 注釈が usWinAscent と usWinDescent の範囲に収まる（Windows で切れない）。hhea の ascender は行送りを決める値で、超えても切れないので見ない |
| `geometry/no-overlap` | ERROR | ○ | 注釈と親字の bbox が重ならず、`min_gap` 以上離れている |
| `geometry/advance-matches-base` | ERROR | ○ | 注釈付きのグリフの送り幅が、注釈なしと同じ |
| `geometry/annotation-within-advance` | WARN | ○ | 注釈が送り幅からはみ出さない |
| `geometry/centered` | WARN | ✓ 実装済み | 注釈の中央が送り幅の中央にある（`center_tolerance` 以内） |
| `geometry/baseline-aligned` | WARN | ✓ 実装済み | 注釈のベースラインがグリフ間でそろっている |
| `geometry/min-scale` | WARN | ✓ 実装済み | 長い読みの縮小率が `min_scale` 以上である |
| `geometry/line-gap` | WARN | ✓ 実装済み | 行間の指定で、隣の行の注釈と親字がぶつからない |

`centered`、`baseline-aligned`、`min-scale`、`line-gap` の定義は、実装で次のように決めた。
どれも、注釈が親字の上か下にあるとき（`position` が `top` か `bottom`）の検査で、
左右にあるときは何も報告しない（`annotation-within-advance` と同じ扱い）。

- `centered`: 注釈の輪郭の bbox の中央と、親字の既定のグリフの送り幅の中央の差。
  差が `center_tolerance`（em に対する比。UPM で割った値）を超えると指摘する。輪郭の
  bbox で測ると決めた（字母の左右の余白の違いも「見える中央」として数える）。送り幅が違うグリフは
  `advance-matches-base` が見るので、基準は既定のグリフの送り幅にそろえ、二重に
  指摘しない。
- `baseline-aligned`: 字母の部品を置く y（部品の原点。字母の字形はベースラインを
  原点に作る前提）を、注釈の字母すべてで数え、最頻値を「フォントのベースライン」と
  する。それと `baseline_tolerance`（em に対する比）を超えて違う字母のあるグリフを
  指摘する。
- `min-scale`: 字母の部品を描く倍率（変換の横と縦の倍率の小さいほう）を、グリフごとに
  最小の字母で表す。全グリフのうち最大の倍率を「縮めていない大きさ」として、それに
  対する比が `min_scale` 未満のグリフを指摘する。
- `line-gap`: 行送りは hhea の `ascender - descender + lineGap`。`top` なら、下の行の
  注釈のいちばん上（全グリフで最大）と、上の行の親字のいちばん下（全グリフで最小）の
  すき間が `[geometry] min_gap` に満たないと指摘する。`bottom` なら上下を逆にする。
  最悪の組み合わせの 1 件だけを報告する。Windows が使う usWin の値や、
  `USE_TYPO_METRICS` で選ばれる typo の値での行送りは見ない。

### 読みの求め方（`resolve/`）

| ID | 重大度 | 最小版 | 検査すること |
| --- | --- | --- | --- |
| `resolve/methods-agree` | WARN | ○ | 部品から求めた読みと、グリフ名から求めた読みが一致する（両方の方式が使えるフォントだけ） |

### 形式の上限と健全性（`format/`）

| ID | 重大度 | 最小版 | 検査すること |
| --- | --- | --- | --- |
| `format/glyph-count` | ERROR | ○ | グリフ数が 65,535 以内。余裕が `glyph_headroom` 未満なら WARN |
| `format/ots` | ERROR | ○ | OpenType Sanitizer を通る（入っていなければスキップ） |
| `format/tables-parse` | ERROR | ○ | fontTools で全テーブルを読める（壊れた GSUB を見つける） |
| `format/no-circular-reference` | ERROR | ○ | 複合グリフに循環参照がない |
| `format/maxp-composite` | WARN | - | 複合グリフの深さと部品数が `maxp` の値以内である |
| `format/derived-values` | WARN | - | bbox などの計算値が、輪郭から求めた値と一致する |

### 元のフォントとの差分（`source/`。元のフォントを渡したときだけ）

| ID | 重大度 | 最小版 | 検査すること |
| --- | --- | --- | --- |
| `source/base-outline` | ERROR | - | 親字の輪郭が元のフォントと同じである |
| `source/other-glyphs` | WARN | - | 注釈に関係しないグリフ（かな、記号など）が変わっていない |

### リリース間の差分（`yomilint diff OLD NEW`）

検査ではなく報告。既定の読みが変わった文字、結果が変わった語句、増減したグリフを
一覧にする。

`format/derived-values` と `source/` は、フォントの組み立て一般に通じる検査なので、
実装は otfcc-rs 側（ビルドし直したフォントを元のフォントと比べる仕組み）と考え方を
そろえ、共通にできる部分は otfcc-rs のリポジトリで育てる。

## 6. 実行と報告

```bash
yomilint check outputs/Mengshen-HanSerif.ttf --spec yomilint.toml
yomilint check FONT --spec SPEC --format json > report.json
yomilint check FONT --spec SPEC --select 'context/*' --fail-on warn
yomilint baseline FONT --spec SPEC          # 今の失敗を既知の問題として保存
yomilint diff OLD.ttf NEW.ttf --spec SPEC
```

- 終了コード: ERROR が 1 件でもあれば 1。`--fail-on warn` で WARN も失敗にする。
- 結果の 1 件は「検査 ID、重大度、対象（文字、語句、グリフ）、期待値、実際の値」を
  持つ。同じ原因の失敗が大量に出るときは、検査ごとに件数と先頭の数件にまとめる。
- HTML の報告は、失敗した語句を実際に描いた画像を付ける（期待と実際を並べる）。
- 既知の問題（baseline）に載っている失敗は数えず、「解消した」ものは知らせる。

## 7. プロファイル

プロファイルは「読みの正規化と妥当性の規則」と「使う検査の組み合わせ」を持つ。

| プロファイル | 読みの形 | 固有の規則 | 既定の位置 |
| --- | --- | --- | --- |
| `generic` | 任意の文字列 | なし | top |
| `pinyin` | 声調記号付きの音節（`zhuó`）。軽声は記号なし | 音節表にあること。声調記号の位置。`ü` の扱い | top |
| `zhuyin` | 注音符号と声調（`ㄓㄨㄛˊ`） | 声母・介音・韻母の並び。声調記号の位置（軽声は前） | right |
| `jyutping` | 音節と声調の数字（`zoek6`） | 音節表にあること | top |
| `furigana` | かな（`たく`）。語句単位の読みあり | かなだけであること。送りがなは注釈に含めない | top |

最初から 4 種類すべてを作るのではなく、次の点だけ最初から守る。

- 注釈の位置（上下左右）を仮定しない。寸法の検査は「親字に対する向き」で書く。
- 読みの単位を「1 文字 = 1 音節」と仮定しない。ふりがなは語句単位（熟字訓）が
  あるので、比べる単位は HarfBuzz のクラスターにする。
- 読みの妥当性はプロファイルに閉じ込め、中核には拼音の知識を入れない。

## 8. 進め方

1. **最小版**（このリポジトリの `tools/yomilint/`）
   - `components`（字母は cmap の逆引きとグリフ名の規則まで）と `names` の
     resolver、`mengshen` 形式の読み込み器。
   - 5 章で「最小版 ○」の検査、端末と JSON の報告、baseline。
   - Mengshen の 2 書体で動かし、`test_built_font_gsub.py` と `gsub_checker.py` の
     検証をこのツールの呼び出しに置き換える。
   - 開発は TDD。小さな試験用フォントを fontTools の FontBuilder で作り、検査ごとに
     「通るフォント」と「落ちるフォント」を用意する。
2. **拡張**: 規則の静的解析、寸法の残りの検査、HTML の報告、`diff`、
   `source/` の検査。
3. **公開**: 別リポジトリへ切り出し、名前の確定、PyPI、ドキュメント、GitHub Action、
   fontbakery の外部プロファイル、`zhuyin` と `furigana` のプロファイル。

## 9. 未決定の点

- 寸法のキーの単位。`center_tolerance` と `baseline_tolerance` は em に対する比にしたが、
  `min_gap` などの既存のキーはフォントの単位のまま。そろえるなら別の変更で行う。
- ツールの名前（`yomilint` は仮）。
- 語句テストの大きな公開データ（CC-CEDICT など）を任意で取り込むか。ライセンスは
  CC BY-SA なので、同梱せずダウンロードする形になる。
- 縦書き（`vert`、`vmtx`）での注釈の位置を検査の対象にするか。
- HarfBuzz 以外のシェーパー（DirectWrite、CoreText）との差をどこまで扱うか。
  CI では HarfBuzz だけになる。
