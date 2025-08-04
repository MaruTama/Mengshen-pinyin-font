# リファクタコード向けテスト計画

## 概要

萌神拼音フォントプロジェクトのリファクタコード向けの包括的なテスト計画です。TDD（テスト駆動開発）原則に従い、セキュリティ強化、品質向上、保守性の確保を目的としています。

## テスト戦略

### 1. テスト駆動開発（TDD）原則

- **Red-Green-Refactor**サイクルを厳格に適用
- すべての新機能とリファクタリングはテストファーストで実装
- 既存動作の特性化テストを先に作成してから改善

### 2. テストカテゴリ分類

- **Unit Tests（単体テスト）**: 個別コンポーネントの動作検証
- **Integration Tests（結合テスト）**: コンポーネント間の連携検証
- **Security Tests（セキュリティテスト）**: 脆弱性防止検証
- **Performance Tests（パフォーマンステスト）**: 性能回帰防止
- **Characterization Tests（特性化テスト）**: 既存動作の保護

## テスト実装状況

### ✅ 完了済み

#### 1. テストインフラ

- **pytest設定**: `pytest.ini`で各種マーカーと設定を定義
- **フィクスチャ**: `tests/conftest.py`で共通テストデータを提供
- **ディレクトリ構成**: 機能別にテストファイルを整理

#### 2. 単体テスト（Unit Tests） - **220/220テスト通過 (100%)**

##### A. 設定システム（Config System） - 100% 完了（34/34テスト）

- ✅ `test_font_config.py`: フォント設定の検証（19テスト）
- ✅ `test_constants.py`: 定数と値の検証（15テスト）

##### B. データ管理（Data Management） - 100% 完了（77/77テスト）

- ✅ `test_pinyin_data.py`: 拼音データ管理（21テスト）
- ✅ `test_character_data.py`: 文字データ管理（26テスト）
- ✅ `test_mapping_data.py`: マッピングデータ管理（30テスト）

##### C. フォント処理（Font Processing） - 100% 完了（16/16テスト）

- ✅ `test_font_builder.py`: フォント構築（16テスト）

##### D. ユーティリティ（Utilities） - 100% 完了（34/34テスト）

- ✅ `test_cmap_utils.py`: CMapユーティリティ（34テスト）

##### E. CLI・コマンドラインインターフェース - 100% 完了（29/29テスト）

- ✅ `test_main.py`: CLIメインエントリーポイント（29テスト）

##### F. グリフ処理（Glyph Processing） - 100% 完了（30/30テスト）

- ✅ `test_pinyin_glyph.py`: 拼音グリフ生成（30テスト）

```python
# 実装済みテスト例
def test_pinyin_data_manager_loading():
    """拼音データマネージャーのデータ読み込み"""
    manager = PinyinDataManager()
    assert manager.get_pinyin("中") == ["zhōng", "zhòng"]

def test_font_builder_initialization():
    """FontBuilderの初期化テスト"""
    builder = FontBuilder(font_type=FontType.HAN_SERIF, ...)
    assert builder.font_type == FontType.HAN_SERIF
```

#### 3. テストカバレッジ実績

- **実装済みモジュール**: 6つの主要コンポーネント
- **テスト成功率**: 100% (220/220テスト通過)
- **TDD原則**: 全テストでRed-Green-Refactorサイクル適用
- **モックとプロパティテスト**: 包括的エラーハンドリング検証

### 🔄 実装中

#### 1. 結合テスト（Integration Tests）

##### フォント生成パイプライン - 骨格完了、実装継続中

- ✅ `test_complete_pipeline.py`: 完全パイプラインテスト骨格
- 🔄 HAN_SERIFフォント生成テスト
- 🔄 HANDWRITTENフォント生成テスト
- 🔄 テンプレートJSON作成テスト
- 🔄 ラテンアルファベット抽出テスト

#### 2. セキュリティテスト拡張

- 🔄 パス・トラバーサル防止の改善
- 🔄 ファイル権限検証
- 🔄 環境変数インジェクション防止

### 📋 未実装（優先度順）

#### 1. 高優先度（Phase 1） - refactored モジュールの残りテスト

##### A. CLI・メインエントリーポイント

```markdown
- [x] `test_main.py` - CLIメインエントリーポイント（29テスト完了）✅
```

##### B. コア機能テスト

