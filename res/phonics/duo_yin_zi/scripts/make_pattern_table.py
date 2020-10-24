# -*- coding: utf-8 -*-
#!/usr/bin/env python

# python3 make_pattern_table.py 

import os
import json
import pinyin_getter
import phrase_holder as ph
import validate_phrase as validate

PINYIN_MAPPING_TABLE = pinyin_getter.get_pinyin_table_with_mapping_table()
NORMAL_PRONUNCIATION = 0

# ss0X の番号振り
# [Tag: 'ss01' - 'ss20'](https://docs.microsoft.com/en-us/typography/opentype/spec/features_pt#-tag-ss01---ss20)
# グリフの名前は、'ss01' - 'ss20' にする。
# uni4E0D　　　　標準の読みの拼音
# uni4E0D.ss00　無印の漢字グリフ。設定を変更するだけで拼音を変更できる
# uni4E0D.ss01　以降、異読
# uni4E0D.ss02　

SS_WITHOUT_PRONUNCIATION     = 0
SS_VARIATIONAL_PRONUNCIATION = 1

# [階層構造のあるdictをupdateする](https://www.greptips.com/posts/1242/)
def deepupdate(dict_base, other):
    for k, v in other.items():
        if isinstance(v, dict) and k in dict_base:
            deepupdate(dict_base[k], v)
        else:
            dict_base[k] = v

def replace_chr(target_str, index, replace_charactor):
    tmp = list(target_str)
    tmp[index] = replace_charactor
    return "".join( tmp )

def expand_pattern_list2str(patterns):
    return "|".join( patterns )


"""
ここから pattern_one のための関数
"""

def add_pattern_one_table(pattern_table, charactor, pinyin, pattern):
    if not (pinyin in PINYIN_MAPPING_TABLE[charactor]):
        message = "{} => {} は 正しいピンインではありません".format(charactor, pinyin)
        raise Exception(message)
        
    if not (charactor in pattern_table):
        pattern_table.update( 
            { 
                charactor: { 
                    "pinyin": PINYIN_MAPPING_TABLE[charactor],
                    "patterns": { pinyin: [pattern] }
                }
            })
        return 

    if not (pinyin in pattern_table[charactor]["patterns"]):
        new_dict_of_charactor = pattern_table[charactor]
        deepupdate( new_dict_of_charactor, { "patterns": { pinyin: [pattern] }} )
        pattern_table.update( 
            { 
                charactor: new_dict_of_charactor
            }
        )
    else:
        new_dict_of_charactor = pattern_table[charactor]
        new_patterns = new_dict_of_charactor["patterns"][pinyin]
        new_patterns.append(pattern)
        deepupdate( new_dict_of_charactor, { "patterns": { pinyin: new_patterns }} )
        pattern_table.update( 
            { 
                charactor: new_dict_of_charactor
            }
        )

# pattern_table[漢字]["patterns"] が一つだけのときは不要なパターンである。
# （標準的なピンインで構成された単語なので消してもいいが、もったいないので他のパターンに入れる. 他のパターンが見つからないなら削除）
# 辨 {'pinyin': ['biàn', 'biǎn', 'bàn', 'piàn'], 'patterns': {'biàn': ['~别']}}
# なら 别 のテーブルに移動する
# ネスト深くてキモいな。。。
def compress_pattern_one_table(pattern_table):
    import copy as cy
    pattern_table_4_work = cy.deepcopy(pattern_table)
    for charactor in pattern_table:
        if len(pattern_table[charactor]["patterns"]) == 1:
            
            patterns = list( pattern_table_4_work[charactor]["patterns"].values() )[0]
            for pattern in patterns:
                phrase = pattern.replace("~", charactor)
                for i in range(len(phrase)):
                    new_charactor = phrase[i]
                    if new_charactor != charactor and new_charactor in pattern_table_4_work:
                        if len(pattern_table_4_work[new_charactor]["patterns"]) > 1:
                            pinyin = PINYIN_MAPPING_TABLE[new_charactor][NORMAL_PRONUNCIATION]
                            # replace で置き換えると　累累: lěi/lèi　のpatternが ~~ になるので手動で置換する
                            pattern = replace_chr(phrase, i, "~")
                            add_pattern_one_table( pattern_table_4_work, new_charactor, pinyin, pattern )
            pattern_table_4_work.pop(charactor)

    return pattern_table_4_work

