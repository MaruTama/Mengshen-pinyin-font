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
                for i in range(len(phrase)):
                    new_charactor = phrase[i]
                    if new_charactor != charactor and new_charactor in pattern_table_4_work:
                        if len(pattern_table_4_work[new_charactor]["patterns"]) > 1:
                            pinyin = PINYIN_MAPPING_TABLE[new_charactor][DEFALT_READING]
                            # replace で置き換えると　累累: lěi/lèi　のpatternが ~~ になるので手動で置換する
                            pattern = replace_str(phrase, i, "~")
                            add_pattern_one_table( pattern_table_4_work, new_charactor, pinyin, pattern )
    
            pattern_table_4_work.pop(charactor)

    return pattern_table_4_work

def replace_str(target_str, index, replace_charactor):
    tmp = list(target_str)
    tmp[index] = replace_charactor
    return "".join( tmp )

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
            target_hanzes.append( (i, charactor) )

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
                    pinyin = phrase_instance.get_list_pinyin()[i]
                    # replace で置き換えると　累累: lěi/lèi　のpatternが ~~ になるので、手動で置換する
                    pattern = replace_str(phrase, i, "~")
                    add_pattern_one_table( pattern_table, charactor, pinyin, pattern )
                    break
        # 対象の多音字の漢字のパターンに入れる
        elif 1 == count_variational_pinyin:
            (idx, target_hanzi) = target_hanzes[0]
            variational_pinyin = phrase_instance.get_list_pinyin()[idx]
            pattern = replace_str(phrase, idx, "~")
            add_pattern_one_table( pattern_table, target_hanzi, variational_pinyin, pattern )
        # 単語はすべて標準的なピンイン（多音字ではない）
        else:
            message = "{} は 2文字以上 多音字を含んでいます。".format( phrase_instance.get_name() )
            raise Exception(message)

    pattern_table = compress_pattern_one_table(pattern_table)
    export_pattern_one_table(pattern_table, PATTERN_ONE_TABLE_FILE)

"""
ここから pattern_two のための関数
"""
def make_pattern_two(phrase_holder, OUTPUT_PATTERN_TWO_TABLE_FILE):
    pass

def main():
    PHRASE_ONE_TABLE = "phrase_of_pattern_one.txt"
    PHRASE_TWO_TABLE = "phrase_of_pattern_two.txt"
    DIR_RT = "../"

    OUTPUT_PATTERN_ONE_TABLE = "duoyinzi_pattern_one.txt"
    OUTPUT_PATTERN_TWO_TABLE = "duoyinzi_pattern_two.txt"
    DIR_OT = "../../../../outputs"

    PHRASE_ONE_TABLE_FILE = os.path.join(DIR_RT, PHRASE_ONE_TABLE)
    PHRASE_TWO_TABLE_FILE = os.path.join(DIR_RT, PHRASE_TWO_TABLE)

    OUTPUT_PATTERN_ONE_TABLE_FILE = os.path.join(DIR_OT, OUTPUT_PATTERN_ONE_TABLE)
    OUTPUT_PATTERN_TWO_TABLE_FILE = os.path.join(DIR_OT, OUTPUT_PATTERN_TWO_TABLE)

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
    无色无臭: wú/sè/wú/xiù
    累累: lěi/lèi
    占卜: zhān/bǔ
        占 zhàn
        卜 bo
    
    {
        "lookup_table": {
            # 標準的なピンイン
            "lookup_10": {
                "累" : "累.ss00",
            },
            # 異読的なピンイン
            "lookup_11": {
                "臭" : "臭.ss02",
                "累" : "累.ss02",
                "占" : "无.ss02",
                "卜" : "卜.ss02"
            }
        },
        "pattern": {
            "无色无臭" : [
                {"无" : ""}, 
                {"色" : ""}, 
                {"无" : ""}, 
                {"臭" : "lookup_11"}
            ],
            "累累" : [
                {"累" : "lookup_10"},
                {"累" : "lookup_11"}
            ],
            "占卜" : [
                {"占" : "lookup_11"}, 
                {"卜" : "lookup_11"}
            ]
        }
    }
    """



    # 特殊なパターンを作る
    # 着手 と 背着手 のパターンができるかどうか確認しない
    #できた
    """
    着手: [背着手]
    轴子: [大轴子,压轴子]
    """
    """
    lookup calt2 {
        ignore sub uni80CC uni7740' uni624B;
        sub uni7740' uni624B by d;
    } calt2;
    """
    

    


if __name__ == "__main__":
    main()
