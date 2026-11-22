# 拼音のtableについて

```bash
python make_unicode_pinyin_map_table.py  
```

## 作成手順

1. サイトからunicode のテーブルをダウンロードする  
2. 繁体字と簡体字の unicode テーブルを作成  
3. 繁体字と簡体字を統合した unicode テーブルを作成  
4. unicode テーブル に overwrite.txt の内容を上書きする  

## 読みの元データ（pinyin-data）

読みの元データはサブモジュール `res/pinyin-data` で、[mozillazg/pinyin-data](https://github.com/mozillazg/pinyin-data) のフォーク [MaruTama/pinyin-data](https://github.com/MaruTama/pinyin-data) を参照する。

- 目標は pinyin-data だけを読みの正とし、overwrite.txt はこのプロジェクト固有の細かい修正だけに絞ること
- 読みの誤りはまずフォークで直して使い、本家へ PR を出す。本家に取り込まれたら overwrite.txt の該当行を消す
- overwrite.txt の棚卸しは [#75](https://github.com/MaruTama/Mengshen-pinyin-font/issues/75) で行う

## 生成物

unicode テーブルの書式は[pinyin-data](https://github.com/mozillazg/pinyin-data/blob/master/pinyin.txt)に準拠する  

overwrite.txt は色々な目的のために追加している  
    - pypinyin で取得できない漢字  
    - 発音の優先度の調整  
    - 儿 の r の追加  
    - 軽声の追加、重複する漢字は同じ発音にする  
    - 合成済みコードポイントが無い文字の読み（呣 m̀, 嘸 m̄, 欸 ê̄ など）も含める。拼音グリフは拼音フォントに無ければ [res/fonts/custom_pinyin_glyphs/](../../fonts/custom_pinyin_glyphs) の合成グリフで補う。大文字の読み（Ḿ, Ế, Ề など）は使わない  

### ファイル構成

```text
outputs
   └── marged-mapping-table.txt -> 簡体字と繁体字の unicode テーブルを統合したもの (overwrite.txt を反映済み)
```

```text
download_unicode_tables
         ├── big5_2003-u2b.txt -> 繁体字の対象範囲
         └── TGSCC-Unicode.txt -> 簡体字の対象範囲
```

```text
.
├── BIG5-mapping-table.txt           -> 繁体字の対象範囲の unicode テーブル  
├── README.md
├── TGSCC-mapping-table.txt          -> 簡体字の対象範囲の unicode テーブル  
├── make_unicode_pinyin_map_table.py -> 作成のスクリプト
└── overwrite.txt                    -> 修正のためのテーブル。 marged-mapping-table.txt　に対して上書きを行う。（編集可）
```
