
```
.
├── NOTE.md
├── duoyinzi.json
├── duoyinzi_pattern_one.txt
├── duoyinzi_pattern_two.txt
├── ignone_phrase_pattern.txt　<- 編集可能　特別なパターンのみで使う
├── issue.md
├── phrase.txt　<- 編集可能　複数の読みを持つ漢字の単語帳になっている
├── phrase_of_pattern_one.txt　<- phrase.txt を validate_phrase.py でチェックしてから作成するもの（自動化したいけど見落としそうなので手動で確認しながら）
├── phrase_of_pattern_two.txt　<- phrase.txt を validate_phrase.py でチェックしてから作成するもの
├── phrase_testcase.txt
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