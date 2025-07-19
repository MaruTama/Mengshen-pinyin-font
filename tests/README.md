# 全ユニットテストを実行
  python -m pytest tests/unit/ -v

  # 簡潔な出力で実行
  python -m pytest tests/unit/ -q

  # 警告なしで実行
  python -m pytest tests/unit/ --disable-warnings

  特定カテゴリのテスト実行

  # CLIテストのみ
  python -m pytest tests/unit/cli/ -v

  # コア機能テストのみ
  python -m pytest tests/unit/glyph/ tests/unit/processing/ -v

  # セキュリティテストのみ
  python -m pytest tests/unit/utils/test_shell_utils.py -v

  # データ管理テストのみ
  python -m pytest tests/unit/data/ -v

  📊 カバレッジ付きテスト

  基本カバレッジ

  # カバレッジレポート付きで実行
  python -m pytest tests/unit/ --cov=src --cov-report=term

  # 詳細なカバレッジレポート
  python -m pytest tests/unit/ --cov=src --cov-report=term-missing

  # HTMLカバレッジレポート生成
  python -m pytest tests/unit/ --cov=src --cov-report=html

  高品質カバレッジ

  # 95%以上のカバレッジを要求
  python -m pytest tests/unit/ --cov=src --cov-fail-under=95

  # 特定モジュールのカバレッジのみ
  python -m pytest tests/unit/ --cov=src/refactored/utils --cov-report=term-missing

  🎯 特定テストファイル実行

  個別ファイルテスト

  # 拼音処理テスト
  python -m pytest tests/unit/utils/test_hanzi_pinyin.py -v

  # GSUB生成テスト
  python -m pytest tests/unit/processing/test_gsub_table_generator.py -v

  # セキュリティテスト
  python -m pytest tests/unit/utils/test_shell_utils.py -v

  # フォント設定テスト
  python -m pytest tests/unit/config/test_font_config.py -v

  特定テスト関数実行

  # 特定のテストクラスのみ
  python -m pytest tests/unit/cli/test_main.py::TestFontGenerationCLI -v

  # 特定のテスト関数のみ
  python -m pytest tests/unit/utils/test_shell_utils.py::TestSecurityIntegration::test_comp
  rehensive_injection_prevention -v

  🔍 デバッグ用テスト

  詳細出力

  # 失敗時の詳細トレースバック
  python -m pytest tests/unit/ -v --tb=long

  # より詳細なデバッグ情報
  python -m pytest tests/unit/ -v -s --tb=long

  # 最初の失敗で停止
  python -m pytest tests/unit/ -v -x

  パフォーマンス分析

  # 最も遅いテストを表示
  python -m pytest tests/unit/ --durations=10

  # テスト時間を詳細表示
  python -m pytest tests/unit/ --durations=0

  🏷️ マーク別テスト実行

  TDD段階別

  # ユニットテストのみ（カスタムマーク）
  python -m pytest tests/unit/ -m unit

  # 統合テストのみ
  python -m pytest tests/integration/ -v

  # セキュリティテストのみ（カスタム検索）
  python -m pytest tests/unit/ -k "security or shell"

  📁 推奨テストワークフロー

  開発時の基本フロー

  # 1. 🔴 Red: 失敗するテストを作成後
  python -m pytest tests/unit/[新しいテストファイル] -v

  # 2. 🟢 Green: 実装後に全テスト確認
  python -m pytest tests/unit/ -q --disable-warnings

  # 3. 🔵 Refactor: リファクタリング後にカバレッジ確認
  python -m pytest tests/unit/ --cov=src --cov-report=term-missing

  本格的品質チェック

  # 完全品質チェック（推奨）
  python -m pytest tests/unit/ --cov=src --cov-report=term-missing --tb=short
  --disable-warnings

  # CI/CD用コマンド
  python -m pytest tests/unit/ --cov=src --cov-report=xml --junitxml=test-results.xml

  🔧 トラブルシューティング

  インポートエラー対処

  # PYTHONPATHを設定して実行
  PYTHONPATH=src python -m pytest tests/unit/ -v

  # 現在のディレクトリから実行
  cd /Users/tama/workspace/font/Mengshen-pinyin-font
  python -m pytest tests/unit/ -v

  キャッシュクリア

  # Pytestキャッシュをクリア
  python -m pytest --cache-clear tests/unit/

  # __pycache__を削除
  find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

  🎖️ 品質保証コマンド

  最高品質チェック

  # 厳格な品質チェック
  python -m pytest tests/unit/ \
    --cov=src \
    --cov-fail-under=90 \
    --cov-report=term-missing \
    --tb=short \
    --disable-warnings \
    --durations=10

  # セキュリティ重点チェック
  python -m pytest tests/unit/utils/test_shell_utils.py \
    --cov=src/refactored/utils/shell_utils.py \
    --cov-fail-under=80 \
    --cov-report=term-missing \
    -v

  💡 便利なエイリアス設定

  # ~/.bashrc または ~/.zshrc に追加
  alias test-all="python -m pytest tests/unit/ --disable-warnings"
  alias test-cov="python -m pytest tests/unit/ --cov=src --cov-report=term-missing 
  --disable-warnings"
  alias test-security="python -m pytest tests/unit/utils/test_shell_utils.py -v"
  alias test-core="python -m pytest tests/unit/glyph/ tests/unit/processing/ -v"
  alias test-quick="python -m pytest tests/unit/ -q --disable-warnings"
