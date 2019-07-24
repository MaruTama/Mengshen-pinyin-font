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
DIR_MT = "./unicode_tables"

# json の名前
PINYIN_JSON = "unicode-pinyin-mapping.json"
DIR_JSN = "./jsons"

# 簡体字
dict_simplified_chinese = {}
# 繁体字
dict_traditional_chinese = {}
# 全体の辞書
dict_hanzi = {"SimplifiedChinese":dict_simplified_chinese, "TraditionalChinese":dict_traditional_chinese}

# テーブルをダウンロードする
def downloadTableTexts():
    # 簡体字
    try:
        with urllib.request.urlopen(url=SIMPLIFIED_FILE_URL) as res:
            data = res.read().decode("utf-8")
            file_ = open(os.path.join(DIR_MT,SIMPLIFIED_FILE_NAME), 'w')
            file_.write(data)
            file_.close()

    except urllib.error.HTTPError as e:
        print("in getSimplifiedChineseMappingTables()")
        if e.code >= 400:
            print(e.reason)
        else:
            raise e

    # 繁体字
    try:
        with urllib.request.urlopen(url=TRADITIONAL_FILE_URL) as res:
            data = res.read().decode("utf-8")
            file_ = open(os.path.join(DIR_MT,TRADITIONAL_FILE_NAME), 'w')
            file_.write(data)
            file_.close()

    except urllib.error.HTTPError as e:
        print("in getTraditionalChineseMappingTables()")
        if e.code >= 400:
            print(e.reason)
        else:
            raise e


# 簡体字の情報取得する
def getSimplifiedChineseMappingTables():

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
    with open(os.path.join(DIR_MT,SIMPLIFIED_FILE_NAME)) as f:
        # 二行分読み飛ばす
        for i in range(2):
            next(f)
        for line in f:
            str_unicode = line.rstrip('\n').split('	')[1]
            int_unicode = int(str_unicode[2:], 16)
            character = chr(int_unicode)
            # 複数の拼音があるときに、他の拼音を入れる
            otherPinyins = [p for p in pinyin(character, heteronym=True)[0] if p != pinyin(character)[0][0]]
            dict_simplified_chinese.update( {str_unicode: {"Character":character, "Pinyin":pinyin(character)[0][0], "OtherPinyins":otherPinyins, "Comment":""}})
            # print("{}: {}: {}: {}".format(str_unicode, character, pinyin(character)[0][0], pinyin(character, heteronym=True)[0]))

    # json 書き出し
    f = open(os.path.join(DIR_JSN,PINYIN_JSON), "w")
    dict_hanzi.update( {"SimplifiedChinese": dict_simplified_chinese} )
    json.dump(dict_hanzi, f, ensure_ascii=False, indent=3, sort_keys=True, separators=(',', ': '))


# 繁体字の情報取得する
def getTraditionalChineseMappingTables():
    # 中身こんな感じ
    '''
    # big5 unicode # 2004/08/12
    0xA1B1 0x00A7
    0xC6D8 0x00A8
    …
    0xA244 0xFFE5
    '''
    # Big5-2003 二行目から開始
    with open(os.path.join(DIR_MT,TRADITIONAL_FILE_NAME)) as f:
        # 一行分読み飛ばす
        next(f)
        for line in f:
            int_unicode = int(line.rstrip('\n').split(' ')[1], 16)
            str_unicode = "U+{:04X}".format(int_unicode)
            character = chr(int_unicode)
            # 複数の拼音があるときに、他の拼音を入れる
            otherPinyins = [p for p in pinyin(character, heteronym=True)[0] if p != pinyin(character)[0][0]]
            dict_traditional_chinese.update( {str_unicode: {"Character":character, "Pinyin":pinyin(character)[0][0], "OtherPinyins":otherPinyins, "Comment":""}})
            # print("{}: {}: {}: {}".format(str_unicode, character, pinyin(character)[0][0], pinyin(character, heteronym=True)[0]))

    # json 書き出し
    f = open(os.path.join(DIR_JSN,PINYIN_JSON), "w")
    dict_hanzi.update( {"TraditionalChinese": dict_traditional_chinese} )
    json.dump(dict_hanzi, f, ensure_ascii=False, indent=3, sort_keys=True, separators=(',', ': '))


