#!/usr/bin/env python

# https://dokochina.com/duoyinzi.htm
# 漢字、拼音と多音字の単語を渡して、百度汉字とpypinyin を比較する
# python3 createduoyinziJson.py 重 chóng 重版,重婚,重孙,重围,重霄 


# 基本的な方針として、ここで一致していたら三箇所で一致しているので、登録する
from pypinyin import pinyin, lazy_pinyin, Style

import os
import sys
import argparse
import requests
from bs4 import BeautifulSoup
# Webページを取得して解析する

BAIDU_URL  = "https://hanyu.baidu.com/s?wd={}&from=zici"

def get_pinyin(hanzi):
    html = requests.get(BAIDU_URL.format(hanzi))
    soup = BeautifulSoup(html.content, "html.parser")
    elem = soup.find("div", id="pinyin")
    try:
        raw_text = elem.find("b")
        # [ chóng xiāo ] こんな感じの文字列
        text = raw_text.get_text()
        text = text.replace("[ ", "")
        text = text.replace(" ]", "")
        pinyins = text.split(" ")
        # print(pinyins)
        return pinyins
    except:
        # print("not found pinyin")
        return None


def main(args=None):
    parser = argparse.ArgumentParser(description='this script is converting text to hanzi')
    parser.add_argument('hanzi')
    parser.add_argument('pinyin')
    parser.add_argument('texts')
    arg = parser.parse_args(args)

    # print(arg.pinyin)
    # print(arg.texts)

    # [中国語の多音字辞典（Chinese Duoyinzi Dictionary）](https://dokochina.com/duoyinzi.htm) の拼音を入れる
    # 間違っていないか確認するため
    hanzi = arg.hanzi
    input_pinyin  = arg.pinyin
    duoyinzi_list = arg.texts.split(",")
    for duoyinzi in duoyinzi_list:
        # 二通りで検証する
        pinyins1 = pinyin(duoyinzi, heteronym=True)
        # [['tán'], ['cí']] こういう感じなので ['tán', 'cí'] こうする
        pinyins1 = [e[0] for e in pinyins1]
        # print("{}, {}".format(duoyinzi, pinyins1))
        pinyins2 = get_pinyin(duoyinzi)
        # print("{}, {}".format(duoyinzi, pinyins2))

        # python すげえな。これで配列の比較できる
        if pinyins1 == pinyins2:
            str4print = ""
            is_match_input_pinyin = False
            for p in pinyins1:
                str4print += '"{}"'.format(p)
                if not (p == pinyins1[-1]):
                    str4print += ", "
                if input_pinyin == p:
                    is_match_input_pinyin = True
            if is_match_input_pinyin:
                duoyinzi = duoyinzi.replace(hanzi, "*")
                print('{}|'.format(duoyinzi), end="")
            else:
                print("\n\n")
                print("not match")
                print("input_pinyin is {}".format(input_pinyin))
                print("pypintin   : {}, {}".format(duoyinzi, pinyins1))
                print("baidu-hanzi: {}, {}".format(duoyinzi, pinyins2))
        else:
            print("\n\n")
            print()
            print("not match")
            print("pypintin   : {}, {}".format(duoyinzi, pinyins1))
            print("baidu-hanzi: {}, {}".format(duoyinzi, pinyins2))
        # print()

if __name__ == '__main__':
    sys.exit(main())
    