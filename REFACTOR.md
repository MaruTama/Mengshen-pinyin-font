  # CLAUDE.md - 萌神拼音フォント リファクタリング方針

このプロジェクトは段階的なリファクタリングを実行中です。以下の方針に従って作業を進めてください。

## プロジェクト概要
- **名前**: 萌神(Mengshen)拼音フォント
- **目的**: 多音字対応の中国語拼音フォント生成ツール
- **現在のバージョン**: 1.03
- **ターゲット言語**: Python 3.11+
- **主要機能**: 簡体字・繁体字への拼音自動付与、OpenType機能による文脈置換

## 現在の状態 (2024年12月29日)
- **Python**: 3.8.2 → 3.11+への移行が必要
- **コード行数**: 3,511行 (25ファイル)
- **重要課題**: セキュリティ脆弱性、アーキテクチャ負債、型安全性の欠如

## リファクタリング戦略 (5段階)

### Phase 1: セキュリティ緊急修正 🔴 最優先
**期間**: 1-2週間
**状態**: 未着手

**TDD実装ステップ**:
1. **🔴 Red: セキュリティテスト作成**
   ```python
   # tests/security/test_shell_injection.py
   def test_no_shell_true_usage():
       """shell=Trueが使用されていないことを確認"""
       vulnerable_files = find_shell_true_usage()
       assert len(vulnerable_files) == 0
   
   def test_command_injection_prevention():
       """コマンドインジェクション攻撃の防止"""
       malicious_input = "test; rm -rf /"
       with pytest.raises(SecurityError):
           execute_external_tool(malicious_input)
   
   def test_path_traversal_prevention():
       """パストラバーサル攻撃の防止"""
       malicious_path = "../../../etc/passwd"  
       with pytest.raises(SecurityError):
           process_file_path(malicious_path)
   ```

2. **🟢 Green: 最小限の安全な実装**
   ```python
   # src/secure_shell.py (新規)
   import shlex
   import subprocess
   from pathlib import Path
   
   def safe_command_execution(cmd: list[str]) -> subprocess.CompletedProcess:
       """安全なコマンド実行"""
       if isinstance(cmd, str):
           raise SecurityError("String commands not allowed")
       return subprocess.run(cmd, capture_output=True, text=True)
   ```

3. **🔵 Refactor: 既存コードの置き換え**

**修正対象**:
- `src/shell.py:8` - `subprocess.run(cmd, shell=True)` の脆弱性
- `tools/shell.py` - 同様の脆弱性
- ハードコードされた絶対パス (`tools/hoge.py`, `tools/diff_output.py`)

**TDD完了条件**:
- [ ] 🔴 全セキュリティテストが作成済み
- [ ] 🟢 全テストが成功
- [ ] 🔵 レガシーコードの完全置き換え
- [ ] カバレッジ100% (セキュリティ関連コード)
- [ ] 静的解析ツール(bandit)でのクリーンスコア

### Phase 2: Python環境モダン化 🟡 高優先
**期間**: 1週間
**状態**: 未着手

**TDD実装ステップ**:
1. **🔴 Red: モダン化テスト作成**
   ```python
   # tests/modernization/test_python_features.py
   def test_all_functions_have_type_hints():
       """全関数に型ヒントがあることを確認"""
       untyped_functions = find_functions_without_type_hints("src/")
       assert len(untyped_functions) == 0
   
   def test_uses_pathlib_not_os_path():
       """os.pathではなくpathlibを使用していることを確認"""
       os_path_usage = find_os_path_usage("src/")
       assert len(os_path_usage) == 0
   
   def test_modern_import_syntax():
       """from __future__ import annotationsの使用確認"""
       files_without_future_imports = check_future_imports("src/")
       assert len(files_without_future_imports) == 0
   ```

2. **🟢 Green: Python 3.11+機能の段階的実装**
3. **🔵 Refactor: レガシーコードの置き換え**

**作業内容**:
- Python 3.11+への移行
- `pyproject.toml`の作成  
- 依存関係の更新とバージョン固定
- `.gitignore`の追加

**TDD対象の新機能**:
- 型ヒント: `from __future__ import annotations`
- パターンマッチング: `match-case` 
- より効率的なジェネリクス
- `pathlib.Path`による安全なファイル操作

**TDD完了条件**:
- [ ] 🔴 全モダン化テストが作成済み
- [ ] 🟢 Python 3.11+でのテスト成功
- [ ] 🔵 レガシー構文の完全置き換え
- [ ] mypy型チェック100%通過

