# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリでコードを扱う際のガイダンスを提供します。
catは使用せず、lessを使用してください。

## プロジェクト概要

これは萌神（Mengshen）拼音フォントプロジェクトです - 中国語フォントに自動的に拼音（発音記号）注釈を生成するオープンソースツールです。このプロジェクトは中国語文字の上に拼音を表示するフォントを作成し、多音字（文脈によって異なる発音を持つ文字）の特別なサポートを提供します。

**主な機能：**

- 簡体字中国語、繁体字中国語、日本語文字のサポート
- OpenType GSUB テーブルを使用した文脈的拼音置換
- Unicode IVS（表意文字異体字セレクタ）サポート
- 2つのフォントスタイル：han_serif と handwritten

## 開発手法

### テスト駆動開発（TDD）

このプロジェクトは、すべての開発とリファクタリング作業において厳格なTDD原則に従います。**必ず**Red-Green-Refactorサイクルを適用してください：

1. **🔴 Red**: 最初に失敗するテストを書く
2. **🟢 Green**: テストを通すための最小限のコードを書く
3. **🔵 Refactor**: テストを通したままコードを改善する

### TDD コマンド

```bash
# すべてのテストを実行
python -m pytest tests/ -v

# カバレッジ付きでテストを実行
python -m pytest tests/ --cov=src --cov-report=html

# セキュリティテストを実行
python -m pytest tests/security/ -v

# 特定のテストカテゴリを実行
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/performance/ --benchmark-only

# 開発中のテスト監視
pytest-watch --clear
```

### テスト要件

- **ユニットテストカバレッジ**: 95%以上必須
- **セキュリティテストカバレッジ**: セキュリティ関連コードは100%
- **統合テスト**: すべての主要パイプラインをカバー
- **パフォーマンステスト**: 回帰なし

### フォント開発のTDDワークフロー（完全パイプライン）

```bash
# 1. 🔴 Red: 既存機能の特性化テストを作成
python -m pytest tests/integration/test_font_output_baseline.py

# 2. 🔴 Red: 新機能/リファクタリング用テストを書く
python -m pytest tests/unit/test_new_feature.py  # 失敗するはず（Red）

# 3. 🟢 Green: テストを通すための最小限のコードを実装
# ソースファイルを編集...
python -m pytest tests/unit/test_new_feature.py  # 成功するはず（Green）

# 4. 🔵 Refactor: テストを通したままコードを改善
# ソースファイルをリファクタリング...
python -m pytest tests/unit/ tests/security/  # すべて成功するはず

# 5. 🧪 Pipeline: 完全なパイプライン検証
# 辞書生成
cd res/phonics/duo_yin_zi/scripts/
python make_pattern_table.py

cd res/phonics/unicode_mapping_table/
python make_unicode_pinyin_map_table.py

# ベースにするフォントを編集可能の状態（json）にダンプする
# glyf table はサイズが大きく閲覧のときに不便なので他のテーブルと分離する。
# han-serif
PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style han_serif
# handwritten
PYTHONPATH=src python -m refactored.scripts.make_template_jsons --style handwritten


# 拼音表示のための文字を抽出する
# 固定幅の英字フォントのみ対応
# han-serif
PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style han_serif
# handwritten
PYTHONPATH=src python -m refactored.scripts.retrieve_latin_alphabet --style handwritten

# フォント生成
cd ../../../..
python src/main.py -t han_serif
python src/main.py -t handwritten

# 6. 🎯 Integration: 完全なテストスイートを実行
python -m pytest tests/ --cov=src

# 7. ✅ Validation: 回帰がないことを確認
python -m pytest tests/integration/test_complete_pipeline.py
```

## ビルドコマンド

### フォント生成

#### レガシー版

```bash
# han_serifフォントを生成
python3 src/main.py  -t han_serif

# handwrittenフォントを生成
python3 src/main.py -t handwritten

# ビルドプロセスの時間測定
time python3 src/main.py
```

#### リファクタ版

```bash
# han_serifフォントを生成
PYTHONPATH=src python -m refactored.cli.main -t han_serif

# handwrittenフォントを生成
PYTHONPATH=src python -m refactored.cli.main -t handwritten
```

### 依存関係セットアップ

```bash
# Python依存関係をインストール
pip install -r requirements.txt

# 外部依存関係をインストール（macOS）
brew tap caryll/tap
brew install otfcc-mac64
brew install jq
```

### パターンテーブル生成

```bash
# 多音字パターンテーブルを生成
cd res/phonics/duo_yin_zi/scripts
python3 make_pattern_table.py
```

## アーキテクチャ概要

### コアパイプライン

フォント生成は以下のパイプラインに従います：

1. **フォントダンプ**: otfccを使用してベースフォント（TTF）を編集可能なJSONに変換
2. **拼音処理**: 拼音グリフと発音マッピングを生成
3. **グリフ統合**: ベースフォントグリフと拼音グリフを結合
4. **GSUB テーブル生成**: 多音字のための文脈的置換ルールを作成
5. **フォント組み立て**: 修正されたJSONから最終的なTTFフォントを構築