```markdown
- [x] `test_pinyin_glyph.py` - 拼音グリフ生成（30テスト完了）✅
- [ ] `test_gsub_table_generator.py` - GSUBテーブル生成（コア機能）
- [ ] `test_make_template_jsons.py` - テンプレートJSON生成（重要前処理）
- [ ] `test_retrieve_latin_alphabet.py` - ラテン文字抽出（重要前処理）
```

##### C. 拼音処理テスト

```markdown
- [ ] `test_hanzi_pinyin.py` - 漢字拼音処理（コア機能）
- [ ] `test_pinyin_conversion.py` - 拼音変換（コア機能）
- [ ] `test_pinyin_utils.py` - 拼音ユーティリティ
```

##### D. セキュリティ重要テスト

```markdown
- [ ] `test_shell_utils.py` - シェル実行セキュリティ（拡張）
```

##### B. エラーハンドリングテスト

```python
# 実装予定テスト例
def test_missing_font_file_handling():
    """フォントファイル不存在時の処理"""
    with pytest.raises(FileNotFoundError):
        FontBuilder(font_type=FontType.HAN_SERIF,
                   template_main_path="nonexistent.json")

def test_corrupted_json_handling():
    """破損JSONファイルの処理"""
    with pytest.raises(json.JSONDecodeError):
        load_template_json("corrupted.json")
```

#### 2. 中優先度（Phase 2） - 残りのrefactoredモジュール

##### A. フォント処理拡張テスト

```markdown
- [ ] `test_font_assembler.py` - フォント組み立て
- [ ] `test_glyph_manager.py` - グリフ管理
```

##### B. 処理系テスト

```markdown
- [ ] `test_optimized_utility.py` - 最適化ユーティリティ
- [ ] `test_parallel_processor.py` - 並列処理
- [ ] `test_cache_manager.py` - キャッシュ管理
- [ ] `test_benchmark.py` - ベンチマーク機能
```

##### C. 設定テスト拡張

```markdown
- [ ] `test_paths.py` - パス設定
- [ ] `test_name_table.py` - 名前テーブル
- [ ] `test_font_name_tables.py` - フォント名前テーブル
```

##### D. ユーティリティテスト拡張

```markdown
- [ ] `test_character_utils.py` - 文字ユーティリティ
- [ ] `test_dict_utils.py` - 辞書ユーティリティ
```

#### 3. 低優先度（Phase 3）

##### A. 外部ツール統合テスト

```python
# 実装予定テスト例
@pytest.mark.requires_external_tools
def test_otfcc_integration():
    """otfccツールとの統合テスト"""
    # 実際のotfccコマンドを使用したテスト

@pytest.mark.requires_external_tools
def test_jq_integration():
    """jqツールとの統合テスト"""
    # 実際のjqコマンドを使用したテスト
```

##### B. 国際化・文字エンコーディングテスト

```python
# 実装予定テスト例
def test_unicode_handling():
    """Unicode文字処理テスト"""
    # 簡体字、繁体字、日本語漢字の処理検証

def test_emoji_handling():
    """絵文字処理テスト"""
    # 絵文字を含むテキストの処理検証
```

## テストファイル構成

```shell
tests/
├── __init__.py
├── conftest.py                      # 共通フィクスチャ
├── pytest.ini                      # pytest設定
├── unit/                            # 単体テスト
│   ├── config/
│   │   ├── test_font_config.py      ✅ (19テスト)
│   │   ├── test_constants.py        ✅ (15テスト)
│   │   ├── test_paths.py            📋
│   │   ├── test_name_table.py       📋
│   │   └── test_font_name_tables.py 📋
│   ├── data/
│   │   ├── test_pinyin_data.py      ✅ (21テスト)
│   │   ├── test_character_data.py   ✅ (26テスト)
│   │   └── test_mapping_data.py     ✅ (30テスト)
│   ├── font/
│   │   ├── test_font_builder.py     ✅ (16テスト)
│   │   ├── test_font_assembler.py   📋
│   │   └── test_glyph_manager.py    📋
│   ├── glyph/
│   │   └── test_pinyin_glyph.py     ✅ (30テスト)
│   ├── processing/
│   │   ├── test_gsub_table_generator.py 📋 (HIGH)
│   │   ├── test_optimized_utility.py   📋
│   │   ├── test_parallel_processor.py  📋
│   │   ├── test_cache_manager.py       📋
│   │   └── test_benchmark.py           📋
│   ├── utils/
│   │   ├── test_cmap_utils.py       ✅ (34テスト)
│   │   ├── test_hanzi_pinyin.py     📋 (HIGH)
│   │   ├── test_pinyin_conversion.py 📋 (HIGH)
│   │   ├── test_pinyin_utils.py     📋 (HIGH)
│   │   ├── test_shell_utils.py      📋 (HIGH)
│   │   ├── test_character_utils.py  📋
│   │   └── test_dict_utils.py       📋
│   └── cli/
│       └── test_main.py             ✅ (29テスト)
├── integration/
│   ├── test_complete_pipeline.py    🔄
│   ├── test_font_generation.py      📋
│   └── test_data_flow.py            📋
├── security/
│   ├── test_shell_security.py       🔄
│   ├── test_path_validation.py      🔄
│   └── test_input_validation.py     📋
├── performance/
│   ├── test_font_generation_perf.py 📋
│   ├── test_memory_usage.py         📋
│   └── test_cpu_usage.py            📋
└── characterization/
    ├── test_legacy_behavior.py      ✅
    ├── test_current_behavior.py     📋
    └── test_output_compatibility.py 📋
```