### Phase 3: データ構造モダン化 🟡 高優先
**期間**: 1-2週間
**状態**: 未着手

**目標**:
- 型安全性の向上 (`TypedDict`, `dataclass`)
- イテレータによるメモリ効率化
- 遅延評価の導入

**重要原則**:
- 全ての関数に型ヒントを追加
- `Iterator`と`Generator`を活用してメモリ使用量を削減
- データクラスで構造化

### Phase 4: アーキテクチャリファクタリング 🟢 中優先
**期間**: 2-3週間
**状態**: 未着手

**新パッケージ構造**:
```
mengshen_font/
├── config/      # 設定管理
├── data/        # データ処理
├── processing/  # 拼音・グリフ処理
├── font/        # フォント生成
├── external/    # 外部ツール連携
└── cli/         # コマンドライン
```

**設計原則**:
- 依存性注入パターン
- Protocol-based interfaces
- 単一責任の原則

### Phase 5: パフォーマンス最適化 🟢 中優先
**期間**: 1-2週間
**状態**: 未着手

**最適化領域**:
- `@lru_cache`による頻用データのキャッシュ
- 非同期処理による並列化
- バッチ処理とストリーミング

### Phase 6: 拼音データ統合 (Git Submodules) 🟡 高優先
**期間**: 1週間  
**状態**: 🔄 実装中（ハイブリッドアプローチ採用）

**TDD実装ステップ**:
1. **🔴 Red: データ整合性テスト作成**
   ```python
   # tests/integration/test_pinyin_data_migration.py
   def test_pinyin_data_consistency():
       """旧データと新データの整合性確認"""
       old_data = load_current_pinyin_data()
       new_data = load_submodule_pinyin_data()
       
       # 主要文字の拼音が一致することを確認
       for char in COMMON_CHARACTERS:
           old_pinyin = old_data.get_pinyin(char)
           new_pinyin = new_data.get_pinyin(char)
           assert pinyin_sets_equivalent(old_pinyin, new_pinyin)
   
   def test_offline_functionality():
       """完全オフラインでの動作確認"""
       with mock_offline_environment():
           font_result = generate_font_with_pinyin()
           assert font_result.success
           assert font_result.quality_score >= BASELINE_SCORE
   
   def test_no_web_requests():
       """Web リクエストが発生しないことを確認"""
       with mock_network_block():
           # 全機能がオフラインで動作することを確認
           result = full_font_generation_pipeline()
           assert result.success
   ```

2. **🟢 Green: 段階的データソース移行**
3. **🔵 Refactor: Web依存コードの完全排除**

**目標**:
- 外部拼音データソースの統一
- Webスクラピング依存の排除
- データ品質とメンテナンス性の向上
- オフライン実行環境の実現

**TDD完了条件**:
- [ ] 🔴 データ整合性テスト100%作成
- [ ] 🟢 オフライン環境テスト成功
- [ ] 🔵 Web依存コード0%
- [ ] フォント品質回帰テスト通過

**現在の問題**:
- **セキュリティリスク**: Webスクラピング（baidu.com、zdic.net）
- **信頼性問題**: 外部サービス依存によるビルド失敗リスク
- **データ品質**: 複数ソースの不整合
- **メンテナンス**: 手動データ更新の負担

**統合計画**:

**1. Git Submodules設定**:
```bash
# pinyin-dataリポジトリをサブモジュールとして追加
git submodule add https://github.com/mozillazg/pinyin-data.git res/phonics/pinyin-data
git submodule update --init --recursive
```

**2. データソース移行マッピング**:
```
現在のファイル → pinyin-data移行先
─────────────────────────────────────
TGSCC-mapping-table.txt → pinyin-data/kTGHZ2013.txt
BIG5-mapping-table.txt → pinyin-data/pinyin.txt  
pypinyin Web API → pinyin-data/kMandarin.txt
Webスクラピング → pinyin-data/zdic.txt
```

**3. シンプルなオフラインデータ処理** ✅ 実装済み:
```python
# 実装済み: 処理済みデータの直接読み込み
def get_pinyin_table_with_mapping_table():
    # merged-mapping-table.txt を直接読み込み (16,028文字)
    # このファイルは make_unicode_pinyin_map_table.py で生成済み
    # overwrite.txt による手動オーバーライドも適用済み
    # Webスクラピング完全排除、セキュリティリスク解決
```

**4. 実装スケジュール**:

