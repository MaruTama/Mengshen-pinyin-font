import os
import sys
import argparse
import json
import glob

# 使ってない漢字以外削除する

def parse_args(args):
    def transform_list(arg):
        try:
            return [float(n) for n in split(arg)]
        except ValueError:
            msg = "Invalid transformation matrix: %r" % arg
            raise argparse.ArgumentTypeError(msg)

    parser = argparse.ArgumentParser(
        description="This Script is ")
    parser.add_argument(
        "dir_svg", metavar="DIRECTORY_OF_SVG", help="Input folder containing SVG file ")
    parser.add_argument(
        "unicode2cid_json", metavar="unicode-cid-mapping.json",
        help="Json of unicode and cid mapping table")
    parser.add_argument(
        "unicode_of_hanzi_json", metavar="unicode-pinyin-mapping.json",
        help="Json of hanzi and pinyin mapping table")
    return parser.parse_args(args)


def main(args=None):

    options = parse_args(args)

    DIR_SVG = options.dir_svg
    # マッピングテーブル
    UNICODE_TO_CID_JSON = options.unicode2cid_json
    # 中国語に使う漢字の一覧
    PINYIN_JSON = options.unicode_of_hanzi_json


    files = glob.glob(os.path.join(DIR_SVG,"*"))
    # 全てのファイル名のセットを作る
    file_names = {os.path.basename(file) for file in files}

    # unicode -> cid の変換をするため
    f = open(UNICODE_TO_CID_JSON, 'r')
    dict_unicode2cid = json.load(f)
    # 中国語の漢字情報の一覧を取得する
    f = open(PINYIN_JSON, 'r')
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


if __name__ == "__main__":
    sys.exit(main())