# 繁体字 の漢字以外のコードを消すのと足りないpinyinを追加
def deleteWithoutHunzi():
    f = open(os.path.join(DIR_JSN,PINYIN_JSON), 'r')
    json_data = json.load(f)
    # 繁体字 のこの範囲は漢字ではない
    # U+00A7 - U+33D5
    # U+E000 - U+F6B0
    # U+FE30 - U+FFE5

    # 上の範囲を削除する
    for uc in list(json_data["TraditionalChinese"]):
        if "U+00A7" <= uc and uc <= "U+33D5":
            json_data["TraditionalChinese"].pop(uc)
        elif "U+E000" <= uc and uc <= "U+F6B0":
            json_data["TraditionalChinese"].pop(uc)
        elif "U+FE30" <= uc and uc <= "U+FFE5":
            json_data["TraditionalChinese"].pop(uc)

    # 足りないpinyinを追加
    # 兀
    json_data["TraditionalChinese"]["U+FA0C"]["Pinyin"] = "wù"
    # 嗀
    json_data["TraditionalChinese"]["U+FA0D"]["Pinyin"] = "hù"
    json_data["TraditionalChinese"]["U+FA0D"]["OtherPinyins"] = ["huò"]

    f = open(os.path.join(DIR_JSN,PINYIN_JSON), 'w')
    json.dump(json_data, f, ensure_ascii=False, indent=3, sort_keys=True, separators=(',', ': '))