**実装完了状況:**
- [x] Git submodule追加とデータファイル分析 ✅
- [x] pinyin-dataパーサーの実装 ✅ (`src/offline_pinyin_loader.py`)
- [x] シンプルなオフライン実装 ✅ (`src/pinyin_getter.py`)
- [x] 綴り修正完了 ✅ (`marged` → `merged`)

**具体的ファイル変更**:
```python
# src/pinyin_getter.py - 大幅リファクタ
class PinyinDataLoader:
    def __init__(self, submodule_path="res/phonics/pinyin-data"):
        self.data_path = Path(submodule_path)
        self.pinyin_mapping = self._load_pinyin_txt()
        self.manual_overrides = self._load_overrides()
    
    def _load_pinyin_txt(self) -> Dict[str, List[str]]:
        """pinyin-data/pinyin.txt をパース"""
        with open(self.data_path / "pinyin.txt", 'r', encoding='utf-8') as f:
            # U+4E2D: zhōng,zhòng  # 中 形式をパース
            
    def get_pinyin(self, char: str) -> List[str]:
        """Webスクラピングを完全排除"""
```

**5. Docker設定更新**:
```dockerfile
# Dockerfile - submodule対応
COPY .gitmodules .gitmodules
COPY .git .git
RUN git submodule update --init --recursive
# または build contextで事前にsubmodule更新
```

**6. CI/CD更新**:
```yaml
# .github/workflows/build.yml
- name: Checkout with submodules
  uses: actions/checkout@v3
  with:
    submodules: recursive
```

**完了条件**:
- [x] Git submodule統合完了 ✅
- [x] シンプルオフライン実装完了 ✅  
- [x] 既存フォント出力との互換性確認 ✅（16,028文字正常読み込み）
- [x] オフライン環境でのビルド成功 ✅
- [x] 綴り修正完了 ✅ (`marged` → `merged`)
- [x] ドキュメント更新（データソース説明）✅

**実装したシンプルオフラインアプローチのメリット**:
- **セキュリティ**: Webスクラピング完全排除、外部接続不要
- **安定性**: 外部サービス依存完全解消、100%オフライン実行
- **シンプル性**: 処理済みデータ（16,028文字）の直接読み込み
- **保守性**: `make_unicode_pinyin_map_table.py` でデータ前処理済み
- **互換性**: 既存の`overwrite.txt`オーバーライド機能を完全保持
- **効率性**: 不要な複雑性を排除、高速で信頼性の高い実装

**互換性保証**:
- 既存の`overwrite.txt`手動オーバーライド機能は維持
- 多音字（homograph）処理は現在のロジックを保持
- 出力フォーマットは完全互換

### Phase 7: Docker コンテナ化 🟢 中優先
**期間**: 1週間
**状態**: 未着手

**目標**:
- 開発環境の標準化
- 外部依存関係の管理
- CI/CDパイプラインの構築
- 本番環境でのデプロイメント簡易化

**実装内容**:

**1. Multi-stage Dockerfile**:
```dockerfile
# Build stage
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y \
    build-essential \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install otfcc
RUN wget https://github.com/caryll/otfcc/releases/download/v0.10.4/otfcc-linux64-0.10.4.tar.gz \
    && tar -xzf otfcc-linux64-0.10.4.tar.gz \
    && mv otfcc-linux64/bin/* /usr/local/bin/

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/bin/otfcc* /usr/local/bin/
COPY --from=builder /usr/bin/jq /usr/bin/jq
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

WORKDIR /app
# Copy source with submodules
COPY . .
# Initialize submodules if needed
RUN if [ -f .gitmodules ]; then git submodule update --init --recursive; fi

ENTRYPOINT ["python3", "src/main.py"]
```

**2. Docker Compose 設定**:
```yaml
version: '3.8'
services:
  mengshen-font:
    build: .
    volumes:
      - ./res:/app/res:ro
      - ./outputs:/app/outputs
      - ./tmp:/app/tmp
    environment:
      - PYTHONUNBUFFERED=1
    profiles:
      - production
  
  mengshen-dev:
    build:
      context: .
      target: builder
    volumes:
      - .:/app
      - font-cache:/app/.cache
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    working_dir: /app
    command: bash
    profiles:
      - development

  test:
    extends: mengshen-dev
    command: python -m pytest tests/
    profiles:
      - test

volumes:
  font-cache:
```

