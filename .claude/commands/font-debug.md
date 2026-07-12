---
name: font-debug
description: Mengshen 拼音フォントプロジェクト固有のデバッグスキル。otfccbuild のエラー、GSUB feature の動作不良、グリフ消失などの既知の問題パターンに基づいて診断手順を案内する。エラーメッセージや症状を $ARGUMENTS に渡すか、そのまま実行して対話的に診断する。
---

# Mengshen Font Project Debug Guide

`$ARGUMENTS` にエラーメッセージや症状を渡してください。
渡されない場合は、以下の既知パターン一覧を表示して症状を確認します。

## 診断の進め方

1. `$ARGUMENTS` のエラーメッセージ・症状を既知パターンと照合する
2. 該当するパターンの診断手順を順番に案内する
3. 原因が特定できたら具体的な修正箇所を示す

---

## 既知のデバッグパターン

### パターン1: 循環グリフ参照エラー

**症状（エラーメッセージ）**

```text
otfccbuild: Circular glyph reference found in gid X to gid Y. The reference will be dropped.
```

**原因**

同一の glyph（Unicode の異体字など）が2回グリフ登録されている。
代表的な重複ケース：

| Unicode | グリフ名 |
| --- | --- |
| ⺎ (U+2E8E), 兀 (U+5140), 兀 (U+FA0C) | cid10849 |
| 嗀 (U+55C0), 嗀 (U+FA0D) | cid12670 |

**診断手順**

```bash
# Step 1: 循環参照しているグリフを特定する
cd tools
python find_circular_reference_gid.py
# 出力例: cid10849.ss00

# Step 2: gid から文字を逆引きする（gid は glyph_order の添字）
# camp.json を検索して該当 Unicode を確認する
# 例: "11918": "cid10849"  → U+2E8E (⺎)

# Step 3: overwrite.txt で重複文字の発音が同一になっているか確認する
# 重複している文字はすべて同じ発音が登録されている必要がある
```

**修正箇所**: `src/font.py` でグリフの二重登録を防ぐ処理を確認する。

---

### パターン2: GSUB feature が効かない / 多音字置換が動作しない

**症状**

- 多音字の拼音が切り替わらない
- 特定の環境（Mac など）で feature が動作しない

**feature タグ別の動作（調査済み）**

| タグ | Mac | 用途 | 採用 |
| --- | --- | --- | --- |
| `salt` | ⚠️ 検証時に不可 | スタイル代替 | 非推奨（`rclt` を優先） |
| `aalt` | ✅ | ユーザー向け代替文字表示 | 目的が違う |
| `calt` | ✅ | 文脈依存置換（Chaining contextual substitution） | 使用可 |
| `ccmp` | ✅ | 合字・解字 | 目的が違う |
| `rclt` | ✅ | 文脈依存置換（アラビア文字向けだが全スクリプト適用可） | **採用** |

**このプロジェクトの方針**

- 多音字置換には `rclt` を使用する（ユーザーが無効化できない）
- `salt` は Mac で動作しないため使用禁止

**GSUB lookup の命名規則**

| lookup 名 | 対応パターン |
| --- | --- |
| `lookup_pattern_0N` | pattern one（1文字だけ変化） |
| `lookup_pattern_1N` | pattern two（2文字以上変化） |
| `lookup_pattern_2N` | exception pattern（例外） |

**診断手順**

```bash
# GSUB テーブルを dump して確認する
otfccdump -o out.json --pretty <フォントファイル>.ttf
cat out.json | jq '.GSUB' > gsub.json
# gsub.json で feature タグと lookup の接続を確認する
```

---

### パターン3: グリフが消失する（アフィン変換後）

**症状**

- グリフにアフィン変換（拡大縮小）を設定したのに表示されない
- JSON にグリフデータはあるが、フォントに反映されない

**原因**

otfccbuild の仕様（または OpenType の仕様）で、アフィン変換の `a` と `d` の値が完全に同じ場合にグリフが消失する。

