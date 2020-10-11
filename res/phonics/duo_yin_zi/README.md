
```
.
├── NOTE.md
├── duoyinzi.json
├── duoyinzi_pattern_one.txt
├── duoyinzi_pattern_two.txt
├── ignone_phrase_pattern.txt　<- 編集可能　特別なパターンのみで使う
├── issue.md
├── phrase_of_pattern_one.txt　<- 置き換えが1個または0個の単語
├── phrase_of_pattern_two.txt　<- 置き換えが2個以上の単語
├── phrase_testcase.txt　<- validate_phrase.py が有効的に働くかどうかの確認に使ったテストケース
└── scripts
    ├── check_exsit_duoyinsi_on_word.py
    ├── make_pattern_table.py
    ├── phrase.py
    ├── phrase_holder.py
    ├── pinyin_getter.py
    └── validate_phrase.py
```
## 多音字について
書式が異なっているが、duoyinzi_one　が一熟語のうち一語のみ置き換えるパターン
duoyinzi_two は一熟語のうち二語以上置き換えるパターン


最初に辞書のチェックを行い
validate_phrase.py

パターンテーブル生成
make_pattern_table.py 