**3. 開発環境スクリプト**:
```bash
# scripts/dev.sh
#!/bin/bash
docker-compose --profile development up -d mengshen-dev
docker-compose exec mengshen-dev bash

# scripts/build-font.sh  
#!/bin/bash
docker-compose --profile production run --rm mengshen-font "$@"

# scripts/test.sh
#!/bin/bash
docker-compose --profile test run --rm test
```

**4. CI/CD対応**:
- GitHub Actions での自動テスト
- Docker Hub への自動デプロイ
- セキュリティスキャン統合

**完了条件**:
- [ ] Multi-stage Dockerfileの実装
- [ ] docker-compose.ymlの作成
- [ ] 開発・本番・テスト環境の分離
- [ ] 外部依存関係の完全コンテナ化
- [ ] ドキュメント更新（README.md）
- [ ] CI/CDパイプラインの構築

**メリット**:
- **環境統一**: ローカル・本番環境の差異解消
- **依存関係管理**: otfcc、jqの自動インストール
- **セキュリティ**: コンテナによる分離実行
- **スケーラビリティ**: 複数フォント並列生成
- **デバッグ**: 再現可能な開発環境

## 開発ガイドライン

### コーディング規約
    - **型ヒント**: 全ての関数・メソッドに必須
    - **命名**: 英語統一、snake_case
    - **コメント**: 英語で記述
    - **docstring**: Google形式
    
    ### セキュリティ原則
    - **外部コマンド実行**: `shell=True`は絶対禁止
    - **ファイルパス**: `pathlib.Path`を使用
    - **入力検証**: 全ての外部入力を検証
    - **エラーハンドリング**: システム情報を漏洩させない
    
    ### パフォーマンス原則
    - **メモリ効率**: `Iterator`を優先
    - **キャッシュ**: 重い処理には`@lru_cache`
    - **並列処理**: I/Oバウンドな処理は`asyncio`
    - **遅延評価**: 大容量データは必要時のみ処理
    
    ## ファイル構造ルール
    
    ### 作業対象外
    - `outputs/` - 生成されたフォントファイル
    - `tmp/` - 一時ファイル
    - `tools/SVGCleaner.app/` - 外部アプリケーション
    - `*.pyc` - コンパイル済みPythonファイル
    
    ### 重要ファイル
    - `src/main.py` - エントリーポイント
    - `src/font.py` - メインフォント処理クラス
    - `src/shell.py` - **セキュリティ修正最優先**
    - `src/config.py` - 設定定義
    
    ### データファイル
    - `res/phonics/unicode_mapping_table/` - Unicode-拼音マッピング
    - `res/phonics/duo_yin_zi/` - 多音字データ
    - `requirements.txt` - 依存関係
    
    ## テスト戦略 (TDD原則)

### TDD実装方針
全リファクタリングフェーズでTest-Driven Development (TDD) を採用。
**Red → Green → Refactor** サイクルを厳守する。

**完全パイプライン統合**: 辞書生成 + フォント生成の全工程をTDDサイクルに含める。

### TDD実装サイクル
```
1. 🔴 Red: テストを書く（失敗させる）
2. 🟢 Green: 最小限の実装でテストを通す  
3. 🔵 Refactor: コードを改善する
4. 🧪 Pipeline: 完全パイプライン検証
5. 繰り返し
```

### 完全パイプラインTDD統合
各リファクタリングフェーズで以下の完全検証サイクルを実行：

**Pipeline TDD Cycle**:
```bash
# 1. 🔴 Red: 新機能/変更に対するテスト作成
pytest tests/unit/test_new_feature.py  # 失敗を確認

# 2. 🟢 Green: 最小実装でテスト通過
# コード変更...
pytest tests/unit/test_new_feature.py  # 成功を確認

# 3. 🔵 Refactor: コード品質向上
# リファクタリング...
pytest tests/unit/ tests/security/  # 全単体・セキュリティテスト

# 4. 🧪 Pipeline: 完全パイプライン検証
cd res/phonics/duo_yin_zi/scripts/
python make_pattern_table.py  # 辞書生成テスト

cd ../../unicode_mapping_table/
python make_unicode_pinyin_map_table.py  # マッピング生成テスト

cd ../../../..
python src/main.py -t han_serif  # フォント生成テスト
python src/main.py -t handwritten  # 両スタイル検証

# 5. 🎯 Integration: 統合テスト実行
pytest tests/integration/ -v  # 完全統合テスト
```

### フェーズ別TDDアプローチ