**修正**

`a` と `d` をわずかに異なる値にする：

```json
// ❌ 消失する
{ "a": 0.9, "b": 0, "c": 0, "d": 0.9 }

// ✅ 正しい（値をわずかにずらす）
{ "a": 0.9, "b": 0, "c": 0, "d": 0.91 }
```

**確認箇所**: `src/pinyin_glyph.py` のアフィン変換設定部分

---

### パターン4: `inputBegins` / `inputEnds` の値が期待と異なる

**症状**

- otfcc で dump した GSUB JSON の `inputBegins`、`inputEnds` の値が想定外
- GSUB テーブル生成コードのデバッグ中に値の意味がわからない

**仕様（調査済み）**

```text
inputBegins = min(at)
inputEnds   = max(at) + 1
```

`at` は置換が適用されるグリフシーケンス内のインデックス（0始まり）。

`ignore` ルールの場合は `inputBegins` / `inputEnds` を計算した後に `at` を削除する。

**具体例**

```text
sub [uni4E0D uni9280] uni884C' lookup lookup_0;
  → at: 1, inputBegins: 1, inputEnds: 2

sub A' lookup_1 A' lookup_2 F;
  → at: [0, 1], inputBegins: 0, inputEnds: 2

ignore sub uni80CC uni7740' uni624B;
  → at: None（削除済み）, inputBegins: 1, inputEnds: 2
```

**調査方法**

```bash
otfccdump -o Sawarabi.json --pretty SawarabiMincho-Regular.otf
cat Sawarabi.json | jq '.GSUB' > Sawarabi_GSUB.json
# Sawarabi_GSUB.json で実際の値を確認する
```

---

## otfcc による JSON 展開とテーブル確認

フォントの内部状態を確認したいときは、otfcc で JSON に展開する。

### 基本コマンド

```bash
# TTF/OTF → JSON（pretty モード：閲覧向け）
otfccdump --pretty -o output.json font.ttf

# TTF/OTF → JSON（ugly モード：パイプライン用・高速）
otfccdump -o output.json --ugly font.ttf

# JSON → TTF/OTF（フォント再構築）
otfccbuild input.json -o output.ttf
```

### JSON が大きすぎるときの対処

Source Han Serif 等の大規模フォントは JSON が数百 MB になる。

```bash
# 特定テーブルだけ抽出して別ファイルに保存
cat output.json | jq '.GSUB' > gsub.json
cat output.json | jq '.cmap' > cmap.json
cat output.json | jq '.glyph_order' > glyph_order.json

# less で逐次確認（editor に読み込まず確認する）
less output.json

# jq で整形してから less
cat output.json | jq | less
```

### テーブル別 jq 抽出コマンド

| テーブル | コマンド | 内容 |
| --- | --- | --- |
| GSUB | `jq '.GSUB'` | feature・lookup の定義 |
| cmap | `jq '.cmap'` | Unicode → グリフ名の対応 |
| cmap_uvs | `jq '.cmap_uvs'` | IVS (異体字セレクタ) のマッピング |
| glyph_order | `jq '.glyph_order'` | グリフの並び順（gid の対応） |
| glyf | `jq '.glyf'` | グリフの輪郭データ（非常に大きい） |

```bash
# 特定グリフのデータを確認
cat output.json | jq '.glyf["uni4E0D"]'
cat output.json | jq '.glyf["uni4E0D.ss00"]'

# cmap で Unicode からグリフ名を確認（10進数）
cat output.json | jq '.cmap["19981"]'   # U+4E0D → "uni4E0D"

# GSUB の feature 一覧を確認
cat output.json | jq '.GSUB.features | keys'

# 特定 lookup の内容を確認
cat output.json | jq '.GSUB.lookups["lookup_pattern_00"]'
```

### JSON のテーブル構造（このプロジェクト固有）

