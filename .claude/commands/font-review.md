---
name: font-review
description: Mengshen 拼音フォントプロジェクト固有のコードレビュースキル。Python スタイル（black/isort/flake8/mypy）、フォント規格（グリフ命名規則・IVS コード・feature タグ・glyf 制約）、OS サポート（Mac/Windows/Android での feature 動作）の3軸でチェックする。src/refactored/ の変更や新機能追加時に使用する。
---

# Mengshen Font Project Code Review

`$ARGUMENTS` で指定されたファイルまたはディレクトリをレビューする。指定がない場合は直近の変更ファイルを対象とする。

## レビュー手順

1. 対象ファイルを読み込み、以下の2軸でチェックする
2. 問題を重要度順（Critical → Warning → Suggestion）に列挙する
3. 具体的な修正例を示す

---

## 1. Python スタイルチェック

### コードフォーマット

- **Black 準拠**: 88文字以上の行、不適切なクォート、不要な括弧
- **isort 準拠**: インポート順序（標準ライブラリ → サードパーティ → ローカル）
- **flake8 規則**: 未使用インポート、未使用変数、空白の問題

### 複雑度

- 関数の循環的複雑度が 12 を超えていないか（`.flake8` の `max-complexity = 12`）
- 関数が長すぎないか（目安: 50行以内）

### 型アノテーション（`src/refactored/` のみ厳格適用）

- 関数の引数と戻り値に型ヒントがあるか
- `Any` の過剰使用がないか
- `Optional` / `Union` が適切か（Python 3.10+ では `X | Y` を推奨）

### レガシーコードの扱い

- `src/legacy/` は型ヒント・複雑度の規則を緩く適用する（既存コードは変更しない）
- `src/refactored/` は厳格に適用する

---

## 2. フォントプロジェクト規格チェック

### TDD 遵守（Critical）

- 本番コードの変更に対応するテストが `tests/` に存在するか
- テストが Red → Green → Refactor サイクルを意識した構造か
- カバレッジ: `src/refactored/` は 95% 以上、セキュリティ関連は 100%

### セキュリティ（Critical）

- `subprocess.run(cmd, shell=True)` または `shell=True` の使用を検出したら必ず指摘
- コマンドインジェクションの可能性がある文字列結合
- 代替案: `subprocess.run(["cmd", arg1, arg2], shell=False)` を提案

### パイプライン構造の遵守

フォント生成パイプラインの各ステップが正しいモジュールに実装されているか確認する：

```
Font dump (TTF→JSON) → Pinyin processing → Glyph integration → GSUB table → Font assembly
```

- フォントダンプ処理: `src/refactored/scripts/make_template_jsons.py`
- 拼音処理: `src/refactored/` 内の pinyin 関連モジュール
- GSUB テーブル: `src/GSUB_table.py`（または refactored 版）
- エントリーポイント: `src/main.py` / `src/refactored/cli/main.py`

### インポート規則

- `src/refactored/` 内のモジュールは `PYTHONPATH=src` を前提としたインポートを使用しているか
- 例: `from refactored.processing.xxx import yyy`（`src.refactored...` は不可）

### ファイル配置規則

- 新しいコードは `src/refactored/` に追加する（`src/legacy/` には追加しない）
- テストは `tests/unit/` または `tests/integration/` の適切な場所に配置する
- 設定値は `src/config.py` または `src/refactored/` 内の設定モジュールに集約する

---

## 3. フォント規格チェック

### グリフ命名規則

| グリフ名 | 役割 |
| --- | --- |
| `hanzi_glyf` | 標準の読みの拼音付きグリフ |
| `hanzi_glyf.ss00` | 拼音なし漢字グリフ（IVS で拼音を切り替えるベース） |
| `hanzi_glyf.ss01` | 標準の読みの拼音（多音字があるとき GSUB 置換を無効化して強制置換するため用意） |
| `hanzi_glyf.ss02` 以降 | 異読の拼音（多音字の各読みに対応） |

- `ss00` ～ `ss20` の範囲内に収まっているか（OpenType 仕様の上限）
- `ssXX` に標準の拼音を入れないと `cmap_uvs` で戻したときに GSUB が再適用される問題があることを把握しているか

### IVS コード割り当て