**Phase 1 (セキュリティ修正)** - ✅ 完了:
```python
# ✅ 1. セキュリティテストを先に書く (Red)
def test_shell_injection_prevention():
    # shell=Trueが使用されていないことを確認
    assert not has_shell_true_usage("src/shell.py")
    
def test_input_validation():
    # 不正入力の適切な処理を確認
    with pytest.raises(ValidationError):
        unsafe_command_execution("rm -rf /")

# ✅ 2. 実装でテストを通す (Green)
# ✅ 3. セキュリティを保ちつつリファクタ (Refactor)
# ✅ 4. 完全パイプライン検証 (Pipeline)
#      - 辞書生成: 1.03秒で成功
#      - マッピング生成: 2.31秒で成功  
#      - フォント生成: 86.95秒で成功
```

**Phase 2 (Python環境モダン化)** - 🔄 次期実装:
```python
# 🔴 1. Python 3.11+機能のテスト (Red)
def test_type_hints_validation():
    # 全関数に型ヒントがあることを確認
    assert all_functions_have_type_hints("src/")

def test_modern_python_features():
    # match-case, pathlib使用の確認
    assert uses_pathlib_not_os_path("src/")

# 🟢 2. 段階的モダン化実装 (Green)
# 🔵 3. レガシー構文置き換え (Refactor)  
# 🧪 4. 完全パイプライン検証 (Pipeline)
#      - 辞書生成が Python 3.11+ で動作確認
#      - フォント生成が型安全性保持で動作確認
```

**Phase 6 (拼音データ統合)** - 📋 計画中:
```python
# 🔴 1. データ整合性テストを先に書く (Red)
def test_pinyin_data_consistency():
    # mozillazg/pinyin-dataとの互換性確認
    old_data = load_current_pinyin_data()
    new_data = load_submodule_pinyin_data()
    assert pinyin_mappings_equivalent(old_data, new_data)

def test_offline_functionality():
    # オフライン環境での動作確認
    with mock_offline_environment():
        result = generate_font_with_pinyin()
        assert result.success

# 🟢 2. サブモジュール統合実装 (Green)
# 🔵 3. Web依存排除 (Refactor)
# 🧪 4. 完全パイプライン検証 (Pipeline)
#      - 辞書生成がオフライン環境で動作確認
#      - フォント生成品質が維持されることを確認
```

### テスト構造とツール

**テストディレクトリ構造** (パイプライン統合):
```
tests/
├── unit/                    # 単体テスト
│   ├── test_pinyin_getter.py
│   ├── test_font_processing.py
│   └── test_security.py
├── integration/             # 統合テスト (パイプライン含む)
│   ├── test_font_generation.py      # フォント生成テスト
│   ├── test_dictionary_generation.py # 辞書生成テスト  
│   ├── test_complete_pipeline.py    # 完全パイプラインテスト
│   └── test_pipeline_security.py   # パイプラインセキュリティ
├── performance/             # パフォーマンステスト
│   ├── test_benchmarks.py          # 個別性能テスト
│   └── test_pipeline_performance.py # パイプライン性能テスト
├── security/                # セキュリティテスト
│   └── test_shell_injection.py    # shell=True脆弱性テスト
└── fixtures/                # テストデータ
    ├── sample_fonts/              # サンプルフォント
    ├── sample_dictionaries/       # サンプル辞書データ
    └── expected_outputs/          # 期待される出力結果
```

**テストツールスタック**:
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addoptions = 
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

**必須依存関係**:
```txt
# requirements-dev.txt
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0  
pytest-benchmark>=4.0.0
hypothesis>=6.0.0           # Property-based testing
black>=22.0.0              # Code formatting
mypy>=1.0.0                # Type checking  
bandit>=1.7.0              # Security linting
```

### フェーズ別TDD実装計画

**完全パイプライン統合TDDワークフロー** (各フェーズで適用):

1. **既存パイプライン特性化テスト作成**
   ```python
   def test_current_pipeline_output_unchanged():
       # 辞書 → フォント完全パイプラインの現在出力を固定
       dict_output = generate_current_dictionaries()
       font_output = generate_current_font()
       assert dict_output == EXPECTED_DICT_BASELINE
       assert font_output == EXPECTED_FONT_BASELINE
   ```

