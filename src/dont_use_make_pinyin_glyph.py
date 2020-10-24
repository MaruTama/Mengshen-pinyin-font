# -*- coding: utf-8 -*-
#!/usr/bin/env python

# python3 make_pinyin_glyph.py

import os
import orjson
import pinyin_getter as pg
import subprocess
import shell
import pinyin_glyph as py_glyph

# テスト用のフォントクラス（ピンイングリフが生成できるか確認するため）
class Font():
    def __init__(self, TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON):

        self.TAMPLATE_JSON = "./tmp/json/template.json"

        with open(TAMPLATE_MAIN_JSON, mode='rb') as read_file:
            self.marged_font = orjson.loads(read_file.read())
        with open(ALPHABET_FOR_PINYIN_JSON, mode='rb') as read_file:
            self.pinyin_glyf = orjson.loads(read_file.read())
        self.cmap_table = self.marged_font["cmap"]
        self.pinyin_mapping_table = pg.get_pinyin_table_with_mapping_table()

    # とりあえず、ピンインだけ追加
    def add_glyph_order(self):
        # ピンインのグリフを追加 
        set_glyph_order = set(self.marged_font["glyph_order"]) | set(self.pinyin_glyf.keys())
        new_glyph_order = list(set_glyph_order)
        new_glyph_order.sort()
        self.marged_font["glyph_order"] = new_glyph_order
        # print( len(self.marged_font["glyph_order"]) )

    # とりあえず、ピンインだけ追加
    def add_glyf(self):
        new_glyf = self.marged_font["glyf"]
        new_glyf.update( self.pinyin_glyf )
        self.marged_font["glyf"] = new_glyf
        
        # ss00 - 0n をマージする

    def __save_tamplate_json(self, OUTPUT_JSON):
        with open(OUTPUT_JSON, "wb") as write_file:
            serialized_glyf = orjson.dumps(self.marged_font, option=orjson.OPT_INDENT_2)
            write_file.write(serialized_glyf)

    def build(self):
        self.add_glyph_order()
        self.add_glyf()
        self.__save_tamplate_json( self.TAMPLATE_JSON )
        self.convert_json2otf( self.TAMPLATE_JSON, "./pinyin_sample.otf" )

    def convert_json2otf(self, template_json, output_font):
        cmd = "otfccbuild {} -o {}".format(template_json, output_font)
        print(cmd)
        shell.process(cmd)


if __name__ == "__main__":
    DIR_OUTPUT = "./outputs/"
    DIR_JSON   = "./res/fonts/"
    DIR_TMP    = "./tmp/json"

    ALPHABET_FOR_PINYIN_JSON = os.path.join(DIR_JSON, "alphabet4pinyin.json")
    TAMPLATE_MAIN_JSON       = os.path.join(DIR_TMP, "template_main.json")
    TAMPLATE_GLYF_JSON       = os.path.join(DIR_TMP, "template_glyf.json")

    # build の前に ALPHABET_FOR_PINYIN_JSON に発音を入れる
    pinyin_glyph = py_glyph.PinyinGlyph(TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON)
    pinyin_glyph.add_pronunciations_to_glyf_table()
    
    OUTPUT_JSON = "./tmp/json/template.json"
    pinyin_glyph.save(OUTPUT_JSON)

    font = Font(TAMPLATE_MAIN_JSON, OUTPUT_JSON)
    # font = Font(TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON)
    # # glyf に追加するpinyin の種類は、mapping_table に完全に依存する
    font.build()