```json
{
  "cmap": {
    "19981": "uni4E0D"          // 10進 Unicode → グリフ名
  },
  "cmap_uvs": {
    "19981 917984": "uni4E0D.ss00",   // Unicode + IVS selector → グリフ
    "19981 917985": "uni4E0D.ss01"
  },
  "glyph_order": ["uni4E0D", "uni4E0D.ss00", "uni4E0D.ss01", ...],
  "glyf": {
    "uni4E0D": {
      "advanceWidth": 1536,
      "references": [
        {"glyph": "z_bu4", "x": 1024, "y": 0, "a": 1, "b": 0, "c": 0, "d": 1},
        {"glyph": "uni4E0D.ss00", "x": 0, "y": 0, "a": 1, "b": 0, "c": 0, "d": 1}
      ]
    }
  },
  "GSUB": {
    "languages": { "DFLT_DFLT": { "features": ["rclt_00000", ...] } },
    "features":  { "rclt_00000": ["lookup_pattern_00", ...] },
    "lookups": {
      "lookup_pattern_00": {
        "type": "gsub_chaining",
        "subtables": [{ "match": [...], "apply": [...], "inputBegins": 1, "inputEnds": 2 }]
      }
    }
  }
}
```

### プロジェクトの中間 JSON ファイル

| ファイル | 説明 |
| --- | --- |
| `tmp/json/<フォント名>.json` | ベースフォントのメタデータ（glyf 以外） |
| `tmp/json/<フォント名>_glyf.json` | glyf テーブル（サイズが大きいので分離） |
| `tmp/json/camp.json` | Unicode（10進）→ グリフ名のマッピング |

### ttx を使う場合（代替手段）

```bash
# GSUB テーブルのみ TTX 形式で抽出
ttx -t GSUB font.ttf

# テーブルごとに分割して出力
ttx -s -d ./output font.ttf

# GSUB テーブルを確認してからマージ
ttx -m base.ttf gsub_only.ttx
```

---

---

### パターン5: Unicode 文字のグリフを SVG で目視確認する

**用途**

- 生成フォントのグリフを目視で確認したい
- 多音字グリフ（ss00, ss01 など）の見た目をチェックしたい
- バグ修正前後でグリフ形状を比較したい

**スクリプト**: `tools/extract_glyph_svg.py`（fonttools 使用）

**使い方**

```bash
# 文字を直接指定
python tools/extract_glyph_svg.py 道 outputs/Mengshen-HanSerif.ttf

# Unicode コードポイントで指定（U+XXXX または 16進数）
python tools/extract_glyph_svg.py U+9053 outputs/Mengshen-HanSerif.ttf
python tools/extract_glyph_svg.py 9053 outputs/Mengshen-HanSerif.ttf

# 出力ファイル名を指定
python tools/extract_glyph_svg.py 行 outputs/Mengshen-HanSerif.ttf -o glyph_xing.svg

# PNG プレビューも同時生成（rsvg-convert 必要）
python tools/extract_glyph_svg.py 行 outputs/Mengshen-HanSerif.ttf --preview

# プレビューサイズ指定（デフォルト 400px）
python tools/extract_glyph_svg.py 行 outputs/Mengshen-HanSerif.ttf --preview --preview-size 800

# handwritten フォントで確認
python tools/extract_glyph_svg.py 道 outputs/Mengshen-Handwritten.ttf --preview
```

**出力**

- デフォルト: `U<XXXX>_<グリフ名>.svg`（カレントディレクトリ）
- `--preview` 指定時: `.svg` と `.png` を両方生成
- SVG はブラウザで、PNG は任意のビューアで確認可能

**確認できる内容**

| 確認項目 | 方法 |
| --- | --- |
| グリフ形状が正しいか | SVG をブラウザで開く |
| グリフ名の確認 | 実行時のコンソール出力 `U+9053 (道) → cid41428` |
| 多音字グリフ（ss00）の確認 | cmap_uvs から直接グリフ名を確認し `glyf` を参照 |