| IVS コード | 対応グリフ |
| --- | --- |
| `0xE01E0` | 何もないグリフ（拼音なし） |
| `0xE01E1` | 標準的な拼音 |
| `0xE01E2` 以降 | 異読の拼音 |

### GSUB lookup 命名規則

| lookup 名 | 対応パターン |
| --- | --- |
| `lookup_pattern_0N` | pattern one（熟語内で1文字だけ拼音が変化） |
| `lookup_pattern_1N` | pattern two（熟語内で2文字以上拼音が変化） |
| `lookup_pattern_2N` | exception pattern（例外的なパターン） |

### feature tag の使用規則

| タグ | 用途 | 使用可否 |
| --- | --- | --- |
| `aalt` | 代替文字の表示（`aalt_0`: gsub_single、`aalt_1`: gsub_alternate） | ✅ |
| `rclt` | 多音字置換（ユーザーが無効化できない） | ✅ **採用** |
| `salt` | スタイル代替 | ⚠️ 検証時に Mac（特定アプリ）で動作しなかった。`rclt` を優先すること |

### フォント仕様の制約

- **横書きのみ対応**（縦書きは非対応）。縦書き処理を実装していないか確認
- **glyf table の上限**: 65536 グリフ。グリフ数が増加する変更では上限に注意
- **拼音グリフ**: 等幅英字フォントのみ使用可能（プロポーショナルフォント不可）
- **JSON 処理**: 標準ライブラリの `json` ではなく `orjson` を使用しているか
- **重複 Unicode**: ⺎(U+2E8E)/兀(U+5140)/兀(U+FA0C)、嗀(U+55C0)/嗀(U+FA0D) は同一グリフを参照させること

---

## 4. OS サポートチェック

### GSUB feature の OS 別動作

コードが新しい feature タグを追加・変更している場合にチェックする：

| feature | macOS | Windows | Android | iOS |
| --- | --- | --- | --- | --- |
| `rclt` | ✅ | ✅ | ✅（アプリ依存） | ✅（アプリ依存） |
| `calt` | ✅ | ✅ | ✅（アプリ依存） | ✅（アプリ依存） |
| `salt` | ⚠️ 検証時に不可 | 未確認 | 未確認 | 未確認 |
| `aalt` | ✅ | ✅ | ✅（アプリ依存） | ✅（アプリ依存） |

- 新しい feature を追加する場合は `rclt` または `calt` を使うこと
- `salt` は検証時（macOS・特定アプリ）で動作しなかった実績がある。`rclt` を優先すること

### Android 固有の注意事項

- 多音字（homograph）サポートはアプリによって異なる
- zFont 経由のインストール：Galaxy / LG / HUAWEI / vivo / Honor / OPPO / Xiaomi で動作確認済み
- Magisk モジュール経由のインストール：root 必須、Android 10(Q)以降は EXT4 dedup filesystem に注意
- フォントを変更しても反映されない場合は再起動が必要（コードのコメントや README に記載があるか確認）

### チェック項目

新しい GSUB feature や lookup を追加・変更するコードに対して：

- `salt` を新たに使っていないか（検証時に Mac で動作しなかった実績あり。詳細は `doc/note2myself/NOTE.md` 参照）
- 縦書き用の処理が誤って横書きに影響していないか
- glyf table のグリフ数が 65536 を超えていないか（追加系の変更のとき）

---

## 出力フォーマット

```
## レビュー結果: <ファイルパス>

### 🔴 Critical
- [行番号] 問題の説明
  修正例: `修正後のコード`

### 🟡 Warning
- [行番号] 問題の説明

### 💡 Suggestion
- [行番号] 改善提案

### ✅ 良い点
- 適切に実装されている箇所のコメント

### 📋 チェックサマリー
| 項目 | 結果 |
| --- | --- |
| Black 準拠 | ✅ / ❌ |
| isort 準拠 | ✅ / ❌ |
| 型アノテーション | ✅ / ❌ |
| TDD 遵守 | ✅ / ❌ |
| shell=True なし | ✅ / ❌ |
| パイプライン構造 | ✅ / ❌ |
| グリフ命名規則 | ✅ / ❌ / N/A |
| feature タグ規則 | ✅ / ❌ / N/A |
| OS サポート | ✅ / ❌ / N/A |
```

---

## 使用例

```
/font-review src/refactored/processing/pinyin_processor.py
/font-review src/refactored/
/font-review tests/unit/glyph/
```
