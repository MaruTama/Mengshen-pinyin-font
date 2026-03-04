---
name: font-dev
description: Mengshen 拼音フォントプロジェクトの開発ワークフロースキル。TDD サイクル、フォント生成パイプライン、コードフォーマット、多音字パターン追加、開発環境セットアップの手順を案内する。$ARGUMENTS にタスク内容を渡すか、未指定でワークフロー一覧を表示する。
---

# Mengshen Font Project Development Guide

`$ARGUMENTS` にタスク内容を渡してください。
未指定の場合は以下のワークフロー一覧を表示します。

## 利用可能なワークフロー

| キーワード | 内容 |
| --- | --- |
| `overview`, `arch` | アーキテクチャ概要・コンポーネント一覧 |
| `tdd`, `new feature`, `bug fix` | TDD サイクルガイド |
| `build`, `pipeline` | フォント生成パイプライン |
| `format`, `lint` | コードフォーマット・リント |
| `pattern`, `polyphone` | 多音字パターン追加 |
| `setup` | 開発環境セットアップ |

---

## ワークフロー 0: アーキテクチャ概要

### コアパイプライン

```text
TTF → [otfcc dump] → JSON → [拼音処理] → [グリフ統合] → [GSUB生成] → [otfcc build] → TTF
```

| ステップ | 処理内容 | 主要ファイル |
| --- | --- | --- |
| 1. フォントダンプ | TTF → 編集可能 JSON | `src/make_template_jsons.py` / `src/refactored/scripts/make_template_jsons.py` |
| 2. 拼音処理 | 拼音グリフ・発音マッピング生成 | `src/pinyin_glyph.py`, `src/pinyin_getter.py` |
| 3. グリフ統合 | ベースフォントグリフ + 拼音グリフを結合 | `src/font.py` |
| 4. GSUB テーブル生成 | 多音字の文脈的置換ルール作成 | `src/GSUB_table.py` |
| 5. フォント組み立て | JSON → 最終 TTF | `src/font.py` （otfccbuild 呼び出し） |

### 主要コンポーネント

| ファイル | 役割 |
| --- | --- |
| `src/main.py` | CLI エントリーポイント |
| `src/font.py` | ビルドプロセス全体の統制（メイン Font クラス） |
| `src/config.py` | フォントタイプ定義・キャンバスサイズ・トラッキング設定 |
| `src/pinyin_glyph.py` | 拼音グリフ生成・アルファベット処理 |
| `src/GSUB_table.py` | OpenType GSUB テーブル生成 |
| `src/pinyin_getter.py` | Unicode → 拼音マッピング |
| `src/utility.py` | 文字・グリフ操作ユーティリティ |
| `src/shell.py` | ⚠️ シェルコマンド実行（`shell=True` セキュリティ警告あり） |

### フォントスタイル

| スタイル | ベースフォント | 拼音フォント | 定数 |
| --- | --- | --- | --- |
| han_serif | Source Han Serif CN Regular | M+ M Type-1 medium | `HAN_SERIF_TYPE = 1` |
| handwritten | Xiaolai MonoSC | SetoFont SP | `HANDWRITTEN_TYPE = 2` |

### ファイル構造

```text
res/fonts/          ベースフォント（TTF）
res/phonics/        拼音データ・多音字パターン
  duo_yin_zi/       多音字パターン定義
  unicode_mapping_table/  Unicode → 拼音マッピングテーブル
src/                Python ソースコード
  legacy/           旧実装（変更しない）
  refactored/       新実装（開発対象）
tmp/json/           中間 JSON ファイル
outputs/            最終 TTF フォント
tools/              分析・変換ユーティリティ
```

### 新しいコードを追加する場所

- 本番コード → `src/refactored/`（`src/legacy/` には追加しない）
- テスト → `tests/unit/` または `tests/integration/`
- 設定値 → `src/config.py` または `src/refactored/` 内の設定モジュール

---

## ワークフロー 1: TDD サイクル（新機能・バグ修正）

### サイクル

```text
🔴 Red:      失敗するテストを書く（本番コードは書かない）
🟢 Green:    テストを通すための最小限のコードを書く
🔵 Refactor: テストを通したままコードと品質を改善する
```

### テスト実行コマンド