### 主要コンポーネント

**メインエントリーポイント：**

- `src/main.py` - CLIインターフェースとフォント生成の統制

**コアフォント処理：**

- `src/font.py` - 全体のビルドプロセスを統制するメインFontクラス
- `src/config.py` - フォントタイプ定義とメタデータ（キャンバスサイズ、トラッキング）
- `src/pinyin_glyph.py` - 拼音グリフ生成とアルファベット処理
- `src/GSUB_table.py` - 文脈的置換のためのOpenType GSUB テーブル生成

**データ処理：**

- `src/pinyin_getter.py` - Unicodeから拼音へのマッピングとWebスクレイピング
- `src/utility.py` - 文字とグリフ操作のユーティリティ関数
- `res/phonics/unicode_mapping_table/` - Unicodeから拼音へのマッピングテーブル
- `res/phonics/duo_yin_zi/` - 多音字パターン定義と処理

**外部ツール統合：**

- `src/shell.py` - ⚠️ シェルコマンド実行（セキュリティ脆弱性を含む）
- `src/make_template_jsons.py` - otfccを使用したフォントからJSONへの変換
- `src/retrieve_latin_alphabet.py` - 拼音用ラテンアルファベット抽出

### フォントスタイルと設定

システムは`src/config.py`で定義された2つのフォントスタイルをサポートします：

- **HAN_SERIF_TYPE (1)**: Source Han Serif + M+ フォントを使用
- **HANDWRITTEN_TYPE (2)**: Xiaolai Font + SetoFontを使用

各スタイルには最適な拼音表示のための特定のキャンバス寸法とトラッキング設定があります。

### 多音字処理

プロジェクトは洗練された多音字処理を実装しています：

- **パターン1**: フレーズ内の単一文字発音変化
- **パターン2**: 複数文字発音変化
- **例外パターン**: 特殊ケース用の手動オーバーライド

パターンファイルは`res/phonics/duo_yin_zi/`にあり、`scripts/`サブディレクトリのスクリプトによって処理されます。

## ファイル構造

**入力アセット：**

- `res/fonts/han-serif/` - Source Han Serif ベースフォント
- `res/fonts/handwritten/` - 手書きスタイルベースフォント
- `res/phonics/` - 拼音と多音字データ

**生成出力：**

- `outputs/` - 最終TTFフォントファイルとパターンテーブル
- `tmp/json/` - フォントの中間JSON表現

**ツール：**

- `tools/` - フォント変換と分析のユーティリティスクリプト

## 重要な注意事項

### TDD開発ルール

**必須**：すべてのコード変更はTDD手法に従う必要があります：

1. **失敗するテストなしに本番コードを書かない**
2. **失敗を実証するのに十分なテストコードのみを書く**
3. **失敗するテストを通すのに十分な本番コードのみを書く**
4. **テストを通したままテストコードと本番コードの両方をリファクタリングする**

### セキュリティ警告（TDD優先）

`src/shell.py`ファイルには`subprocess.run(cmd, shell=True)`による重大なセキュリティ脆弱性があります。

**TDD修正アプローチ**：

```bash
# 1. 最初にセキュリティテストを書く（Red）
def test_no_shell_injection_vulnerability():
    assert not contains_shell_true("src/shell.py")

# 2. 実装を修正（Green）
# 3. 安全にリファクタリング（Blue）
```

これは任意のコマンドインジェクションを可能にし、他の作業の前にTDDを使用して修正する必要があります。

### 外部依存関係

- **otfcc**: フォント解析と生成（必須）
- **jq**: JSON処理（必須）
- **lefthook**: Gitフック管理（開発時）
- requirements.txtにリストされたPythonパッケージ

### 開発環境セットアップ

#### Lefthook（Gitフック）のセットアップ

```bash
# 1. lefthookをインストール（Homebrewの場合）
brew install lefthook

# 2. Gitフックを有効化
lefthook install

# 3. 設定確認
lefthook version
```

#### 開発時のワークフロー

```bash
# コミット前に自動実行される項目：
# - Pythonコードフォーマット（isort + black）
# - Python構文チェック
# - Pythonリンティング（flake8）
# - セキュリティチェック（shell=True検出など）

# プッシュ前に自動実行される項目：
# - コア機能テスト（unit + security）

# スペルチェックはVS Codeで統合されているため、リアルタイムで確認可能

# 手動でフォーマット実行
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# 手動でフックをテスト
lefthook run pre-commit
lefthook run pre-push
```

#### コードフォーマット設定

- **Black**: コードフォーマッター（88文字幅、自動フォーマット）
- **isort**: インポート文整理（Blackと互換性のあるプロファイル）
- **flake8**: コードリンター（.flake8設定ファイル）
- **設定ファイル**: `pyproject.toml`, `.flake8`
- **VS Code統合**: 保存時自動フォーマット