# パターンテーブルの txt を出力する
def export_pattern_one_table(pattern_table, PATTERN_ONE_TABLE_FILE):
    with open(PATTERN_ONE_TABLE_FILE, mode='w', encoding='utf-8') as write_file:
        for charactor in pattern_table:
            order = 1
            for pinyin in PINYIN_MAPPING_TABLE[charactor]:
                if pinyin in list( pattern_table[charactor]["patterns"].keys() ):
                    str_patterns = expand_pattern_list2str( pattern_table[charactor]["patterns"][pinyin] )
                    line = "{0}, {1}, {2}, [{3}]\n".format(order, charactor, pinyin, str_patterns)
                    write_file.write(line)
                    order += 1

# 単語中に含まれる標準的でないピンインの数を返す
def seek_variational_pronunciation_in_phrase(phrase_instance):
    count_variational_pronunciation = 0
    target_hanzes = []
    phrase = phrase_instance.get_name()
    for i in range(len(phrase)):
        charactor = phrase[i]
        charactor_pinyin = phrase_instance.get_list_pinyin()[i]
        charactor_normal_pronunciation = PINYIN_MAPPING_TABLE[charactor][NORMAL_PRONUNCIATION]
        if charactor_pinyin != charactor_normal_pronunciation:
            count_variational_pronunciation += 1
            target_hanzes.append( (i, charactor) )

    return count_variational_pronunciation, target_hanzes

def make_pattern_one(phrase_holder, PATTERN_ONE_TABLE_FILE):
    """
    こんな感じの辞書を作り、パターンテーブルを作る
    {
        "供": {
            "pinyin": ["gōng","gòng"],
            "pattern": {
                "gōng": ["~给","~应"],
                "gòng": ["~养","自~"]
            }
        }
    }
    """
    pattern_table = {}
    for phrase_instance in phrase_holder.get_list_instance_phrases():
        count_variational_pronunciation, target_hanzes = seek_variational_pronunciation_in_phrase(phrase_instance)
        phrase = phrase_instance.get_name()
        # 単語はすべて標準的なピンイン（多音字ではない）
        # ピンインを複数持つ(かつ今回は標準的なピンインで読む）漢字を見つけ次第入れる。先勝ち。
        # 単一の読みしか持たない漢字で構成される単語は除外する
        if   0 == count_variational_pronunciation:
            for i in range(len(phrase)):
                charactor = phrase[i]
                if 1 < len(PINYIN_MAPPING_TABLE[charactor]):
                    pinyin = phrase_instance.get_list_pinyin()[i]
                    # replace で置き換えると　累累: lěi/lèi　のpatternが ~~ になるので、手動で置換する
                    pattern = replace_chr(phrase, i, "~")
                    add_pattern_one_table( pattern_table, charactor, pinyin, pattern )
                    break
        # 対象の多音字の漢字のパターンに入れる
        elif 1 == count_variational_pronunciation:
            (idx, target_hanzi) = target_hanzes[0]
            variational_pronunciation = phrase_instance.get_list_pinyin()[idx]
            pattern = replace_chr(phrase, idx, "~")
            add_pattern_one_table( pattern_table, target_hanzi, variational_pronunciation, pattern )
        # 単語はすべて標準的なピンイン（多音字ではない）
        else:
            message = "{} は 2文字以上 多音字を含んでいます。".format( phrase_instance.get_name() )
            raise Exception(message)

    pattern_table = compress_pattern_one_table(pattern_table)
    export_pattern_one_table(pattern_table, PATTERN_ONE_TABLE_FILE)

"""
ここから pattern_two のための関数
"""
# lookup table の番号にする
def get_pinyin_priority(charactor, pinyin):
    # uni4E0D　　　　標準の読みの拼音
    # uni4E0D.ss00　無印の漢字グリフ。設定を変更するだけで拼音を変更できる
    # uni4E0D.ss01　以降、異読なので、必ず "1" 以上になる. なので、- 1 をして添字を0から開始にする
    return PINYIN_MAPPING_TABLE[charactor].index(pinyin) - 1

def add_lookup4pattern_two(lookup_table_dict, phrase_instance):
    _, has_variational_pronunciation_hanzes = seek_variational_pronunciation_in_phrase(phrase_instance)
    for (idx, target_charactor) in has_variational_pronunciation_hanzes:
        pinyin = phrase_instance.get_list_pinyin()[idx]
        priority = get_pinyin_priority(target_charactor, pinyin)
        lookup_name = "lookup_1{}".format( priority )
        # init
        if not (lookup_name in lookup_table_dict):
            lookup_table_dict.update( {lookup_name:{}} )
        # set
        if not (target_charactor in lookup_table_dict[lookup_name]):
            lookup_table_dict[lookup_name].update( { target_charactor : "{0}.ss0{1}".format( target_charactor, (SS_VARIATIONAL_PRONUNCIATION + priority) ) } )

