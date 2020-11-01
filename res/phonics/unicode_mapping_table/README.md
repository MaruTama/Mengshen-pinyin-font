# 拼音のtableについて
```
$ python make_unicode_pinyin_map_table.py  
```

## 作成手順
1. サイトからunicode のテーブルをダウンロードする  
2. 繁体字と簡体字の unicode テーブルを作成  
3. 繁体字と簡体字を統合した unicode テーブルを作成  
4. unicode テーブル に overwrite.txt の内容を上書きする  

## 生成物
unicode テーブルの書式は[pinyin-data](https://github.com/mozillazg/pinyin-data/blob/master/pinyin.txt)に準拠する  

overwrite.txt は色々な目的のために追加している  
    - pypinyin で取得できない漢字  
    - 発音の優先度の調整  
    - 儿 の r の追加  
    - 軽声の追加、重複する漢字は同じ発音にする  
    - 呣 m̀, 嘸 m̄　を除外するため（追加してもいいが拼音グリフを作るのが面倒になる）  


### ファイル構成 
```
outputs
   └── marged-mapping-table.txt -> 簡体字と繁体字の unicode テーブルを統合したもの (overwrite.txt を反映済み)
```

```
download_unicode_tables
         ├── big5_2003-u2b.txt -> 繁体字の対象範囲
         └── TGSCC-Unicode.txt -> 簡体字の対象範囲
```

```
.
├── BIG5-mapping-table.txt           -> 繁体字の対象範囲の unicode テーブル  
├── README.md
├── TGSCC-mapping-table.txt          -> 簡体字の対象範囲の unicode テーブル  
├── make_unicode_pinyin_map_table.py -> 作成のスクリプト
└── overwrite.txt                    -> 修正のためのテーブル。 marged-mapping-table.txt　に対して上書きを行う。（編集可）
```