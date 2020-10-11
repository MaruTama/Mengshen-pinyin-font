#!/usr/bin/env python

# 通用规范汉字表 Big5-2003 から必要な文字コードを生成する

# Reference
# [PythonでUnicodeコードポイントと文字を相互変換（chr, ord, \x, \u, \U）](https://note.nkmk.me/python-chr-ord-unicode-code-point/)
# [[python] JSONファイルのフォーマットを整えてDumpする](https://qiita.com/Hyperion13fleet/items/7129623ab32bdcc6e203)
import urllib.request, urllib.error
import os
import json
from pypinyin import pinyin, lazy_pinyin, Style

# マッピングテーブルを取得する
# 簡体字
SIMPLIFIED_FILE_URL  = "http://hanzidb.org/TGSCC-Unicode.txt"
SIMPLIFIED_FILE_NAME = os.path.basename(SIMPLIFIED_FILE_URL)
# 繁体字
TRADITIONAL_FILE_URL  = "https://moztw.org/docs/big5/table/big5_2003-u2b.txt"
TRADITIONAL_FILE_NAME = os.path.basename(TRADITIONAL_FILE_URL)
DIR_MT = "../../download_unicode_tables"

# table の名前
TGSCC_MAPPING_TABLE     = "TGSCC-mapping-table.txt"
BIG5_MAPPING_TABLE      = "BIG5-mapping-table.txt"
OVERWRITE_MAPPING_TABLE = "overwrite.txt"
MARGED_MAPPING_TABLE    = "marged-mapping-table.txt"
DIR_OT = "../../../outputs"

# テーブルをダウンロードする
def download_table_texts():
    # 簡体字
    try:
        with urllib.request.urlopen(url=SIMPLIFIED_FILE_URL) as res:
            data = res.read().decode("utf-8")
            file_ = open(os.path.join(DIR_MT,SIMPLIFIED_FILE_NAME), mode='w', encoding='utf-8')
            file_.write(data)
            file_.close()

    except urllib.error.HTTPError as e:
        print("in get_simplified_chinese_mapping_tables()")
        if e.code >= 400:
            print(e.reason)
        else:
            raise e

    # 繁体字
    try:
        with urllib.request.urlopen(url=TRADITIONAL_FILE_URL) as res:
            data = res.read().decode("utf-8")
            file_ = open(os.path.join(DIR_MT,TRADITIONAL_FILE_NAME), mode='w', encoding='utf-8')
            file_.write(data)
            file_.close()

    except urllib.error.HTTPError as e:
        print("in get_traditional_chinese_mapping_tables()")
        if e.code >= 400:
            print(e.reason)
        else:
            raise e


# 簡体字の情報取得する
def get_simplified_chinese_mapping_tables():
    unicode_table = []
    # 中身こんな感じ
    '''
    # Table of General Standard Chinese Characters mapped to Unicode
    index number	codepoint
    1	U+4E00
    2	U+4E59
    …
    8105	U+883C
    '''
    # 通用规范汉字表　三行目から開始
    with open(os.path.join(DIR_MT,SIMPLIFIED_FILE_NAME), mode='r', encoding='utf-8') as read_file:
        # 二行分読み飛ばす
        for i in range(2):
            next(read_file)
        for line in read_file:
            str_unicode = line.rstrip('\n').split('	')[1]
            int_unicode = int(str_unicode[2:], 16)
            unicode_table.append(int_unicode)

    unicode_table.sort()
    with open(TGSCC_MAPPING_TABLE, mode='w', encoding='utf-8') as write_file:
        for _unicode in unicode_table:
            character = chr(_unicode)
            str_pinyins = ""
            pinyin_list = pinyin(character, heteronym=True)[0]
            for p in pinyin_list:
                str_pinyins += "{},".format(p) if p != pinyin_list[-1] else p
            write_file.write("U+{:X}: {}  #{}\n".format(_unicode, str_pinyins, character))


# 繁体字の情報取得する
def get_traditional_chinese_mapping_tables():
    unicode_table = []
    # 中身こんな感じ
    '''
    # big5 unicode # 2004/08/12
    0xA1B1 0x00A7
    0xC6D8 0x00A8
    …
    0xA244 0xFFE5
    '''
    # Big5-2003 二行目から開始
    with open(os.path.join(DIR_MT,TRADITIONAL_FILE_NAME), mode='r', encoding='utf-8') as read_file:
        # 一行分読み飛ばす
        next(read_file)
        for line in read_file:
            int_unicode = int(line.rstrip('\n').split(' ')[1], 16)
            unicode_table.append(int_unicode)

    unicode_table.sort()
    unicode_table = deleteWithoutHunzi4big5(unicode_table)

    with open(BIG5_MAPPING_TABLE, mode='w', encoding='utf-8') as write_file:
        for _unicode in unicode_table:
            character = chr(_unicode)
            str_pinyins = ""
            pinyin_list = pinyin(character, heteronym=True)[0]
            for p in pinyin_list:
                str_pinyins += "{},".format(p) if p != pinyin_list[-1] else p
            write_file.write("U+{:X}: {}  #{}\n".format(_unicode, str_pinyins, character))