def get_pattern4pattern_two(phrase_instance):
    phrase_value = []
    phrase = phrase_instance.get_name()
    # init
    for charactor in phrase:
        phrase_value.append( {charactor: None} )
    # set
    _, has_variational_pronunciation_hanzes = seek_variational_pronunciation_in_phrase(phrase_instance)
    for (idx, target_charactor) in has_variational_pronunciation_hanzes:
        pinyin = phrase_instance.get_list_pinyin()[idx]
        priority = get_pinyin_priority(target_charactor, pinyin)
        phrase_value[idx] = \
            {
                target_charactor: "lookup_1{}".format( priority )
            }
    return phrase_value

def make_pattern_two(phrase_holder, OUTPUT_PATTERN_TWO_TABLE_FILE):
    dict_base = { "lookup_table": {}, "patterns": {} }
    for phrase_instance in phrase_holder.get_list_instance_phrases():
        add_lookup4pattern_two(dict_base["lookup_table"], phrase_instance)
        pattern = get_pattern4pattern_two(phrase_instance)
        dict_base["patterns"].update( {phrase_instance.get_name() : pattern} )
    
    with open(OUTPUT_PATTERN_TWO_TABLE_FILE, mode='w', encoding='utf-8') as f:
        json.dump(dict_base, f, indent=4, ensure_ascii=False)

"""
ここから exceptional_pattern のための関数
"""
# 特別なのでこれは手動で作成する。
def make_exceptional_pattern(OUTPUT_EXCEPTION_PATTERN_TABLE_FILE):
    dict_base = {
        "lookup_table": {
            "lookup_20": {
                "着" : "着.ss01",
                "轴" : "轴.ss01"
            }
        },
        "patterns": {
            "着手" : {
                "ignore" : "背 着' 手",
                "pattern" :[
                    {"着" : "lookup_20"}, 
                    {"手" : None}
                ]
            },
            "大轴子" : {
                "ignore" : None,
                "pattern" :[
                    {"大" : None}, 
                    {"轴" : "lookup_20"},
                    {"子" : None}
                ]
            },
            "压轴子" : {
                "ignore" : None,
                "pattern" :[
                    {"压" : None}, 
                    {"轴" : "lookup_20"},
                    {"子" : None}
                ]
            }
        }
    }
    with open(OUTPUT_EXCEPTION_PATTERN_TABLE_FILE, mode='w', encoding='utf-8') as f:
        json.dump(dict_base, f, indent=4, ensure_ascii=False)

