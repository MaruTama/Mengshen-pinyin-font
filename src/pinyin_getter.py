# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
from pypinyin import pinyin, lazy_pinyin, Style
import requests
from bs4 import BeautifulSoup
import path as p


BAIDU_URL  = "https://hanyu.baidu.com/s?wd={}&from=zici"
ZDIC_URL   = "https://www.zdic.net/hans/{}"

MARGED_MAPPING_TABLE = "marged-mapping-table.txt"


NORMAL_PRONUNCIATION = 0


def get_pinyin_with_baidu(hanzi):
    try:
        html = requests.get(BAIDU_URL.format(hanzi))
        soup = BeautifulSoup(html.content, "html.parser")
        elem = soup.find("div", id="pinyin")
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

def get_pinyin_with_zdic(hanzi):
    try:
        html = requests.get(ZDIC_URL.format(hanzi))
        soup = BeautifulSoup(html.content, "html.parser")
        elem = soup.find_all(class_="dicpy")
        text = elem[0].get_text()
        pinyins = text.split(" ")
        return pinyins
    except:
        # print("not found pinyin")
        return None

def get_pinyin_with_pypinyin(hanzi):
    return [p[0] for p in pinyin(hanzi)]


def get_pinyin_table_with_mapping_table():
    pinyin_table = {}
    with open(os.path.join(p.DIR_OUTPUT,MARGED_MAPPING_TABLE)) as read_file:
        for line in read_file:
            str_unicode = line.split(':')[0]
            int_unicode = int(str_unicode[2:], 16)
            hanzi = chr(int_unicode)
            str_pinyins = line.split(' ')[1]
            pinyins = str_pinyins.split(",")
            pinyin_table[hanzi] = pinyins
    return pinyin_table

def get_default_pinyin():
    pass
# U+4E3A: wéi,wèi  # 为
# U+5174: xīng,xìng  # 兴
# U+54BD: yān,yàn,yè,yuān  # 咽
# U+62D3: tuò,tà,zhí  # 拓
# U+6F02: piāo,piào,piǎo,biāo  # 漂
# U+820D: shè,shě,shì  # 舍
# U+957F: cháng,zhǎng  # 长


if __name__ == "__main__":
    _pinyin = get_pinyin_with_baidu("兴兴头头")
    print(_pinyin)

    _pinyin = get_pinyin_with_pypinyin("兴兴头头")
    print(_pinyin)
    
    pinyin_table = get_pinyin_table_with_mapping_table()
    _pinyin = pinyin_table["兴"]
    print(_pinyin)

    _pinyin = get_pinyin_with_zdic("兴兴头头")
    print(_pinyin)
    

