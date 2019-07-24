import os
import json
import glob

# 使ってない漢字以外削除する

# 中国語に使う漢字の一覧
PINYIN_JSON = "unicode-pinyin-mapping.json"
# マッピングテーブル
UNICODE_TO_CID_JSON = "unicode-cid-mapping.json"

# 漢字のSVGがあるディレクトリ
DIR_SVG = "./fonts/SVGs"
# 設定ファイルjsonのあるディレクトリ
DIR_JSN = "./jsons"


if __name__ == '__main__':
    files = glob.glob(os.path.join(DIR_SVG,"*"))
    # 全てのファイル名のセットを作る
    file_names = {os.path.basename(file) for file in files}

    # # unicode -> cid の変換をするため
    f = open(os.path.join(DIR_JSN,UNICODE_TO_CID_JSON), 'r')
    dict_unicode2cid = json.load(f)
    # 中国語の漢字情報の一覧を取得する
    f = open(os.path.join(DIR_JSN,PINYIN_JSON), 'r')
    dict_pinyin_unicode = json.load(f)

    for unicode in dict_unicode2cid:
        # 中国語の漢字であるとき
        if unicode in dict_pinyin_unicode["SimplifiedChinese"] or \
            unicode in dict_pinyin_unicode["TraditionalChinese"]:
            try:
                file_names.remove("{}.svg".format(dict_unicode2cid[unicode]))
            except Exception as e:
                pass

    # 漢字以外のファイルを消す
    for file_name in file_names:
        try:
            print(file_name)
            os.remove(os.path.join(DIR_SVG,file_name))
        except Exception as e:
            pass