#### スペルチェック設定

- **VS Code統合**: リアルタイムスペルチェック（Code Spell Checker拡張機能）
- **設定ファイル**: `.vscode/settings.json`, `cspell.json`
- **スコープ**: `src/`, `tests/`, `*.md`ファイル

#### VS Code 統合

**自動セットアップ**:

1. Code Spell Checker 拡張機能をインストール（推奨拡張機能に含まれています）
2. プロジェクト設定が自動適用されます

**VS Code設定ファイル**:

- `.vscode/settings.json` - ワークスペース設定とプロジェクト固有単語
- `cspell.json` - Code Spell Checker 詳細設定
- `.vscode/extensions.json` - 推奨拡張機能

### フォントソース

- Source Han Serif CN Regular（han_serifスタイル）
- M+ M Type-1 medium（han_serif用拼音）
- Xiaolai MonoSC（handwrittenスタイル）
- SetoFont SP（handwritten用拼音）

### 文字カバレッジ

- 簡体字中国語：通用規範漢字表に基づく
- 繁体字中国語：Big-5-2003標準に基づく
- 日本語：常用漢字表に基づく
- ひらがなとカタカナサポートを含む

## リファクタリングガイドライン

### TDD優先リファクタリング

詳細なリファクタリング戦略と近代化計画については、`REFACTOR.md`を参照してください。**すべてのリファクタリングはTDD原則に従う必要があります**：

**TDDリファクタリングプロセス**：

1. **既存動作の特性化テストを作成**
2. **望ましい新動作のテストを書く**（Red）
3. **テストを通したまま段階的にリファクタリング**
4. **フォント出力品質の回帰がないことを確認**

### リファクタリング段階（TDD駆動）

- **段階1**: セキュリティテストを最初に行うセキュリティ修正
- **段階2**: 近代化テストを伴うPython 3.11+移行
- **段階3**: 型安全性テストを伴うデータ構造改善
- **段階4**: 統合テストを伴うアーキテクチャリファクタリング
- **段階5**: ベンチマークテストを伴うパフォーマンス最適化
- **段階6**: データ一貫性テストを伴う拼音データ統合
- **段階7**: デプロイメントテストを伴うDockerコンテナ化

**重要なTDDルール**：以下なしには段階は完了とみなせません：

- [ ] 🔴 すべてのテストが書かれ、最初に失敗
- [ ] 🟢 実装によりすべてのテストが通る
- [ ] 🔵 高品質にコードがリファクタリング
- [ ] 🧪 完全なパイプライン検証（辞書+フォント生成）
- [ ] 🎯 統合テストが通る
- [ ] ✅ 出力品質の回帰なし
- [ ] 95%以上のテストカバレッジ達成

**パイプライン検証コマンド**（各段階で通る必要がある）：

```bash
# クイックパイプライン検証
cd res/phonics/duo_yin_zi/scripts && python make_pattern_table.py
cd ../../unicode_mapping_table && python make_unicode_pinyin_map_table.py
cd ../../../.. && python src/main.py -t han_serif

# 完全検証
python -m pytest tests/integration/test_complete_pipeline.py -v
```

## リファクタリングドキュメント要件

### REFACTOR.md更新ポリシー

**必須**：リファクタリング作業を完了する際は、現在の状況を反映するために`REFACTOR.md`を更新する必要があります：

1. **段階状況更新**: 段階状況を「未着手」→「🔄 実装中」→「✅ 完了」に変更
2. **実装詳細**: 実際の実装を反映するようにコード例を更新
3. **完了基準**: 完了項目に✅マークを付け、チェックリストを更新
4. **利益ドキュメント**: 達成された実際の改善を反映するように利益セクションを更新
5. **ファイル変更**: 修正された特定のファイルとその新機能を文書化

### 各段階後の必要更新

```markdown
**Phase X: [Name]** ✅ 完了
**状態**: ✅ 完了

**実装完了状況:**
- [x] Task 1 ✅ (具体的な変更内容)
- [x] Task 2 ✅ (修正されたファイル名)
- [x] Task 3 ✅ (テスト結果)

**実装したアプローチのメリット**:
- **セキュリティ**: 具体的なセキュリティ改善
- **パフォーマンス**: 測定可能な改善結果
- **保守性**: 実装された改善内容
```

### ドキュメントワークフロー

1. **開始時**: Phase status を「🔄 実装中」に更新
2. **実装完了時**: 実装内容を詳細に記録
3. **テスト完了時**: 検証結果とメリットを更新
4. **Phase完了時**: 全チェックボックスを✅に変更

**重要なルール**：リファクタリング作業完了後は必ず`REFACTOR.md`を最新状態に更新してください。これにより、プロジェクトの進捗と現在の実装状況を正確に把握できます。