# 繁体字 の漢字以外のコードを消す
def deleteWithoutHunzi4big5(unicode_table):
    _unicode_table = unicode_table.copy()
    # 繁体字 のこの範囲は漢字以外の文字なので削除する
    # U+00A7 - U+33D5 英字、記号、ひらがな等
    # U+E000 - U+F6B0 私用領域
    # U+FE30 - U+FE4F CJK互換形(縦書き用記号グリフ)
    # U+FF00 - U+FFE5 半角・全角形(Halfwidth and Fullwidth Forms)
    for uc in unicode_table:
        if int("00A7", 16) <= uc and uc <= int("33D5", 16):
            _unicode_table.remove(uc)
        elif int("E000", 16) <= uc and uc <= int("F6B0", 16):
            _unicode_table.remove(uc)
        elif int("FE30", 16) <= uc and uc <= int("FFE5", 16):
            _unicode_table.remove(uc)

    return _unicode_table

# TGSCC-mapping-table.txt と BIG5-mapping-table.txt を統合する
def marge_mapping_table():
    marged_mapping_table = {}
    unicode_list_for_sort = []

    # 簡体字
    with open(TGSCC_MAPPING_TABLE, mode='r', encoding='utf-8') as read_file:
        for line in read_file:
            # "U+4ECD" -> "4ECD" -> 20173　ソートのために文字列から数値にする
            str_unicode = line.rstrip('\n').split(':')[0]
            int_unicode =  int(str_unicode[2:], 16)
            unicode_list_for_sort.append(int_unicode)
            marged_mapping_table.update( {int_unicode: line} )
    # 繁体字
    with open(BIG5_MAPPING_TABLE, mode='r', encoding='utf-8') as read_file:
        for line in read_file:
            str_unicode = line.rstrip('\n').split(':')[0]
            int_unicode =  int(str_unicode[2:], 16)
            unicode_list_for_sort.append(int_unicode)
            marged_mapping_table.update( {int_unicode: line} )

    # 重複を削除
    unicode_list_for_sort = list(set(unicode_list_for_sort))
    unicode_list_for_sort.sort()

    with open(os.path.join(DIR_OT, MARGED_MAPPING_TABLE), mode='w', encoding='utf-8') as write_file:
        for int_unicode in unicode_list_for_sort:
            write_file.write(marged_mapping_table[int_unicode])

# pinyin を上書きする（pypinyin で変換できなかったもの誤っているものの修正）
def overwrite_pinyin():
    marged_mapping_table = {}
    unicode_list_for_sort = []
    header = ""

    with open(os.path.join(DIR_OT, MARGED_MAPPING_TABLE), mode='r', encoding='utf-8') as read_file:
        for line in read_file:
            # "U+4ECD" -> "4ECD" -> 20173　ソートのために文字列から数値にする
            str_unicode = line.rstrip('\n').split(':')[0]
            int_unicode =  int(str_unicode[2:], 16)
            unicode_list_for_sort.append(int_unicode)
            marged_mapping_table.update( {int_unicode: line} )

    with open(OVERWRITE_MAPPING_TABLE, mode='r', encoding='utf-8') as read_file:
        # 3行分読み飛ばす
        for i in range(3):
            header += read_file.readline()
        for line in read_file:
            str_unicode = line.rstrip('\n').split(':')[0]
            int_unicode =  int(str_unicode[2:], 16)
            unicode_list_for_sort.append(int_unicode)
            marged_mapping_table.update( {int_unicode: line} )

    # 重複を削除
    unicode_list_for_sort = list(set(unicode_list_for_sort))
    unicode_list_for_sort.sort()

    with open(os.path.join(DIR_OT, MARGED_MAPPING_TABLE), mode='w', encoding='utf-8') as write_file:
        for int_unicode in unicode_list_for_sort:
            write_file.write(marged_mapping_table[int_unicode])


# 漢字以外のコードを消すのと足りないpinyinを追加
def create_unicode_pinyin_table():
    # download_table_texts()
    get_simplified_chinese_mapping_tables()
    get_traditional_chinese_mapping_tables()
    marge_mapping_table()
    overwrite_pinyin()

if __name__ == '__main__':
    create_unicode_pinyin_table()
