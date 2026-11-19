---
name: font-glyph-view
description: Mengshen 拼音フォントのグリフを PNG にして目視確認するスキル。フォントと漢字を指定すると、既定の読みと IVS で選べる全ての読み（cmap format 14）を一覧画像にする。任意の文字列の描画も可。「グリフを表示して」「拼音が出ているか画像で見せて」「IVS の読みを一覧で見たい」と言われたら使う。$ARGUMENTS にフォントパスや文字を渡せる。
---

# font-glyph-view

ビルドしたフォント（または任意の .ttf/.otf）のグリフを FreeType (Pillow) で描画し、PNG で確認する。

## 手順

1. 対象を決める（$ARGUMENTS に無ければ既定を使う）
   - フォント: 既定は `outputs/Mengshen-HanSerif.ttf` と `outputs/Mengshen-Handwritten.ttf`（存在するもの）。作業ツリーで作業中ならその作業ツリーの `outputs/`。
   - 文字: `--chars` に漢字を並べる（1 文字 = 1 行。既定の読み + 全 IVS の読み）。
   - 文字列: `--text` で任意の文字列を 1 行描画（文脈置換 GSUB は Pillow の basic layout では効かない点に注意。既定の読みのみ）。
2. 実行する。出力はスクラッチパッド（無ければ `.claude/tmp/`）に置く。

```bash
uv run --with pillow --with fonttools python .claude/skills/font-glyph-view/render_glyphs.py \
  outputs/Mengshen-HanSerif.ttf outputs/Mengshen-Handwritten.ttf \
  --chars 欸誒呣嗯 --text "你好中国" --out <scratchpad>/glyph_sheet.png
```

1. 生成した PNG を Read で確認し、ユーザーには SendUserFile（display: render）で送る。
2. 所見を報告する: 拼音の欠け・はみ出し・重なり、IVS の番号と読みの対応（ラベルはセレクタのコードポイント。萌神は U+E01E0 が拼音なし (ss00)、U+E01E0+n が n 番目の読み）。

## 注意

- 描画は FreeType。CoreText / DirectWrite / Android の表示とは一致しない場合がある（最終確認は実機）。
- IVS の一覧はフォントの cmap format 14 から取る。読みの文字列はフォントからは分からないので、必要なら `outputs/merged-mapping-table.txt` の該当行と突き合わせる。
- `python` は bare で OK（uv 管理）。`uv run --with` は一時環境なのでプロジェクトの venv を汚さない。
