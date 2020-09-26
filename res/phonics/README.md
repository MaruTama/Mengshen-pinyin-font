# 拼音のtableについて
$ python3 create_unicode_pinyin_map_table.py  

サイトからunicode のテーブルをダウンロードする -> download_unicode_tables

pypinyin で取得できなかったもの、または間違っている pinyin を書く。（編集可）
上のマッピングテーブルから取得して、間違っている箇所を overwrite.txt に基づいて下のファイルに上書きする。
overwrite.txt

生成物(書式は[pinyin-data](https://github.com/mozillazg/pinyin-data/blob/master/pinyin.txt)に準拠する)
BIG5-mapping-table.txt -> 繁体字の範囲
TGSCC-mapping-table.txt -> 簡体字の範囲

marged-mapping-table.txt -> 簡体字と繁体字を統合したもの

## 多音字について
書式が異なっているが、duoyinzi_one　が一熟語のうち一語のみ置き換えるパターン
duoyinzi_two は一熟語のうち二語置き換えるパターン
duo_yin_zi/duoyinzi_one.txt　（編集可）
duo_yin_zi/duoyinzi_two.txt　（編集可）