2. **段階的TDDサイクル実行**
   ```python
   # 🔴 Red: 新機能テスト（失敗）
   def test_new_feature_pinyin_logic():
       assert extract_improved_pinyin("中") == ["zhōng", "zhòng"]
   
   # 🟢 Green: 最小実装
   # 🔵 Refactor: 品質向上
   
   # 🧪 Pipeline: 完全検証
   def test_pipeline_integration():
       # 1. 辞書生成テスト
       assert generate_duo_yin_zi_patterns()
       assert generate_unicode_mapping()
       
       # 2. フォント生成テスト  
       assert generate_han_serif_font()
       assert generate_handwritten_font()
       
       # 3. 品質保証テスト
       assert verify_font_quality()
       assert verify_no_regression()
   ```

3. **回帰防止とパフォーマンス監視**
   ```python
   def test_pipeline_no_regression():
       # パイプライン全体の品質が劣化していないことを確認
       old_performance = BASELINE_PERFORMANCE
       new_performance = measure_pipeline_performance()
       
       assert new_performance.dict_generation_time < old_performance.dict_time * 1.2
       assert new_performance.font_generation_time < old_performance.font_time * 1.2
       assert new_performance.output_quality >= old_performance.quality
   ```

4. **セキュリティ継続検証**
   ```python
   def test_pipeline_security_maintained():
       # パイプライン全体でセキュリティが保たれていることを確認
       assert no_shell_true_in_pipeline()
       assert no_command_injection_vectors()
       assert secure_file_operations_only()
   ```

### 継続的テスト実行

**開発時自動テスト**:
```bash
# scripts/watch-tests.sh
#!/bin/bash
pytest-watch --clear --onpass="echo '✅ Tests passed'" \
              --onfail="echo '❌ Tests failed'"
```

**Git Hooks統合**:
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running tests before commit..."
python -m pytest tests/ --quiet
if [ $? -ne 0 ]; then
  echo "❌ Tests failed. Commit aborted."
  exit 1
fi
```

### テスト品質基準

**カバレッジ要件**:
- **Unit tests**: 95%以上
- **Integration tests**: 主要パイプライン100%
- **Security tests**: セキュリティ関連コード100%

**テスト実行時間制限**:
- Unit tests: < 30秒
- Integration tests: < 2分
- Full test suite: < 5分

**テスト品質チェック**:
```python
# tests/test_quality.py
def test_all_tests_have_docstrings():
    """全テスト関数にdocstringがあることを確認"""
    
def test_no_skipped_tests_in_ci():
    """CI環境でskipされるテストがないことを確認"""
    
def test_test_isolation():
    """テスト間の独立性を確認"""
```

### CI/CD統合

**GitHub Actions TDD Workflow**:
```yaml
# .github/workflows/tdd.yml
name: TDD Workflow
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: recursive
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run TDD cycle
        run: |
          # Security tests first
          python -m pytest tests/security/ -v
          # Unit tests
          python -m pytest tests/unit/ --cov=src
          # Integration tests  
          python -m pytest tests/integration/
          # Performance benchmarks
          python -m pytest tests/performance/ --benchmark-only
```

### TDD成功基準

各フェーズ完了の必須条件:
- [ ] 全テストが成功 (Green)
- [ ] カバレッジ基準達成 (95%+)
- [ ] セキュリティテスト100%通過
- [ ] パフォーマンス回帰なし
- [ ] 既存機能の完全後方互換性
    
    ## 進捗管理
    リファクタリングの進捗は本ファイルの各Phaseのチェックボックスで管理。
    完了したPhaseには✅マークを付けること。

    **Phase実行順序（推奨）**:
    1. **Phase 1**: セキュリティ修正（緊急）
    2. **Phase 2**: Python環境モダン化 
    3. **Phase 6**: 拼音データ統合（Git Submodules）
    4. **Phase 7**: Docker化（環境標準化）
    5. **Phase 3**: データ構造モダン化
    6. **Phase 4**: アーキテクチャリファクタリング
    7. **Phase 5**: パフォーマンス最適化

    **拼音データ統合の早期実装理由**:
    - セキュリティ脆弱性（Webスクラピング）の排除
    - 外部サービス依存の解消
    - 安定したオフライン実行環境の確立
    - 後続フェーズでの一貫したデータソース使用
    
    ## 注意事項
    
    ### 既存機能の保持
    - フォント生成機能は一切変更しない
    - 出力ファイル形式は維持
    - CLI インターフェースの互換性を保つ
    
    ### 段階的移行
    - 各Phaseは独立して動作確認
    - 後戻り可能な形で実装
    - 既存テストケースでの検証
    
    ### 品質管理
    - 各Phase完了時にコードレビュー
    - セキュリティスキャンの実行
    - パフォーマンステストの実施