# 足りないピンインを追加する
def setPinyin():
    f = open(os.path.join(DIR_JSN,PINYIN_JSON), 'r')
    json_data = json.load(f)
    # 簡体字
    json_data["SimplifiedChinese"]["U+2B8B8"]["Pinyin"] = "dàn"
    json_data["SimplifiedChinese"]["U+2BAC7"]["Pinyin"] = "ě"
    json_data["SimplifiedChinese"]["U+2BB83"]["Pinyin"] = "shàn"
    json_data["SimplifiedChinese"]["U+2BDF7"]["Pinyin"] = "xīn"
    json_data["SimplifiedChinese"]["U+2BDF7"]["OtherPinyins"] = ["qiàn"]
    json_data["SimplifiedChinese"]["U+2BE29"]["Pinyin"] = "kōu"
    json_data["SimplifiedChinese"]["U+2C029"]["Pinyin"] = "wěi"
    json_data["SimplifiedChinese"]["U+2C02A"]["Pinyin"] = "xiàn"
    json_data["SimplifiedChinese"]["U+2C0A9"]["Pinyin"] = "jiā"
    json_data["SimplifiedChinese"]["U+2C1D5"]["Pinyin"] = "màn"
    json_data["SimplifiedChinese"]["U+2C27C"]["Pinyin"] = "ōu"
    json_data["SimplifiedChinese"]["U+2C27C"]["OtherPinyins"] = ["ǒu"]
    json_data["SimplifiedChinese"]["U+2C288"]["Pinyin"] = "xún"
    json_data["SimplifiedChinese"]["U+2C2A4"]["Pinyin"] = "chǎn"
    json_data["SimplifiedChinese"]["U+2C35B"]["Pinyin"] = "lì"
    json_data["SimplifiedChinese"]["U+2C488"]["Pinyin"] = "hú"
    json_data["SimplifiedChinese"]["U+2C488"]["OtherPinyins"] = ["què"]
    json_data["SimplifiedChinese"]["U+2C542"]["Pinyin"] = "gōng"
    json_data["SimplifiedChinese"]["U+2C613"]["Pinyin"] = "xún"
    json_data["SimplifiedChinese"]["U+2C618"]["Pinyin"] = "dǎn"
    json_data["SimplifiedChinese"]["U+2C621"]["Pinyin"] = "yīn"
    json_data["SimplifiedChinese"]["U+2C62C"]["Pinyin"] = "qiàn"
    json_data["SimplifiedChinese"]["U+2C62D"]["Pinyin"] = "chēn"
    json_data["SimplifiedChinese"]["U+2C64A"]["Pinyin"] = "mò"
    json_data["SimplifiedChinese"]["U+2C64B"]["Pinyin"] = "xiāng"
    json_data["SimplifiedChinese"]["U+2C79F"]["Pinyin"] = "pín"
    json_data["SimplifiedChinese"]["U+2C7C1"]["Pinyin"] = "yì"
    json_data["SimplifiedChinese"]["U+2C7FD"]["Pinyin"] = "dōng"
    json_data["SimplifiedChinese"]["U+2C8D9"]["Pinyin"] = "xū"
    json_data["SimplifiedChinese"]["U+2C8DE"]["Pinyin"] = "zhǔ"
    json_data["SimplifiedChinese"]["U+2C90A"]["Pinyin"] = "shì"
    json_data["SimplifiedChinese"]["U+2CA02"]["Pinyin"] = "qí"
    json_data["SimplifiedChinese"]["U+2CA0E"]["Pinyin"] = "yóu"
    json_data["SimplifiedChinese"]["U+2CA7D"]["Pinyin"] = "xún"
    json_data["SimplifiedChinese"]["U+2CAA9"]["Pinyin"] = "nóng"
    json_data["SimplifiedChinese"]["U+2CB2D"]["Pinyin"] = "lún"
    json_data["SimplifiedChinese"]["U+2CB2E"]["Pinyin"] = "chǎng"
    json_data["SimplifiedChinese"]["U+2CB38"]["Pinyin"] = "shù"
    json_data["SimplifiedChinese"]["U+2CB3B"]["Pinyin"] = "lú"
    json_data["SimplifiedChinese"]["U+2CB3F"]["Pinyin"] = "zhāo"
    json_data["SimplifiedChinese"]["U+2CB41"]["Pinyin"] = "mǔ"
    json_data["SimplifiedChinese"]["U+2CB4A"]["Pinyin"] = "dù"
    json_data["SimplifiedChinese"]["U+2CB4E"]["Pinyin"] = "hóng"
    json_data["SimplifiedChinese"]["U+2CB5A"]["Pinyin"] = "chún"
    json_data["SimplifiedChinese"]["U+2CB5B"]["Pinyin"] = "bō"
    json_data["SimplifiedChinese"]["U+2CB64"]["Pinyin"] = "hóu"
    json_data["SimplifiedChinese"]["U+2CB69"]["Pinyin"] = "wēng"
    json_data["SimplifiedChinese"]["U+2CB73"]["Pinyin"] = "xǐ"
    json_data["SimplifiedChinese"]["U+2CB76"]["Pinyin"] = "hēi"
    json_data["SimplifiedChinese"]["U+2CB78"]["Pinyin"] = "ín"
    json_data["SimplifiedChinese"]["U+2CB7C"]["Pinyin"] = "suì"
    json_data["SimplifiedChinese"]["U+2CBB1"]["Pinyin"] = "yīn"
    json_data["SimplifiedChinese"]["U+2CBC0"]["Pinyin"] = "jī"
    json_data["SimplifiedChinese"]["U+2CBCE"]["Pinyin"] = "tuí"
    json_data["SimplifiedChinese"]["U+2CC56"]["Pinyin"] = "dí"
    json_data["SimplifiedChinese"]["U+2CC5F"]["Pinyin"] = "wěi"
    json_data["SimplifiedChinese"]["U+2CCF5"]["Pinyin"] = "pī"
    json_data["SimplifiedChinese"]["U+2CCF6"]["Pinyin"] = "jiǒng"
    json_data["SimplifiedChinese"]["U+2CCFD"]["Pinyin"] = "shēn"
    json_data["SimplifiedChinese"]["U+2CD0A"]["Pinyin"] = "lín"
    json_data["SimplifiedChinese"]["U+2CD8D"]["Pinyin"] = "tuó"
    json_data["SimplifiedChinese"]["U+2CD8F"]["Pinyin"] = "wéi"
    json_data["SimplifiedChinese"]["U+2CDA8"]["Pinyin"] = "jì"
    json_data["SimplifiedChinese"]["U+2CDAD"]["Pinyin"] = "jì"
    json_data["SimplifiedChinese"]["U+2CE1A"]["Pinyin"] = "yuè"
    json_data["SimplifiedChinese"]["U+2CE23"]["Pinyin"] = "xuān"
    json_data["SimplifiedChinese"]["U+2CE26"]["Pinyin"] = "zhuó"
    json_data["SimplifiedChinese"]["U+2CE2A"]["Pinyin"] = "fán"
    json_data["SimplifiedChinese"]["U+2CE88"]["Pinyin"] = "yǐ"
    json_data["SimplifiedChinese"]["U+2BB5F"]["Pinyin"] = "ōu"
    json_data["SimplifiedChinese"]["U+2BB5F"]["OtherPinyins"] = ["qū"]
    json_data["SimplifiedChinese"]["U+2BB62"]["Pinyin"] = "lǔn"
    json_data["SimplifiedChinese"]["U+2BB7C"]["Pinyin"] = "láo"
    json_data["SimplifiedChinese"]["U+2BC1B"]["Pinyin"] = "xíng"
    json_data["SimplifiedChinese"]["U+2BD77"]["Pinyin"] = "lì"
    json_data["SimplifiedChinese"]["U+2BD87"]["Pinyin"] = "dié"
    json_data["SimplifiedChinese"]["U+2BD87"]["OtherPinyins"] = ["dì"]
    json_data["SimplifiedChinese"]["U+2C0CA"]["Pinyin"] = "zhì"
    json_data["SimplifiedChinese"]["U+2C1D9"]["Pinyin"] = "pèi"
    json_data["SimplifiedChinese"]["U+2C1F9"]["Pinyin"] = "guó"
    json_data["SimplifiedChinese"]["U+2C317"]["Pinyin"] = "hé"
    json_data["SimplifiedChinese"]["U+2C361"]["Pinyin"] = "dàng"
    json_data["SimplifiedChinese"]["U+2C364"]["Pinyin"] = "xún"
    json_data["SimplifiedChinese"]["U+2C494"]["Pinyin"] = "gěng"
    json_data["SimplifiedChinese"]["U+2C497"]["Pinyin"] = "lởm"
    json_data["SimplifiedChinese"]["U+2C629"]["Pinyin"] = "tīng"
    json_data["SimplifiedChinese"]["U+2C62B"]["Pinyin"] = "huán"
    json_data["SimplifiedChinese"]["U+2C62B"]["OtherPinyins"] = ["huàn","wàn"]
    json_data["SimplifiedChinese"]["U+2C62F"]["Pinyin"] = "zhǔn"
    json_data["SimplifiedChinese"]["U+2C62F"]["OtherPinyins"] = ["zhùn"]
    json_data["SimplifiedChinese"]["U+2C642"]["Pinyin"] = "yǎn"
    json_data["SimplifiedChinese"]["U+2C642"]["OtherPinyins"] = ["yǐn"]
    json_data["SimplifiedChinese"]["U+2C72C"]["Pinyin"] = "màn"
    json_data["SimplifiedChinese"]["U+2C72F"]["Pinyin"] = "mán"
    json_data["SimplifiedChinese"]["U+2C8E1"]["Pinyin"] = "jiàn"
    json_data["SimplifiedChinese"]["U+2C8F3"]["Pinyin"] = "hěn"
    json_data["SimplifiedChinese"]["U+2C907"]["Pinyin"] = "yīn"
    json_data["SimplifiedChinese"]["U+2C91D"]["Pinyin"] = "huì"
    json_data["SimplifiedChinese"]["U+2CB29"]["Pinyin"] = "yì"
    json_data["SimplifiedChinese"]["U+2CB31"]["Pinyin"] = "jīn"
    json_data["SimplifiedChinese"]["U+2CB31"]["OtherPinyins"] = ["yǐn","yín"]
    json_data["SimplifiedChinese"]["U+2CB39"]["Pinyin"] = "huán"
    json_data["SimplifiedChinese"]["U+2CB39"]["OtherPinyins"] = ["shén","shēn"]
    json_data["SimplifiedChinese"]["U+2CB6C"]["Pinyin"] = "wèi"
    json_data["SimplifiedChinese"]["U+2CB6F"]["Pinyin"] = "piě"
    json_data["SimplifiedChinese"]["U+2CBBF"]["Pinyin"] = "gāi"
    json_data["SimplifiedChinese"]["U+2CBBF"]["OtherPinyins"] = ["ái","qí­"]
    json_data["SimplifiedChinese"]["U+2CCFF"]["Pinyin"] = "tú"
    json_data["SimplifiedChinese"]["U+2CD02"]["Pinyin"] = "fēi"
    json_data["SimplifiedChinese"]["U+2CD03"]["Pinyin"] = "huō"
    json_data["SimplifiedChinese"]["U+2CD8B"]["Pinyin"] = "jū"
    json_data["SimplifiedChinese"]["U+2CD8B"]["OtherPinyins"] = ["qú","gǒu"]
    json_data["SimplifiedChinese"]["U+2CD90"]["Pinyin"] = "zhào"
    json_data["SimplifiedChinese"]["U+2CD9F"]["Pinyin"] = "là"
    json_data["SimplifiedChinese"]["U+2CDA0"]["Pinyin"] = "liàn"
    json_data["SimplifiedChinese"]["U+2CDAE"]["Pinyin"] = "xǐ"
    json_data["SimplifiedChinese"]["U+2CDAE"]["OtherPinyins"] = "xī"
    json_data["SimplifiedChinese"]["U+2CDD5"]["Pinyin"] = "bū"
    json_data["SimplifiedChinese"]["U+2CDD5"]["OtherPinyins"] = ["pū","pú","bǔ"]
    json_data["SimplifiedChinese"]["U+2CE18"]["Pinyin"] = "yǎn"
    json_data["SimplifiedChinese"]["U+2CE7C"]["Pinyin"] = "xiè"
    json_data["SimplifiedChinese"]["U+2CE93"]["Pinyin"] = "chǔ"

    # 繁体字
    json_data["TraditionalChinese"]["U+5159"]["Pinyin"] = "shí"
    json_data["TraditionalChinese"]["U+5159"]["OtherPinyins"] = ["kè"]
    json_data["TraditionalChinese"]["U+5161"]["Pinyin"] = "bǎi"
    json_data["TraditionalChinese"]["U+5161"]["OtherPinyins"] = ["kè"]
    json_data["TraditionalChinese"]["U+55E7"]["Pinyin"] = "jiālún"

    f = open(os.path.join(DIR_JSN,PINYIN_JSON), 'w')
    json.dump(json_data, f, ensure_ascii=False, indent=3, sort_keys=True, separators=(',', ': '))

# 漢字以外のコードを消すのと足りないpinyinを追加
def createUnicodeJson():
    downloadTableTexts()
    getSimplifiedChineseMappingTables()
    getTraditionalChineseMappingTables()
    deleteWithoutHunzi()
    setPinyin()

if __name__ == '__main__':
    createUnicodeJson()
