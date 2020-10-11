#!/usr/bin/env python
import os
import re
import pinyin_getter

PINYIN_MAPPING_TABLE = pinyin_getter.get_pinyin_table_with_mapping_table()
DEFALT_READING = 0

# 重複している単語（単純な記述ミス）を返す
def get_duplicate_phrase(PHRASE_TABLE_FILE):
    phrases = []
    with open(PHRASE_TABLE_FILE) as read_file:
        for line in read_file:
            [phrase, _] = line.rstrip('\n').split(': ')
            phrases.append(phrase)
    
    duplicate_phrases = [phrase for phrase in set(phrases) if phrases.count(phrase) > 1]
    return duplicate_phrases

# 他のパターン（単語）に影響するパターン（単語）を返す
def get_duplicate_pattern_of_phrase(PHRASE_TABLE_FILE):
    phrases = []
    str_consolidated_phrases = ""
    with open(PHRASE_TABLE_FILE) as read_file:
        for line in read_file:
            [phrase, _] = line.rstrip('\n').split(': ')
            str_consolidated_phrases += phrase + "/"
            phrases.append(phrase)

    duplicate_pattern_of_phrases = []
    for phrase in phrases:
        found_phrases = re.findall(phrase, str_consolidated_phrases)
        if len(found_phrases) > 1:
            duplicate_pattern_of_phrases.append(phrase)
            
    return duplicate_pattern_of_phrases
    
# 単語中に置き換わる文字(多音字)が複数ある単語を返す
def get_multiple_replacement_by_duoyinzi(PHRASE_TABLE_FILE):
    list_multiple_replacement_by_duoyinzi = []
    with open(PHRASE_TABLE_FILE) as read_file:
        for line in read_file:
            [phrase, pinyin_of_phrase] = line.rstrip('\n').split(': ')
            if 2 <= count_variational_pinyin(phrase, pinyin_of_phrase):
                list_multiple_replacement_by_duoyinzi.append(phrase)
    return list_multiple_replacement_by_duoyinzi

def count_variational_pinyin(phrase, pinyin_of_phrase):
    variational_pinyin_count = 0
    for i in range(len(phrase)):
        charactor = phrase[i]
        default_pinyin = PINYIN_MAPPING_TABLE[charactor][DEFALT_READING]
        if default_pinyin != pinyin_of_phrase.split('/')[i]:
            variational_pinyin_count += 1
    return variational_pinyin_count

def get_phrase_dict(PHRASE_TABLE_FILE):
    phrase_dict = {}
    with open(PHRASE_TABLE_FILE) as read_file:
        for line in read_file:
            [phrase, pinyin_of_phrase] = line.rstrip('\n').split(': ')
            phrase_dict.update( {phrase : pinyin_of_phrase} )
    return phrase_dict

def pattern_one(PHRASE_TABLE_FILE):    

    # 単語の重複がないか（単純な記述ミス）
    # 対処法
    # -> 重複箇所を消す
    """
    背弃: bēi/qì
    背弃: bēi/qì
    """
    duplicate_phrases = get_duplicate_phrase(PHRASE_TABLE_FILE)
    if len(duplicate_phrases) > 0:
        print("重複する単語を削除してください")
        print("Duplicate phrase :")
        print(duplicate_phrases)
        exit()
    else:
        print("success!")
        print("Nothing duplicate phrase.")
        print()

    # 他のパターン（単語）に影響するパターン（単語）がないか
    # 対処法
    # -> 基本的に文字数が小さいパターンに合わせる。 阿谀 と 胶阿谀 なら 阿谀 を消す。
    #　　 着手: zhuó/shǒu と 背着手: bèi/zhe/shǒu　は両方とも違うので残す
    # 　　轴子 は zhóu が標準的な読みなので 轴子 のパターンが無くても構わない。
    """
    阿谀: ē/yú
    胶阿谀: jiāo/ē/yú
    轴子: zhóu/zǐ
    大轴子: dà/zhòu/zǐ
    压轴子: yā/zhòu/zi
    """
    duplicate_pattern_of_phrases = get_duplicate_pattern_of_phrase(PHRASE_TABLE_FILE)
    if len(duplicate_pattern_of_phrases) > 0:
        print("重複する単語（パターン）を削除してください")
        print("There are duplicates that affect other phrases :")
        print(duplicate_pattern_of_phrases)
        exit()
    else:
        print("success!")
        print("Nothing duplicates that affect other phrase.")
    print()

    # 単語中に異読字が２個以上ないか
    # 対処法
    # -> 別ファイル(pattern_two)へ
    """
    参差: cēn/cī
    参: cān -> cēn
    差: chà -> cī
    """
    list_multiple_replacement_by_duoyinzi = get_multiple_replacement_by_duoyinzi(PHRASE_TABLE_FILE)
    if len(list_multiple_replacement_by_duoyinzi) > 0:
        print("単語を phrase_of_pattern_two.txt に移動させてください")
        print("There is more than one hanzi(kanji) that can be replaced by Pinyin in a phrase : ")
        print(list_multiple_replacement_by_duoyinzi)
        exit()
    else:
        print("success!")
        print("There is no more than one hanzi(kanji) that can be replaced by Pinyin in a phrase.")
    print()


def pattern_two(PHRASE_TABLE_FILE):    

    # 単語の重複がないか（単純な記述ミス）
    duplicate_phrases = get_duplicate_phrase(PHRASE_TABLE_FILE)
    if len(duplicate_phrases) > 0:
        print("重複する単語を削除してください")
        print("Duplicate phrase :")
        print(duplicate_phrases)
        exit()
    else:
        print("success!")
        print("Nothing duplicate phrase.")
        print()

    # すべての単語が単語中に異読字が２個以上あるか
    """
    参差: cēn/cī
    参: cān -> cēn
    差: chà -> cī
    """
    list_multiple_replacement_by_duoyinzi = get_multiple_replacement_by_duoyinzi(PHRASE_TABLE_FILE)
    phrase_dict = get_phrase_dict(PHRASE_TABLE_FILE)
    if len(list_multiple_replacement_by_duoyinzi) != len(phrase_dict):
        print("単語を phrase_of_pattern_one.txt に移動、もしくは削除してください。")
        print("There is less than one different reading hanzi(kanji) in the phrase : ")
        for phrase, str_pinyin in phrase_dict.items():
            if not (phrase in list_multiple_replacement_by_duoyinzi):
                if   count_variational_pinyin(phrase, str_pinyin) == 0:
                    print("{} <- delete it.".format(phrase))
                elif count_variational_pinyin(phrase, str_pinyin) == 1:
                    print("{} <- move it.".format(phrase))
                else:
                    print("{} <- error.")
        exit()
    else:
        print("success!")
        print("There is more than one hanzi(kanji) that can be replaced by Pinyin in a phrase.")
    print()
        
if __name__ == '__main__':
    DIR_PT = "../"
    PHRASE_TABLE = "phrase_of_pattern_one.txt"
    PHRASE_TABLE_FILE = os.path.join(DIR_PT, PHRASE_TABLE)
    pattern_one(PHRASE_TABLE_FILE)

    print("========================================================================")

    PHRASE_TABLE = "phrase_of_pattern_two.txt"
    PHRASE_TABLE_FILE = os.path.join(DIR_PT, PHRASE_TABLE)
    pattern_two(PHRASE_TABLE_FILE)

