#!/usr/bin/env python

import os
import pinyin_getter
import phrase_holder as ph
import validate_phrase as validate

PINYIN_MAPPING_TABLE = pinyin_getter.get_pinyin_table_with_mapping_table()
DEFALT_READING = 0

# [階層構造のあるdictをupdateする](https://www.greptips.com/posts/1242/)
def deepupdate(dict_base, other):
    for k, v in other.items():
        if isinstance(v, dict) and k in dict_base:
            deepupdate(dict_base[k], v)
        else:
            dict_base[k] = v


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
                for new_charactor in phrase:
                    if new_charactor != charactor and new_charactor in pattern_table_4_work:
                        if len(pattern_table_4_work[new_charactor]["patterns"]) > 1:
                            pinyin = PINYIN_MAPPING_TABLE[new_charactor][DEFALT_READING]
                            add_pattern_one_table( pattern_table_4_work, new_charactor, pinyin, phrase.replace(new_charactor, "~") )
    
            pattern_table_4_work.pop(charactor)

    return pattern_table_4_work

# パターンテーブルの txt を出力する
def export_pattern_one_table(pattern_table, PATTERN_ONE_TABLE_FILE):
    with open(PATTERN_ONE_TABLE_FILE, mode='w') as write_file:
        for charactor in pattern_table:
            order = 1
            for pinyin in PINYIN_MAPPING_TABLE[charactor]:
                if pinyin in list( pattern_table[charactor]["patterns"].keys() ):
                    str_patterns = expand_pattern_list2str( pattern_table[charactor]["patterns"][pinyin] )
                    line = "{0}, {1}, {2}, [{3}]\n".format(order, charactor, pinyin, str_patterns)
                    write_file.write(line)
                    order += 1

def expand_pattern_list2str(patterns):
    expand_pattern = ""
    for pattern in patterns:
        expand_pattern += "{}|".format(pattern) if pattern != patterns[-1] else pattern
    return expand_pattern

# 単語中に含まれる標準的でないピンインの数を返す
def seek_variational_pinyin_in_phrase(phrase_instance):
    count_variational_pinyin = 0
    target_hanzes = []
    phrase = phrase_instance.get_name()
    for i in range(len(phrase)):
        charactor = phrase[i]
        charactor_pinyin = phrase_instance.get_list_pinyin()[i]
        charactor_default_pinyin = PINYIN_MAPPING_TABLE[charactor][DEFALT_READING]
        if charactor_pinyin != charactor_default_pinyin:
            count_variational_pinyin += 1
            target_hanzes.append(charactor)

    return count_variational_pinyin, target_hanzes

def make_pattern_one(phrase_holder, PATTERN_ONE_TABLE_FILE):
    """
    こんな感じの辞書を作り、パターンテーブルを作る
    {
        "供": {
            "pinyin": ["gōng","gòng"],
            "pattern": {
                "gōng": ["*给","*应"],
                "gòng": ["*养","自*"]
            }
        }
    }
    """
    pattern_table = {}
    for phrase_instance in phrase_holder.get_list_instance_phrases():
        count_variational_pinyin, target_hanzes = seek_variational_pinyin_in_phrase(phrase_instance)
        phrase = phrase_instance.get_name()
        # 単語はすべて標準的なピンイン（多音字ではない）
        # ピンインを複数持つ(かつ今回は標準的なピンインで読む）漢字を見つけ次第入れる。先勝ち。
        # 単一の読みしか持たない漢字で構成される単語は除外する
        if   0 == count_variational_pinyin:
            for i in range(len(phrase)):
                charactor = phrase[i]
                if 1 < len(PINYIN_MAPPING_TABLE[charactor]):
                    add_pattern_one_table( pattern_table, charactor, phrase_instance.get_list_pinyin()[i], phrase.replace(charactor, "~") )
                    break
        # 対象の多音字の漢字のパターンに入れる
        elif 1 == count_variational_pinyin:
            target_hanzi = target_hanzes[0]
            idx = phrase.index(target_hanzi)
            add_pattern_one_table( pattern_table, target_hanzi, phrase_instance.get_list_pinyin()[idx], phrase.replace(target_hanzi, "~") )
        # 単語はすべて標準的なピンイン（多音字ではない）
        else:
            message = "{} は 2文字以上 多音字を含んでいます。".format( phrase_instance.get_name() )
            raise Exception(message)

    pattern_table = compress_pattern_one_table(pattern_table)
    export_pattern_one_table(pattern_table, PATTERN_ONE_TABLE_FILE)

"""
ここから pattern_two のための関数
"""
def make_pattern_two(IGNONE_PHRASE_PATTERN):
    """
    着手: [背着手]
    轴子: [大轴子,压轴子]
    """

def main():
    PHRASE_ONE_TABLE = "phrase_of_pattern_one.txt"
    PHRASE_TWO_TABLE = "phrase_of_pattern_two.txt"
    DIR_RT = "../"

    OUTPUT_PATTERN_ONE_TABLE = "duoyinzi_pattern_one.txt"
    OUTPUT_PATTERN_TWO_TABLE = "duoyinzi_pattern_two.txt"
    DIR_OT = "../../../../outputs"

    PHRASE_ONE_TABLE_FILE = os.path.join(DIR_RT, PHRASE_ONE_TABLE)

    OUTPUT_PATTERN_ONE_TABLE_FILE = os.path.join(DIR_OT, OUTPUT_PATTERN_ONE_TABLE)
    OUTPUT_PATTERN_TWO_TABLE_FILE = os.path.join(DIR_OT, OUTPUT_PATTERN_TWO_TABLE)

    # 一応確認しておく
    validate.main(PHRASE_ONE_TABLE_FILE)

    # pattern_one から phrase_holder を作る
    # duoyinzi_pattern_one を作成する
    phrase_holder = ph.PhraseHolder(PHRASE_ONE_TABLE_FILE)
    make_pattern_one(phrase_holder, OUTPUT_PATTERN_ONE_TABLE_FILE)


    # pattern_two から phrase_holder を作る
    # duoyinzi_pattern_two を作成する
    # 重複を確認する

    # phrase_holder = ph.PhraseHolder(PHRASE_TABLE_FILE)
    # make_pattern_two(phrase_holder, PATTERN_TWO_TABLE)


    # 特殊なパターンを作る
    # 着手 と 背着手 のパターンができるかどうか確認しない
    #できた
    """
    lookup calt2 {
        ignore sub uni80CC uni7740' uni624B;
        sub uni7740' uni624B by d;
    } calt2;
    """
    

    


if __name__ == "__main__":
    main()
