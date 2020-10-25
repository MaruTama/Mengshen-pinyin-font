# -*- coding: utf-8 -*-
#!/usr/bin/env python'

import shell
import orjson
import os
import pinyin_getter as pg
import pinyin_glyph as py_glyph
import utility
import path as p

class Font():
    def __init__(self, TAMPLATE_MAIN_JSON, TAMPLATE_GLYF_JSON, ALPHABET_FOR_PINYIN_JSON, \
                        PATTERN_ONE_TXT, PATTERN_TWO_JSON, EXCEPTION_PATTERN_JSON):
        self.TAMPLATE_MAIN_JSON     = TAMPLATE_MAIN_JSON
        self.TAMPLATE_GLYF_JSON     = TAMPLATE_GLYF_JSON
        self.PATTERN_ONE_TXT        = PATTERN_ONE_TXT
        self.PATTERN_TWO_JSON       = PATTERN_TWO_JSON
        self.EXCEPTION_PATTERN_JSON = EXCEPTION_PATTERN_JSON
        self.load_json()
        self.cmap_table = self.marged_font["cmap"]
        self.PINYIN_MAPPING_TABLE = pg.get_pinyin_table_with_mapping_table()

        # 発音のグリフを作成する
        pinyin_glyph = py_glyph.PinyinGlyph(TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON)
        pinyin_glyph.add_pronunciations_to_glyf_table()
        self.pinyin_glyf = pinyin_glyph.get_pronunciations_to_glyf_table()
        print("発音のグリフを作成完了")

        # 定義が重複している文字に関しては、基本的に同一のグリフが使われているはず
        # どれかがグリフに発音を追加したら無視する。
        # ⺎(U+2E8E) 兀(U+5140) 兀(U+FA0C)
        # 嗀(U+55C0) 嗀(U+FA0D)
        self.duplicate_definition_of_hanzes = {
            str(0x2E8E):0, str(0x5140):0, str(0xFA0C):0,
            str(0x55C0):1, str(0xFA0D):1
        }
        self.is_added_glyf = [False, False]

    def get_has_multiple_pinyin_hanzi(self):
        return [(ord(hanzi), pinyins) for hanzi, pinyins in self.PINYIN_MAPPING_TABLE.items() if 1 < len(pinyins)]

    def get_advance_size_of_hanzi(self):
        # なんでもいいが、とりあえず漢字の「一」でサイズを取得する
        cid = self.marged_font["cmap"][str(ord("一"))]
        advanceWidth   = self.marged_font["glyf"][cid]["advanceWidth"]
        advanceHeight  = self.marged_font["glyf"][cid]["advanceHeight"]
        verticalOrigin = self.marged_font["glyf"][cid]["verticalOrigin"]
        return (advanceWidth, advanceHeight, verticalOrigin)

    # GSUB の置換と cmap_uvs の置換はどっちが後？
    def add_cmap_uvs(self):
        IVS = 0xE01E0 #917984
        """
        e.g.: 
        "19981 917984": "uni4E0D",      => 標準的なピンイン
        "19981 917985": "uni4E0D.ss00", => ピンインのないグリフ
        "19981 917986": "uni4E0D.ss01", => 以降、異読のピンイン
        "19981 917987": "uni4E0D.ss02",
        ...
        """

        for (hanzi, pinyins) in self.PINYIN_MAPPING_TABLE.items():
            str_unicode = str(ord(hanzi))
            if not (str_unicode in self.cmap_table):
                raise Exception("グリフが見つかりません.\n  unicode: {}".format(str_unicode))
            cid = self.cmap_table[str_unicode]
            offset = 1
            self.marged_font["cmap_uvs"]["{0} {1}".format(str_unicode, IVS)         ] = cid
            self.marged_font["cmap_uvs"]["{0} {1}".format(str_unicode, IVS + offset)] = "{}.ss00".format(cid)
            for i in range( offset, len(pinyins) ):
                self.marged_font["cmap_uvs"]["{0} {1}".format(str_unicode, IVS + offset + i)] = "{}.ss{:02}".format(cid, i)

    def add_glyph_order(self):
        """
        e.g.: 
        "glyph_order": [
            ...
            "uni4E0D","uni4E0D.ss00","uni4E0D.ss01","uni4E0D.ss02","uni4E0D.ss03",
            ...
        ]
        """
        # 異読の漢字グリフ追加
        set_glyph_order = set(self.marged_font["glyph_order"])
        for (ucode, pinyins) in self.get_has_multiple_pinyin_hanzi():
            str_unicode = str(ucode)
            if not (str_unicode in self.cmap_table):
                raise Exception("グリフが見つかりません.\n  unicode: {}".format(str_unicode))
            for i in range(len(pinyins)):
                cid = self.cmap_table[str_unicode]
                set_glyph_order.add("{}.ss{:02}".format(cid, i))
        
        # ピンインのグリフを追加
        set_glyph_order = set_glyph_order | set(self.pinyin_glyf.keys())
        new_glyph_order = list(set_glyph_order)
        new_glyph_order.sort()
        self.marged_font["glyph_order"] = new_glyph_order
        # print(self.marged_font["glyph_order"])
    
    def generate_hanzi_glyf_with_pinyin(self, cid, pronunciation):
        (advanceWidth, advanceHeight, verticalOrigin) = self.get_advance_size_of_hanzi()
        simpled_pronunciation = utility.simplification_pronunciation( pronunciation )
        hanzi_glyf = {
                         "advanceWidth": advanceWidth,
                         "advanceHeight": advanceHeight,
                         "verticalOrigin": verticalOrigin,
                         "references": [
                             {"glyph":"arranged_{}".format(simpled_pronunciation),"x":0, "y":0, "a":1, "b":0, "c":0, "d":1},
                             {"glyph":"{}.ss00".format(cid),                      "x":0, "y":0, "a":1, "b":0, "c":0, "d":1}
                         ]
                     }
        return hanzi_glyf
    
    # unicode 上に定義が重複している漢字があるとエラーになるので判定を入れる
    # Exception: otfccbuild : Build : [WARNING] [Stat] Circular glyph reference found in gid 11663 to gid 11664. The reference will be dropped.
    def is_added_glyf_4_duplicate_definition_of_hanzi(self, str_unicode):
        duplicate_definition_of_hanzes = [str_unicode for str_unicode, _ in self.duplicate_definition_of_hanzes.items()]
        if str_unicode in duplicate_definition_of_hanzes:
            idx = self.duplicate_definition_of_hanzes[str_unicode]
            return self.is_added_glyf[idx]
        return False

    def update_status_is_added_glyf_4_duplicate_definition_of_hanzi(self, str_unicode):
        duplicate_definition_of_hanzes = [str_unicode for str_unicode, _ in self.duplicate_definition_of_hanzes.items()]
        if str_unicode in duplicate_definition_of_hanzes:
            idx = self.duplicate_definition_of_hanzes[str_unicode]
            self.is_added_glyf[idx] = True
                
    def add_glyf(self):
        """
        e.g.: 
        uni4E0D　　　　標準の読みの拼音
        uni4E0D.ss00　無印のグリフ。設定を変更するだけで拼音を変更できる。
        uni4E0D.ss01　以降、異読
        uni4E0D.ss02　
        """
        """
        Sawarabi
        "uni4E00": {
            "advanceWidth": 1000,
            "advanceHeight": 1000,
            "verticalOrigin": 952,
        """
        # e.g.:
        # uni4E00 -> uni4E00.ss00
        # uni4E00 = uni4E00.ss00 + normal pronunciation
        # if uni4E00 has variational pronunciation
        # uni4E00.ss01 = uni4E00.ss00 + variational pronunciation
        for (hanzi, pinyins) in self.PINYIN_MAPPING_TABLE.items():
            str_unicode = str(ord(hanzi))
            if not (str_unicode in self.cmap_table):
                raise Exception("グリフが見つかりません.\n  unicode: {}".format(str_unicode))
            if self.is_added_glyf_4_duplicate_definition_of_hanzi(str_unicode):
                continue
            cid = self.cmap_table[str_unicode]
            glyf_data = self.font_glyf_table[cid]
            # hanzi_glyf -> hanzi_glyf.ss00
            self.font_glyf_table.update( { "{}.ss00".format(cid) : glyf_data } )
            # hanzi_glyf = hanzi_glyf.ss00 + normal pronunciation
            normal_pronunciation = pinyins[pg.NORMAL_PRONUNCIATION]
            glyf_data = self.generate_hanzi_glyf_with_pinyin(cid, normal_pronunciation)
            self.font_glyf_table.update( { cid : glyf_data } )
            # if hanzi_glyf has variational pronunciation
            # hanzi_glyf.ss01 = hanzi_glyf.ss00 + variational pronunciation
            for i in range( 1,len(pinyins) ):
                variational_pronunciation = pinyins[i]
                glyf_data = self.generate_hanzi_glyf_with_pinyin(cid, variational_pronunciation)
                self.font_glyf_table.update( { "{}.ss{:02}".format(cid, i) : glyf_data } )
            self.update_status_is_added_glyf_4_duplicate_definition_of_hanzi(str_unicode)


        new_glyf = self.marged_font["glyf"]
        new_glyf.update( self.pinyin_glyf )
        new_glyf.update( self.font_glyf_table )
        self.marged_font["glyf"] = new_glyf


    # 代替文字の指定、置換条件の指定
    def add_GSUB(self):
        self.PATTERN_ONE_TXT
        self.PATTERN_TWO_JSON
        self.EXCEPTION_PATTERN_JSON

        # lookups の aalt
        # aalt_0 は拼音が一つのみの漢字 + 記号とか。置き換え対象が一つのみのとき
        # aalt_1 は拼音が複数の漢字
        """
        e.g.:
        "lookups": {
            "lookup_aalt_0": {
                "type": "gsub_single",
                "flags": {},
                "subtables": [
                    {   
                        ...
                        "uni4E01": "uni4E01.ss00",
                        "uni4E03": "uni4E03.ss00",
                        "uni4E08": "uni4E08.ss00",
                        ...
                    }
                ]
            },
            "lookup_aalt_1": {
                "type": "gsub_alternate",
                "flags": {},
                "subtables": [
                    {
                        "uni4E00": [
                            "uni4E00.ss00",
                            "uni4E00.ss01",
                            "uni4E00.ss02"
                        ],
                        "uni4E07": [
                            "uni4E07.ss00",
                            "uni4E07.ss01"
                        ],
                        ...
                    }
                ]
            }
        }
        """
        self.marged_font["GSUB"]["lookups"]
        

        # lookups の catl
        """
        lookup calt0 {
            sub [uni4E0D uni9280] uni884C' lookup lookup_0 ;
        } calt0;
        """
        """
        "lookups": {
            "lookup_calt_0": {
                "type": "gsub_chaining",
                "flags": {},
                "subtables": [
                    {
                        "match": [
                            ["uni4E0D","uni9280"],
                            ["uni884C"]
                        ],
                        "apply": [
                            {
                                "at": 1,
                                "lookup": "lookup_11_3"
                            }
                        ],
                        "inputBegins": 1,
                        "inputEnds": 2
                    }
                ]
            },
            ...
        }
        """

        # lookup order
        """
        "lookupOrder": [
            "lookup_calt_0",
            "lookup_calt_1",
            "lookup_ccmp_2",
            "lookup_11_3"
        ]
        """

        # 文字体系 ごとに使用する feature を指定する
        # 'hani' = CJK (中国語/日本語/韓国語)
        # 'kana' = ひらがな/カタカナ -> 使わない
        """
        "languages": {
            "DFLT_DFLT": {
                "features": [
                    "aalt_00000",
                    "ccmp_00007",
                ]
            },
            "hani_DFLT": {
                "features": [
                    "aalt_00003",
                    "ccmp_00010",
                ]
            },
            ...
        }
        """

        # feature ごとに使用する lookup table を指定する
        """
        "features": {
            "aalt_00000": [
                "lookup_aalt_0",
                "lookup_aalt_1"
            ],
            ...
        }
        """
        pass

    def load_json(self):
        with open(self.TAMPLATE_MAIN_JSON, "rb") as read_file:
            self.marged_font = orjson.loads(read_file.read())
        with open(self.TAMPLATE_GLYF_JSON, "rb") as read_file:
            self.font_glyf_table = orjson.loads(read_file.read())

    def save_as_json(self, TAMPLATE_MARGED_JSON):
        with open(TAMPLATE_MARGED_JSON, "wb") as f:
            serialized_glyf = orjson.dumps(self.marged_font, option=orjson.OPT_INDENT_2)
            f.write(serialized_glyf)
    
    def convert_json2otf(self, TAMPLATE_JSON, OUTPUT_FONT):
        cmd = "otfccbuild {} -o {}".format(TAMPLATE_JSON, OUTPUT_FONT)
        shell.process(cmd)

    def build(self, OUTPUT_FONT):
        self.add_cmap_uvs()
        print("cmap_uvs table を追加完了")
        self.add_glyph_order()
        print("glyph_order table を追加完了")
        self.add_glyf()
        print("glyf table を追加完了")
        # self.add_GSUB()
        # print("GSUB table を追加完了")
        TAMPLATE_MARGED_JSON = os.path.join(p.DIR_TEMP, "template.json")
        self.save_as_json(TAMPLATE_MARGED_JSON)
        cmd = "otfccbuild {} -o {}".format(TAMPLATE_MARGED_JSON, OUTPUT_FONT)
        shell.process(cmd)