def main():
    PHRASE_ONE_TABLE = "phrase_of_pattern_one.txt"
    PHRASE_TWO_TABLE = "phrase_of_pattern_two.txt"
    DIR_RT = "../"

    OUTPUT_PATTERN_ONE_TABLE = "duoyinzi_pattern_one.txt"
    OUTPUT_PATTERN_TWO_TABLE = "duoyinzi_pattern_two.json"
    OUTPUT_EXCEPTION_PATTERN_TABLE = "duoyinzi_exceptional_pattern.json"
    DIR_OT = "../../../../outputs"

    PHRASE_ONE_TABLE_FILE = os.path.join(DIR_RT, PHRASE_ONE_TABLE)
    PHRASE_TWO_TABLE_FILE = os.path.join(DIR_RT, PHRASE_TWO_TABLE)

    OUTPUT_PATTERN_ONE_TABLE_FILE = os.path.join(DIR_OT, OUTPUT_PATTERN_ONE_TABLE)
    OUTPUT_PATTERN_TWO_TABLE_FILE = os.path.join(DIR_OT, OUTPUT_PATTERN_TWO_TABLE)
    OUTPUT_EXCEPTION_PATTERN_TABLE_FILE = os.path.join(DIR_OT, OUTPUT_EXCEPTION_PATTERN_TABLE)
    

    """
    1, 阿, ā, [~托品]
    2, 阿, ē, [~谀]
    1, 差, chà, [~劲]
    2, 差, chā, [~别|~额|~距|~价|~错|~异|~数|偏~|误~|逆~]
    3, 差, chāi, [~遣|~使|~事|出~|公~|交~|钦~|当~]
    1, 藏, cáng, [~匿|~书|~拙|暗~|保~|躲~|库~|收~|窝~|蕴~|珍~|贮~|掩~|捉迷~]
    2, 藏, zàng, [~蓝|~历|~族|~红花|宝~]
    """
    """
    lookup calt0 {
        sub 阿' lookup lookup_00 [谀];
        # 前後の文脈で書き方が変わる
        sub 差' lookup lookup_00 [别 额 距 价 错 异 数];
        sub [偏 误 逆] 差' lookup lookup_00;
        sub 差' lookup lookup_01 [遣 使 事];
        sub [出 公 交 钦 当] 差' lookup lookup_01;
        sub 藏' lookup lookup_00 [蓝 历 族];
        sub [宝] 藏' lookup lookup_00;
        # 三文字以上ならそれ専用の参照を作る
        sub 藏' lookup lookup_00 红 花;
    } calt0;
    lookup lookup_00 {
        sub 阿 by 阿.ss02;
        sub 差 by 差.ss02;
        sub 藏 by 藏.ss02;
    } lookup_00;
    lookup lookup_01 {
        sub 差 by 差.ss03;
    } lookup_01;
    """
    # 一応確認しておく
    validate.pattern_one(PHRASE_ONE_TABLE_FILE)
    # pattern_one から phrase_holder を作る
    # duoyinzi_pattern_one を作成する
    phrase_holder = ph.PhraseHolder(PHRASE_ONE_TABLE_FILE)
    make_pattern_one(phrase_holder, OUTPUT_PATTERN_ONE_TABLE_FILE)

    print("========================================================================")


    # pattern_two の検証を作成
    # 重複を確認する
    # 異読の漢字が一つ以上あるか (颤颤巍巍: chàn/chàn/wēi/wēi これは異読字が無いので削除する)
    validate.pattern_two(PHRASE_TWO_TABLE_FILE)
    # pattern_two から phrase_holder を作る
    # duoyinzi_pattern_two を作成する
    phrase_holder = ph.PhraseHolder(PHRASE_TWO_TABLE_FILE)
    make_pattern_two(phrase_holder, OUTPUT_PATTERN_TWO_TABLE_FILE)

    """
    lookup calt1 {
        sub A' lookup lookup_10 A' lookup lookup_10 F;
    } calt1;
    lookup lookup_10 {
        sub A by X;
    } lookup_10;
    """

    """
    [Tag: 'ss01' - 'ss20'](https://docs.microsoft.com/en-us/typography/opentype/spec/features_pt#-tag-ss01---ss20)
    グリフの名前は、'ss01' - 'ss20' にする。
    ss01 はなにも付いていない漢字のグリフにする。

    最初からこんな漢字の cmap の記述に合わせて書く 
    
    pattern_one は lookup_0*
    pattern_two は lookup_1* を使う
    
    占卜: zhān/bǔ
        占 zhàn
        卜 bo
    少不更事: shào/bù/gēng/shì
        少 shǎo
        不 bù
        更 gèng
        事 shì
    {
        "lookup_table": {
            # 異読的なピンイン
            # 数字の並びは、marged-mapping-table.txt の配列の添字順にする。
            "lookup_10": {
                "占" : "无.ss02",
                "卜" : "卜.ss02",
                "少" : "少.ss02",
                "更" : "更.ss02"
            }
        },
        "pattern": {
            "占卜" : [
                {"占" : "lookup_10"}, 
                {"卜" : "lookup_10"}
            ],
            "少不更事" : [
                {"少" : "lookup_10"},
                {"不" : ""},
                {"更" : "lookup_10"},
                {"事" : ""}
            ]
        }
    }
    """



    # 特殊なパターンを作る
    # [5.f.ii. Specifying exceptions to the Chain Sub rule](http://adobe-type-tools.github.io/afdko/OpenTypeFeatureFileSpecification.html#5fii-specifying-exceptions-to-the-chain-sub-rule)
    # を利用する
    """
    着手: [背着手]
    轴子: [大轴子,压轴子]
    """
    """
    lookup calt2 {
        ignore sub uni80CC uni7740' uni624B;
        sub uni7740' uni624B by d;
    } calt2;

    着手: zhuó/shǒu, 背着手: bèi/zhe/shǒu
    轴子 は zhóu が標準的なピンインなので、ingone にしない
    轴子: zhóu/zi, 大轴子: dà/zhòu/zi, 压轴子: yā/zhòu/zi
    """
    make_exceptional_pattern(OUTPUT_EXCEPTION_PATTERN_TABLE_FILE)
    print("========================================================================")
    print("success!")
    print("Output duoyinzi_exceptional_pattern.json.")
    

if __name__ == "__main__":
    main()