**前提条件**

```bash
# fonttools のインストール（pyproject.toml の dev deps に含まれる）
pip install fonttools
```

---

### パターン6: 多音字の拼音が期待と違う（webapp の GSUB 検証タブを使う）

**症状**

- 特定の熟語で拼音が期待と違う読みになる（例: 着手 が zhuó ではなく別の読みになる）
- `scripts/validate_phrase.py` は通るのに、実際にビルドしたフォントで読みがおかしい

**原因（典型例）**

`outputs/duoyinzi_pattern_one.txt` や手書きの `duoyinzi_exceptional_pattern.json` に書かれた
読みの ss 番号（`ss01`, `ss02`, ...）が、現在の `outputs/merged-mapping-table.txt` の読み順と
ずれている。`validate_phrase.py` はパターン表の**内部整合性**（重複・干渉・異読数）しか検証せず、
「生成された GSUB が実際に期待どおりの拼音を出すか」までは検証しない。

**診断ツール**: webapp の 多音字/GSUB → 検証 タブ（`webapp/backend/services/gsub_checker.py`）

このタブは OpenType シェーパーと同じ手順で rclt チェイニングルールをシミュレートし、
`res/phonics/duo_yin_zi/` のフレーズ表（期待読み）と突き合わせて次の3状態に分類する:

| ステータス | 意味 | 対応要否 |
|---|---|---|
| **一致** | 表示される読みが期待どおり | 対応不要 |
| **GSUB未設定** | この熟語・文字にはまだ GSUB に置換ルールが無い（ごく一部は「置換しない」例外ルールによる意図的な抑止。例: 背着手 の 着）。標準の読み（readings[0]）のまま表示される。バグではなく未対応（カバレッジ不足） | 任意（パターン表への追加でカバレッジ拡張可） |
| **誤置換** | ルールは発火したが、期待と異なる読みに置換された | **要修正**。パターン表の ss 番号が現在の読み順とずれている可能性が高い |

**診断手順**

```bash
# API で直接確認する場合
curl -s localhost:8000/api/projects/<id>/gsub/verify | jq '.counts'
curl -s localhost:8000/api/projects/<id>/gsub/verify | jq '.results[] | select(.status=="wrong")'

# 特定フレーズを個別にシミュレートする（フレーズシミュレータと同じ処理）
curl -s -X POST localhost:8000/api/projects/<id>/gsub/simulate \
  -H 'Content-Type: application/json' -d '{"text":"背着手"}' | jq
```

「誤置換」が出た場合は、対象文字の `outputs/merged-mapping-table.txt` の読み順を確認し、
`res/phonics/duo_yin_zi/scripts/make_pattern_table.py` を再実行してパターン表を再生成する
（`res/phonics/duo_yin_zi/phrase_of_exceptional_pattern.txt` は手書きなので ss 番号を手動修正）。

**GSUB タブの「グラフ」表示**でも同じ文字を対象に、コンテキスト → lookup → 読みの関係を
視覚的に確認できる（ignore ルールは赤で表示）。

---

### パターン7: `python -m src.refactored.cli.main -t <style>` が `Missing required files: template_glyf_*.json` で失敗する

**症状**

```text
ERROR: Error: Missing required files: ['template_glyf: /path/to/tmp/json/template_glyf_han_serif.json']
```

新しいクローン・新しいブランチ・新しい worktree でビルドしようとすると必ず起きる。
`tmp/json/template_main_<style>.json`（glyf を除いたメタデータ）は git 管理されているが、
`tmp/json/template_glyf_<style>.json`（glyf テーブル本体、数百MB）は git 管理されておらず、
手元で `res/fonts/` のベースフォントから再生成する必要がある。

**診断手順**

