# 多音字について
pattern one は 熟語の中で 0~1 文字だけ拼音が変化するパターン  
pattern two は 熟語の中で 2 文字以上拼音が変化するパターン  
exception pattern は 例外的なパターン  

# ファイル構成
```
outputs
   ├── duoyinzi_pattern_one.txt          <- make_pattern_table.py によって生成される
   ├── duoyinzi_pattern_two.json         <- make_pattern_table.py によって生成される
   └── duoyinzi_exceptional_pattern.json <- 特別なパターンのみで使う
```
現在は、duoyinzi_exceptional_pattern.json の生成は手動にて生成している.
-> [生成箇所](https://github.com/MaruTama/Mengshen-pinyin-font/blob/e5d6e9e1770d849d6c17016683faf7c04d028473/res/phonics/duo_yin_zi/scripts/make_pattern_table.py#L237-L276)

```
.
├── NOTE.md
├── phrase_of_exceptional_pattern.txt <- 例外的な置換パターンを含む熟語集（編集可能）  
├── phrase_of_pattern_one.txt         <- 熟語の中で 0~1文字だけ拼音が変化する熟語集（編集可能）  
├── phrase_of_pattern_two.txt         <- 熟語の中で 2文字以上拼音が変化する熟語集（編集可能）
├── phrase_testcase.txt               <- validate_phrase.py が有効的に働くかどうかの確認に使ったテストケース
└── scripts
    ├── check_exsit_duoyinsi_on_word.py
    ├── make_pattern_table.py
    ├── phrase.py
    ├── phrase_holder.py
    ├── pinyin_getter.py
    └── validate_phrase.py
```

# 生成手順
```
# 最初に辞書のチェックを行う
$ python validate_phrase.py

# パターンテーブル生成
$ python make_pattern_table.py 
```

## make_pattern_table.py の概略

```mermaid 
flowchart TB
    classDef noteclass fill:#fff5ad,stroke:#decc93;

    id0["単語の重複がある<br/>validate_phrase.get_duplicate_word()"] -- yes --> 重複を削除する
    id0 -- no --> id1["他の単語に影響するパターンがある<br/>validate_phrase.get_duplicate_pattern_of_word()"]
    id1 -- yes --> id2["
        書き込み先は phrase_of_exceptional_pattern.txt になる

        基本的に小さいパターンに合わせる
        例えば、「阿谀」と「胶阿谀」なら阿谀を残す
    "]
    id1 -- no --> id3["単語中で置き換わる文字（多音字)は2文字以上か<br/>validate_phrase.get_multiple_replacement_by_duoyinzi()"]
    id3 -- yes --> id4["
                        書き込み先はphrase_of_pattern_two.txtになる

                        文脈依存の複数置換のパターンを作成する
                        make_pattern_table.set_pattern_two()
                        
                        #グリフの名前は、'ss01'~'ss20'にする。
                        #ss00 は何も付いていない漢字のグリフにする
                        #ss01は標準的な拼音
                        #ss02 以降は異読的な拼音"]
    id3 -- no --> id5["
                        書き込み先はphrase_of_pattern_one.txtになる

                        置き換わる文字（多音字）に対して、パターンを作成する
                        make_pattern_table.set_pattern_one()

                        ・すべての文字が標準的なピンイン（多音字ではない）のみで構成される単語のとき
                        　　ピンインを複数持つ(かつ今回は標準的なピンインで読む）漢字を見つけ次第入れる。つまり先勝ちで詰めていく。
                        　　もし、すべて単一の読みしか持たない漢字で構成される単語ならパターンテーブルから除外する
                        ・ 単語中に置き換わる文字（多音字)が一文字のとき
                        　　対象の漢字のパターンに単語を入れる

                        "]
    %% フローチャートだとNOTEが使えないので、nodeで代用する
    id2 -.- SEVLNOTE0["
        e.g.:

        [轴子]と[大轴子,压轴子]
        [着手]と[背着手]
        
        例外パターンは下記のように calt feature を記述する
        lookup calt {
        　　ignore sub uni80CC uni7740' uni624B;
        　　sub uni7740' uni624B by d;
        } calt;

        すると
        着手->着手
        背着手->背d手
        のように、それぞれ別パターンに置換される
        "]:::noteclass
    id4 -.- SEVLNOTE1["
        e.g.:

        'lookup_table': {
        　　# 異読的なピンイン
        　　# 数字の並びは、marged-mapping-table.txt の配列の添字順にする。
        　　'lookup_10': {
        　　　　'占' : '占.ss02',
        　　　　'卜' : '卜.ss02',
        　　　　'少' : '少.ss02',
        　　　　'更' : '更.ss02'
        　　}
        }"]:::noteclass
    id4 -.- SEVLNOTE2["
            e.g.:
            
            兴兴头头: xīng/xìng/tou/tóu、
            占卜:zhān/bǔ、吐血:tù/xiě
            
            記述例（2つ以上置き換える）
            lookup calt {
            　　sub A' lookup lookup_0 A' lookup lookup_0 F;
            } calt;

            lookup lookup_0 {
            　　sub A by X;
            } lookup_0;

            すると
            AAF -> XXF
            のように二文字以上置き換えられる
        "]:::noteclass
    %% linkStyle 5 stroke-width:0px;

    style id2 text-align:left
    style id4 text-align:left
    style id5 text-align:left
    style SEVLNOTE0 text-align:left
    style SEVLNOTE1 text-align:left
    style SEVLNOTE2 text-align:left
```