```bash
# すべてのテストを実行
python -m pytest tests/ -v

# カテゴリ別に実行
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/security/ -v

# カバレッジレポートを生成
python -m pytest tests/ --cov=src --cov-report=html

# テスト監視（開発中）
pytest-watch --clear
```

### 完了チェックリスト

- [ ] 🔴 失敗するテストを先に書いた
- [ ] 🟢 テストが通る最小限の実装をした
- [ ] 🔵 テストを通したままリファクタリングした
- [ ] カバレッジ: `src/refactored/` 95% 以上、セキュリティ関連 100%

---

## ワークフロー 2: フォント生成パイプライン

パイプラインの順序:

```text
辞書生成 → JSONダンプ → 拼音抽出 → フォント生成 → 検証
```

### Docker を使う方法（推奨）

```bash
cd <PROJECT ROOT>

# han_serif フォントのみ生成
docker-compose -f docker/docker-compose.yml up pipeline-han-serif

# handwritten フォントのみ生成
docker-compose -f docker/docker-compose.yml up pipeline-handwritten

# 両方のフォントを生成
docker-compose -f docker/docker-compose.yml up pipeline-all
```

### 手動実行（ステップ別）

### ステップ 1: 辞書生成

```bash
cd res/phonics/duo_yin_zi/scripts/
python make_pattern_table.py

cd res/phonics/unicode_mapping_table/
python make_unicode_pinyin_map_table.py
```

### ステップ 2: ベースフォントを JSON にダンプ（refactored 版）

```bash
# glyf テーブルはサイズが大きいため他のテーブルと分離される
PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style han_serif
PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style handwritten
```

### ステップ 3: 拼音アルファベット抽出

```bash
# 固定幅の英字フォントのみ対応（プロポーショナルフォント不可）
PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style han_serif
PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style handwritten
```

### ステップ 4: フォント生成

```bash
# Legacy 版
python src/main.py -t han_serif
python src/main.py -t handwritten

# Refactored 版
PYTHONPATH=src python -m refactored.cli.main -t han_serif
PYTHONPATH=src python -m refactored.cli.main -t handwritten
```

### ステップ 5: 統合テストで回帰確認

```bash
python -m pytest tests/integration/test_complete_pipeline.py -v
```

### 中間ファイルの場所

| ファイル | 説明 |
| --- | --- |
| `tmp/json/<フォント名>.json` | ベースフォントのメタデータ（glyf 以外） |
| `tmp/json/<フォント名>_glyf.json` | glyf テーブル（分離保存） |
| `tmp/json/camp.json` | Unicode（10進）→ グリフ名のマッピング |
| `outputs/` | 最終 TTF フォントファイル |

---

## ワークフロー 3: コードフォーマット・リント

```bash
# インポート整理
isort src/ tests/

# コードフォーマット（88文字幅）
black src/ tests/

# リント
flake8 src/ tests/

# Git フックで一括実行（コミット前と同等）
lefthook run pre-commit
```

### フォーマット設定

| ツール | 設定 |
| --- | --- |
| Black | 88文字幅、自動フォーマット |
| isort | Black 互換プロファイル |
| flake8 | `.flake8` 参照（max-complexity=12） |

---

## ワークフロー 4: 多音字パターン追加

### 手順

1. **パターンファイルを編集**: `res/phonics/duo_yin_zi/` に発音パターンを追加
2. **パターンテーブルを再生成**:

   ```bash
   cd res/phonics/duo_yin_zi/scripts/
   python make_pattern_table.py
   ```

3. **テストを書く**（Red → Green → Refactor）
4. **フォントをビルドして回帰確認**:

   ```bash
   python src/main.py -t han_serif
   python -m pytest tests/integration/ -v
   ```

---

## ワークフロー 5: 開発環境セットアップ

```bash
# Python 依存関係
pip install -r requirements.txt

# 外部ツール（macOS）
brew tap caryll/tap
brew install otfcc-mac64
brew install jq
brew install lefthook

# Git フックを有効化
lefthook install

# 設定確認
lefthook version
```

---

## 使用例

```text
/font-dev
/font-dev overview
/font-dev arch
/font-dev tdd
/font-dev build
/font-dev format
/font-dev add pattern
/font-dev setup
```
