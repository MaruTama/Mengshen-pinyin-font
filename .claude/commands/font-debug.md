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

```
otfccbuild: Circular glyph reference found in gid X to gid Y. The reference will be dropped.
```

**原因**

同一の glyph（Unicode の異体字など）が2回グリフ登録されている。
代表的な重複ケース：

| Unicode | グリフ名 |
|---|---|
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
|---|---|---|---|
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
|---|---|
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

```
inputBegins = min(at)
inputEnds   = max(at) + 1
```

`at` は置換が適用されるグリフシーケンス内のインデックス（0始まり）。

`ignore` ルールの場合は `inputBegins` / `inputEnds` を計算した後に `at` を削除する。

**具体例**

```
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

## 使用例

```text
/font-debug Circular glyph reference found in gid 11663
/font-debug 多音字の拼音が Mac で切り替わらない
/font-debug グリフが消えた
/font-debug inputBegins の値がおかしい
/font-debug json dump
/font-debug グリフを SVG で確認したい
```
