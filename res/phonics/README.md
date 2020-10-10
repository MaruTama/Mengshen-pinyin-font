# 拼音のtableについて
```
$ python3 create_unicode_pinyin_map_table.py  
```

サイトからunicode のテーブルをダウンロードする -> download_unicode_tables

↓

生成物(書式は[pinyin-data](https://github.com/mozillazg/pinyin-data/blob/master/pinyin.txt)に準拠する)
BIG5-mapping-table.txt -> 繁体字の範囲
TGSCC-mapping-table.txt -> 簡体字の範囲

↓

marged-mapping-table.txt -> 簡体字と繁体字を統合したもの

↓

overwrite.txt -> 修正のためのテーブル
pypinyin で取得できなかったもの、または間違っている pinyin を書く。（編集可）
marged-mapping-table.txt　に対して overwrite.txt の内容を上書きする。

