#!/usr/bin/env python
import os
import re
import pinyin_getter

# 単語の重複がないか（単純な記述ミス）
def get_duplicate_word(PHRASE_TABLE_FILE):
    words = []
    with open(PHRASE_TABLE_FILE) as read_file:
        for line in read_file:
            [word, _] = line.rstrip('\n').split(': ')
            words.append(word)
    
    duplicate_words = [word for word in set(words) if words.count(word) > 1]
    return duplicate_words

# 他のパターン（単語）に影響するパターン（単語）がないか
def get_duplicate_pattern_of_word(PHRASE_TABLE_FILE, IGNONE_PHRASE_PATTERN_FILE):
    ignone_phrase_patterns = []
    with open(IGNONE_PHRASE_PATTERN_FILE) as read_file:
        for line in read_file:
            pattern = line.rstrip('\n').split(": ")[0]
            ignone_phrase_patterns.append(pattern)

    words = []
    str_consolidated_words = ""
    with open(PHRASE_TABLE_FILE) as read_file:
        for line in read_file:
            [word, _] = line.rstrip('\n').split(': ')
            str_consolidated_words += word + "/"
            words.append(word)

    duplicate_pattern_of_words = []
    for word in words:
        found_words = re.findall(word, str_consolidated_words)
        if len(found_words) > 1 and not (word in ignone_phrase_patterns):
            duplicate_pattern_of_words.append(word)
            
    return duplicate_pattern_of_words

# 単語中に同じ漢字が２回以上出現するものがないか
# 兴兴头头 -> xīng/xìng/tou/tóu のように重なると音が変わるパターン
# 血淋淋 -> xiě/lín/lín のように音が同じパターンの２つがある
# これらの単語は別ファイルへ
def get_multiple_same_hanzi_in_word(PHRASE_TABLE_FILE):
    list_multiple_same_hanzi_in_word = []
    with open(PHRASE_TABLE_FILE) as read_file:
        for line in read_file:
            [word, _] = line.rstrip('\n').split(': ')
            multiple_charactor = [charactor for charactor in word if word.count(charactor) > 1]
            if len(multiple_charactor) > 0:
                list_multiple_same_hanzi_in_word.append(line.rstrip('\n'))
    return list_multiple_same_hanzi_in_word
    
# 単語中に置き換わる文字(多音字)が一文字のみであるか確認する
def get_multiple_replacement_by_duoyinzi(PHRASE_TABLE_FILE):
    list_multiple_replacement_by_duoyinzi = []
    pinyin_table = pinyin_getter.get_pinyin_table_with_mapping_table()
    with open(PHRASE_TABLE_FILE) as read_file:
        for line in read_file:
            [word, pinyin_of_word] = line.rstrip('\n').split(': ')
            variational_pinyin_count = 0
            for i in range(len(word)):
                charactor = word[i]
                default_pinyin = pinyin_table[charactor][0]
                if default_pinyin != pinyin_of_word.split('/')[i]:
                    variational_pinyin_count += 1
            if 2 <= variational_pinyin_count:
                list_multiple_replacement_by_duoyinzi.append(word)
    return list_multiple_replacement_by_duoyinzi

def main(PHRASE_TABLE_FILE, IGNONE_PHRASE_PATTERN_FILE):    

    # 単語の重複がないか（単純な記述ミス）
    # 対処法
    # -> 重複箇所を消す
    """
    背弃: bēi/qì
    背弃: bēi/qì
    """
    duplicate_words = get_duplicate_word(PHRASE_TABLE_FILE)
    if len(duplicate_words) > 0:
        print("重複する単語を削除してください")
        print("Duplicate word :")
        print(duplicate_words)
        exit()
    else:
        print("success!")
        print("Nothing duplicate word.")
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
    duplicate_pattern_of_words = get_duplicate_pattern_of_word(PHRASE_TABLE_FILE, IGNONE_PHRASE_PATTERN_FILE)
    if len(duplicate_pattern_of_words) > 0:
        print("重複する単語（パターン）を削除してください")
        print("There are duplicates that affect other words :")
        print(duplicate_pattern_of_words)
        exit()
    else:
        print("success!")
        print("Nothing duplicates that affect other word.")
    print()


    # 単語中に同じ漢字が２回以上出現するものがないか
    # 対処法
    # -> 別ファイル(pattern_two)へ
    """
    血淋淋: xiě/lín/lín
    兴兴头头: xīng/xìng/tou/tóu
    """
    list_multiple_same_hanzi_in_word = get_multiple_same_hanzi_in_word(PHRASE_TABLE_FILE)
    if len(list_multiple_same_hanzi_in_word) > 0:
        print("単語を別ファイルに移動させてください")
        print("Multiple occurrences of the same hanzi in a word : ")
        print(list_multiple_same_hanzi_in_word)
        exit()
    else:
        print("success!")
        print("There is only one hanzi in a word.")
    print()

    # ここは標準の読みが変わると変わる可能性があるので 
    # phrase.txt から phrase_of_pattern_two.txt に移動せず、そのままにしておく
    # 単語中に音が置き換わる漢字が２個以上ないか
    # 対処法
    # -> 別ファイル(pattern_two)へ
    """
    参差: cēn/cī
    参: cān -> cēn
    差: chà -> cī
    """
    list_multiple_replacement_by_duoyinzi = get_multiple_replacement_by_duoyinzi(PHRASE_TABLE_FILE)
    if len(list_multiple_replacement_by_duoyinzi) > 0:
        print("単語を別ファイルに移動させてください")
        print("There is more than one hanzi that can be replaced by Pinyin in a word : ")
        print(list_multiple_replacement_by_duoyinzi)
        exit()
    else:
        print("success!")
        print("There is no more than one hanzi that can be replaced by Pinyin in a word.")
    print()
        
if __name__ == '__main__':
    IGNONE_PHRASE_PATTERN = "phrase_pattern_including_ignone.txt"
    PHRASE_TABLE = "phrase.txt"
    DIR_PT = "../"

    PHRASE_TABLE_FILE = os.path.join(DIR_PT, PHRASE_TABLE)
    IGNONE_PHRASE_PATTERN_FILE = os.path.join(DIR_PT, IGNONE_PHRASE_PATTERN)

    main(PHRASE_TABLE_FILE, IGNONE_PHRASE_PATTERN_FILE)

