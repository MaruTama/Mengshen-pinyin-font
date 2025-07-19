# Docker環境での萌神フォント生成 (Linux x64)

このドキュメントでは、Docker Composeを使用してリファクタ版でフォント生成を実行する方法を説明します。

**重要**: このDocker環境はLinux x64プラットフォーム専用です。otfccの安定したビルドを確保するため、`--platform=linux/amd64`を指定しています。

## 前提条件

- Docker Engine 20.10以上
- Docker Compose 2.0以上  
- x64プロセッサ（Intel/AMD）または Docker Desktopでのx64エミュレーション
- 十分なディスク容量（ビルド時に約3GB）
- インターネット接続（初回ビルド時に必要）

## 初回セットアップ

### 1. イメージのビルド

初回実行前に、otfccをソースからビルドするためイメージの構築が必要です：

```bash
# イメージをビルド（5-10分程度かかります）
docker-compose build

# ビルドキャッシュを使わずに再ビルド
docker-compose build --no-cache
```

### 2. otfccインストールの確認

```bash
# otfccが正しくインストールされているか確認
docker-compose run --rm mengshen-font otfccdump --version
docker-compose run --rm mengshen-font otfccbuild --version
```

## 基本的な使用方法

### 1. 完全パイプライン実行

全ての辞書生成からフォント生成までを一括で実行：

```bash
docker-compose up pipeline
```

### 2. 個別フォント生成

#### han_serifフォントのみ生成
```bash
docker-compose up han-serif
```

#### handwrittenフォントのみ生成
```bash
docker-compose up handwritten
```

### 3. 開発環境

インタラクティブな開発環境でコンテナに入る：

```bash
docker-compose up -d dev
docker-compose exec dev bash
```

コンテナ内で個別にコマンド実行：
```bash
# テスト実行
python -m pytest tests/ -v

# 個別フォント生成
python -m refactored.cli.main -t han_serif

# デバッグモードでの実行
python -m refactored.cli.main -t handwritten --debug
```

## ファイル構成

### ボリュームマウント

- `./src` → `/app/src` (ソースコード)
- `./res` → `/app/res` (リソースファイル、読み取り専用)
- `./outputs` → `/app/outputs` (生成されたフォント出力)
- `./tmp` → `/app/tmp` (一時ファイル)

### 生成されるファイル

パイプライン実行後、以下のファイルが`./outputs/`に生成されます：

- `Mengshen-HanSerif.ttf` - 明朝体スタイル
- `Mengshen-Handwritten.ttf` - 手書き体スタイル
- `merged-mapping-table.txt` - 統合マッピングテーブル

## サービス構成

### mengshen-font (基本サービス)
- ベースとなるサービス定義
- Python 3.11 + 必要な依存関係

### han-serif
- han_serifフォント生成専用
- 実行: `python -m refactored.cli.main -t han_serif`

### handwritten
- handwrittenフォント生成専用
- 実行: `python -m refactored.cli.main -t handwritten`

### pipeline
- 完全パイプライン実行
- 辞書生成 → フォント生成の全工程

### dev
- 開発・デバッグ用インタラクティブ環境
- ソースコードの変更がリアルタイムで反映

## トラブルシューティング

### ログの確認
```bash
docker-compose logs pipeline
docker-compose logs han-serif
```

### コンテナの状態確認
```bash
docker-compose ps
```

### クリーンアップ
```bash
# 停止と削除
docker-compose down

# ボリュームも含めて削除
docker-compose down -v

# イメージの再ビルド
docker-compose build --no-cache
```

### 権限エラーの解決

ホスト側でoutputsディレクトリの権限を確認：
```bash
# 権限の確認
ls -la outputs/

# 権限の修正（必要に応じて）
sudo chown -R $USER:$USER outputs/ tmp/
```

## パフォーマンス最適化

### リソース制限の設定

必要に応じて`docker-compose.yml`にリソース制限を追加：

```yaml
services:
  mengshen-font:
    # ... 他の設定 ...
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
```

### 並列実行

han_serifとhandwrittenを並列で生成：
```bash
docker-compose up han-serif handwritten
```

## 継続的インテグレーション

GitHub ActionsやJenkinsでの自動化例：

```yaml
# .github/workflows/font-generation.yml
name: Font Generation
on:
  push:
    branches: [main]

jobs:
  generate-fonts:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Generate fonts
      run: docker-compose up --abort-on-container-exit pipeline
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: generated-fonts
        path: outputs/*.ttf
```