## 品質基準

### 1. カバレッジ要件

- **単体テスト**: 95%以上
- **セキュリティ関連**: 100%
- **統合テスト**: 主要パイプライン80%以上
- **全体**: 90%以上

### 2. テスト実行時間

- **単体テスト**: 5秒以内
- **統合テスト**: 30秒以内
- **完全テストスイート**: 2分以内

### 3. 信頼性要件

- **フラッキーテスト**: 0%
- **テスト成功率**: 99%以上
- **CI/CD統合**: 完全自動化

## 実行コマンド

### 基本テスト実行

```bash
# 全テスト実行
python -m pytest tests/ -v

# カテゴリ別実行
python -m pytest tests/unit/ -v           # 単体テスト
python -m pytest tests/integration/ -v    # 結合テスト
python -m pytest tests/security/ -v       # セキュリティテスト

# カバレッジ付き実行
python -m pytest tests/ --cov=src --cov-report=html
```

### 特定用途実行

```bash
# 高速テスト（単体テストのみ）
python -m pytest tests/unit/ -x --tb=short

# セキュリティテストのみ
python -m pytest -m security -v

# パフォーマンステストのみ
python -m pytest -m benchmark --benchmark-only

# 外部ツール必要なテストを除外
python -m pytest -m "not requires_external_tools"
```

## CI/CD統合

### GitHub Actions設定例

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        python -m pytest tests/unit/ tests/security/ -v --cov=src
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## 次のステップ

### 即座に実装すべきテスト（高優先度Phase 1）

1. ✅ **CLIメインテスト**（`test_main.py`） - 最重要エントリーポイント（完了）
2. **コア機能テスト**：
   - ✅ `test_pinyin_glyph.py` - 拼音グリフ生成（完了）
   - [ ] `test_gsub_table_generator.py` - GSUBテーブル生成
3. **前処理スクリプトテスト**：
   - [ ] `test_make_template_jsons.py` - テンプレートJSON生成
   - [ ] `test_retrieve_latin_alphabet.py` - ラテン文字抽出
4. **拼音処理テスト**：
   - [ ] `test_hanzi_pinyin.py` - 漢字拼音処理
   - [ ] `test_pinyin_conversion.py` - 拼音変換
5. **セキュリティテスト**（`test_shell_utils.py`） - シェル実行セキュリティ

### 継続的改善項目

1. **テストカバレッジ向上**
2. **CI/CD統合強化**
3. **パフォーマンス回帰防止**
4. **セキュリティテスト拡張**

## 成功基準

### 短期目標（1-2週間）

- [x] 基本単体テストカバレッジ達成（220/220テスト通過）
- [x] CLI・コア機能テスト部分完了（Phase 1高優先度の40%完了）
- [ ] refactoredモジュール主要テスト90%完了

### 中期目標（1ヶ月）

- [ ] 全refactoredモジュールテスト完了（Phase 2中優先度）
- [ ] 結合テスト完了
- [ ] セキュリティテスト100%完了

### 長期目標（2-3ヶ月）

- [ ] パフォーマンステスト実装
- [ ] 完全自動化テストパイプライン
- [ ] 全体テストカバレッジ95%達成

---

*このテスト計画は、萌神拼音フォントプロジェクトの品質保証と継続的改善を目的として作成されました。TDD原則に基づき、セキュリティ強化と保守性向上を重視しています。*
