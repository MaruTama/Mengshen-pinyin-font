---
name: font-studio
description: Mengshen Font Studio（webapp）を起動する。フォント選択→ライセンス確認→拼音位置調整→グリフ一覧→多音字/GSUB/IVS→読み編集→ビルドをブラウザで行うローカル Web アプリ。「アプリを起動」「webapp を起動」「Font Studio を開いて」と言われたら使う。$ARGUMENTS に "stop"（停止）、"dev"（Vite 開発モード）、"rebuild"（フロントエンド再ビルド後に起動）を渡せる。
---

# Mengshen Font Studio 起動

FastAPI + React のローカル Web アプリを <http://localhost:8000> で起動する。

## 手順

`$ARGUMENTS` に応じて分岐する。未指定なら「通常起動」。

### 通常起動（デフォルト）

1. **前提チェック**（不足があれば手順を案内して中断）

   ```bash
   python -m uvicorn --version || echo "uvicorn が見つからない"
   which otfccdump otfccbuild jq
   ls webapp/frontend/dist/index.html || echo "フロントエンド未ビルド"
   ```

   - uvicorn が見つからない場合: `python3.11 -m venv .venv && .venv/bin/pip install -e ".[webapp]"`
   - otfcc/jq がない場合: `brew tap caryll/tap && brew install otfcc-mac64 jq`
   - dist がない場合: `cd webapp/frontend && npm install && npm run build`

2. **起動**: `.claude/launch.json` に `font-studio` 設定があるので、
   ブラウザプレビューが使える環境では **preview_start（name: "font-studio"）** で起動する。
   使えない環境では:

   ```bash
   nohup python -m uvicorn webapp.backend.main:app --port 8000 > /tmp/font-studio.log 2>&1 &
   ```

3. **動作確認**: `curl -s localhost:8000/api/health` が `{"status":"ok",...}` を返すこと。
   `missing_tools` が空でなければユーザーに brew インストールを案内する
   （UI は表示できるがビルド実行はできない）。

4. ユーザーに <http://localhost:8000> を開くよう伝える。

### stop

```bash
pkill -f "uvicorn webapp.backend" || echo "起動していません"
```

preview_start で起動していた場合は preview_stop を使う。

### rebuild

フロントエンドを再ビルドしてから通常起動:

```bash
cd webapp/frontend && npm run build
```

サーバーが既に起動中なら再起動する（静的ファイルは dist から都度配信されるため
再起動不要だが、backend も変更されている場合は必要）。

### dev

フロントエンドを Vite の HMR で開発するモード（`/api` は :8000 にプロキシされる）:

```bash
# ターミナル1: backend（--reload 付き）
python -m uvicorn webapp.backend.main:app --port 8000 --reload
# ターミナル2: frontend
cd webapp/frontend && npm run dev   # http://localhost:5173
```

## トラブルシューティング

| 症状 | 対処 |
| --- | --- |
| `Address already in use` | 既に起動済み。`pkill -f "uvicorn webapp.backend"` してから再起動 |
| health が `degraded` | otfccdump/otfccbuild/jq が PATH にない。brew でインストール |
| 画面が真っ白/古い | `cd webapp/frontend && npm run build` 後にブラウザをリロード |
| prepare/build が `error: server restarted` | サーバー再起動でタスクが中断された。ビルド画面から再実行 |
| プロジェクトの中間ファイル | `tmp/projects/<id>/` と `tmp/json/*_proj_*.json`。削除は UI から（成果物も GC される） |

詳細は [webapp/README.md](../../webapp/README.md) を参照。