```bash
# 1. どのベースフォントから template_main_<style>.json が作られたか確認する
#    (han_serif -> res/fonts/han-serif/SourceHanSerifCN-Regular.ttf、
#     handwritten -> 対応するベースフォント)

# 2. 同じフォントを otfccdump で展開する
otfccdump -o /tmp/dump.json --pretty res/fonts/han-serif/SourceHanSerifCN-Regular.ttf

# 3. 既存の template_main_<style>.json と head/cmap/glyph_order が一致するか確認する
#    （一致しなければ別バージョンのフォントを掴んでいるので template_main 側を疑う）
python3 -c "
import json
with open('/tmp/dump.json', encoding='utf-8', errors='replace') as f:
    d = json.load(f)
with open('tmp/json/template_main_han_serif.json', encoding='utf-8', errors='replace') as f:
    m = json.load(f)
print('head:', d['head']==m['head'])
print('cmap:', d['cmap']==m['cmap'])
print('glyph_order:', d['glyph_order']==m['glyph_order'])
"

# 4. 一致したら glyf だけ抽出して不足ファイルを作る
jq '.glyf' /tmp/dump.json > tmp/json/template_glyf_han_serif.json
```

handwritten スタイルも同様（`res/fonts/` 配下の対応するベースフォント + `template_glyf_handwritten.json`）。

**注意**: `otfccdump` の出力は UTF-8 として厳密でないバイトを含むことがある
（copyright の `©` 等）。Python で読む際は `encoding='utf-8', errors='replace'` を付ける。

---

### パターン8: otfccbuild の修正が「本当に効いたか」を確認する

**背景**

`otfccbuild` は壊れた GSUB テーブルでも**警告なくビルドを成功させる**ことがある
（パターン2・issue #29/#31/otfcc#1 の GSUB 破損バグが典型例）。
「ビルドが通った」「unit test が通った」だけでは、実際にシェーピングエンジンが
正しく解釈できる状態かどうかの証明にならない。

**3段階の検証手順（このプロジェクトで実際に使った方法）**

```bash
# 1. otfccdump で自己往復させる
#    otfccbuild が壊れたテーブルを吐いた場合、otfccdump 自身が
#    「subtable が空」「lookup を削除した」等の警告を出すことがある
otfccdump -o /tmp/check.json --pretty outputs/Mengshen-HanSerif.ttf 2>&1
# 例: "[WARNING] [Consolidate] Lookup lookup_aalt_1 is empty and will be removed."
#     → ビルド時に投入したデータが失われている証拠

# 2. fontTools の厳格なパーサで読み込めるか確認する
#    otfcc の甘い実装と違い、仕様違反があると例外を出す
python3 -c "
from fontTools.ttLib import TTFont
f = TTFont('outputs/Mengshen-HanSerif.ttf')
gsub = f['GSUB'].table
print('lookup types:', [lk.LookupType for lk in gsub.LookupList.Lookup])
"
# AssertionError や 'Unknown Coverage format: NNNNN' が出たら破損確定

# 3. 実際の HarfBuzz シェーピングで期待通りに動くか確認する
LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
  hb-shape --font-file=outputs/Mengshen-HanSerif.ttf --text="道行" --show-text --output-format=json
# 期待: 2文字目が héng 用の .ssNN グリフになっている
# (hb-shape はロケール未設定だと日本語環境で
#  "変換する入力に無効なバイトの並びがあります" と失敗するので LC_ALL/LANG が必須)
```

**この3段階すべてが揃って初めて「直った」と言える**。1・2だけでは自動置換が
実際に発火するかまでは分からない。

---

## 使用例

```text
/font-debug Circular glyph reference found in gid 11663
/font-debug 多音字の拼音が Mac で切り替わらない
/font-debug グリフが消えた
/font-debug inputBegins の値がおかしい
/font-debug json dump
/font-debug グリフを SVG で確認したい
/font-debug 着手の拼音が期待と違う
/font-debug Missing required files template_glyf
/font-debug GSUB の修正が本当に効いたか確認したい
```
