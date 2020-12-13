# -*- coding: utf-8 -*-
#!/usr/bin/env python'

import shell
import orjson
import os
import copy
import pinyin_getter as pg
import pinyin_glyph as py_glyph
import utility
import path as p
import GSUB_table as gt
import name_table as nt

class Font():
    def __init__(self, TAMPLATE_MAIN_JSON, TAMPLATE_GLYF_JSON, ALPHABET_FOR_PINYIN_JSON, \
                        PATTERN_ONE_TXT, PATTERN_TWO_JSON, EXCEPTION_PATTERN_JSON):
        self.TAMPLATE_MAIN_JSON     = TAMPLATE_MAIN_JSON
        self.TAMPLATE_GLYF_JSON     = TAMPLATE_GLYF_JSON
        self.PATTERN_ONE_TXT        = PATTERN_ONE_TXT
        self.PATTERN_TWO_JSON       = PATTERN_TWO_JSON
        self.EXCEPTION_PATTERN_JSON = EXCEPTION_PATTERN_JSON
        self.load_json()
        # utility を使うために設定する
        utility.cmap_table = self.marged_font["cmap"]
        self.PINYIN_MAPPING_TABLE = pg.get_pinyin_table_with_mapping_table()

        # 発音のグリフを作成する
        pinyin_glyph = py_glyph.PinyinGlyph(TAMPLATE_MAIN_JSON, ALPHABET_FOR_PINYIN_JSON)
        self.py_alphablet = pinyin_glyph.get_py_alphablet_glyf_table()
        pinyin_glyph.add_references_of_pronunciation()
        self.pronunciation = pinyin_glyph.get_pronunciation_glyf_table()
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
        # もし、別のグリフが用意されているなら、グリフ数削減のためにも参照を先を統一する。
        self.integrate_reference_of_wu4()
        self.integrate_reference_of_hu4()

    # ⺎(U+2E8E) 兀(U+5140) 兀(U+FA0C)
    def integrate_reference_of_wu4(self):
        wu4_str_oct_unicodes = [str(0x2E8E), str(0x5140), str(0xFA0C)]
        self.integrate_reference_of_duplicate_hanzi(wu4_str_oct_unicodes)
    
    # 嗀(U+55C0) 嗀(U+FA0D)
    def integrate_reference_of_hu4(self):
        hu4_str_oct_unicodes = [str(0x55C0), str(0xFA0D)]
        self.integrate_reference_of_duplicate_hanzi(hu4_str_oct_unicodes)

    # 重複して定義されている漢字においてグリフが複数あるときには参照するグリフを一つにする
    def integrate_reference_of_duplicate_hanzi(self, duplicate_hanzi_unicodes):
        refered_set_glyf_name = set()
        cmap_table = self.marged_font["cmap"]

        for str_oct_unicode in duplicate_hanzi_unicodes:
            if str_oct_unicode in cmap_table:
                refered_set_glyf_name.add(cmap_table[str_oct_unicode])
        refered_glyf_names = list(refered_set_glyf_name)
        refered_glyf_names.sort()
        # 参照先が一つのときは問題ないので抜ける
        if len(refered_glyf_names) < 2:
            return

        for str_oct_unicode in duplicate_hanzi_unicodes:
            if str_oct_unicode in cmap_table:
                # 最初のものに統一する
                refered_glyf_name = refered_glyf_names[0]
                # 不要なグリフの削除
                delete_glyf_name = cmap_table[str_oct_unicode]
                self.delete_glyf(delete_glyf_name)
                # 参照するグリフを更新
                cmap_table.update( {str_oct_unicode : refered_glyf_name} )

    def delete_glyf(self, glyf_name):
        # 空のグリフのテーブル（管理しやすくするために、glyf table は別オブジェクトになっている）
        template_glyf_table  = self.marged_font["glyf"]
        glyph_order_list     = self.marged_font["glyph_order"]
        
        if glyf_name in template_glyf_table:
            del template_glyf_table[glyf_name]
        if glyf_name in self.substance_glyf_table:
            del self.substance_glyf_table[glyf_name]
        if glyf_name in glyph_order_list:
            glyph_order_list.remove(glyf_name)

        print(glyf_name)

    def get_advance_size_of_hanzi(self):
        # なんでもいいが、とりあえず漢字の「一」でサイズを取得する
        cid = self.marged_font["cmap"][str(ord("一"))]
        # advanceWidth は確実にあるはずなので、有無の検証はしない
        if not ("advanceHeight" in self.marged_font["glyf"][cid]):
            glyf_cid = self.marged_font["glyf"][cid]
            glyf_cid.update( {"advanceHeight": self.marged_font["glyf"][cid]["advanceWidth"]} )

        advanceWidth   = self.marged_font["glyf"][cid]["advanceWidth"]
        advanceHeight  = self.marged_font["glyf"][cid]["advanceHeight"]
        return (advanceWidth, advanceHeight)

    def get_advance_size_of_pinyin_glyf(self):
        # なんでもいいが、とりあえず「yi1」でサイズを取得する
        advanceWidth  = self.pronunciation["yi1"]["advanceWidth"]
        advanceHeight = self.pronunciation["yi1"]["advanceHeight"]
        verticalOrigin = self.pronunciation["yi1"]["verticalOrigin"]
        return (advanceWidth, advanceHeight, verticalOrigin)
    
    def add_cmap_uvs(self):
        IVS = 0xE01E0 #917984
        """
        e.g.:
        hanzi_glyf　　　　標準の読みの拼音
        hanzi_glyf.ss00　ピンインの無い漢字グリフ。設定を変更するだけで拼音を変更できる
        hanzi_glyf.ss01　（異読のピンインがあるとき）標準の読みの拼音（uni4E0D と重複しているが GSUB の置換（多音字のパターン）を無効にして強制的に置き換えるため）
        hanzi_glyf.ss02　（異読のピンインがあるとき）以降、異読
        ...
        """
        if not ("cmap_uvs" in self.marged_font):
            self.marged_font.update( {"cmap_uvs": {}} )

        for (hanzi, pinyins) in utility.get_has_single_pinyin_hanzi():
            str_oct_unicode = str(ord(hanzi))
            if not (str_oct_unicode in self.marged_font["cmap"]):
                raise Exception("グリフが見つかりません.\n  unicode: {}".format(str_oct_unicode))
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            self.marged_font["cmap_uvs"]["{0} {1}".format(str_oct_unicode, IVS)] = "{}.ss00".format(cid)
        
        for (hanzi, pinyins) in utility.get_has_multiple_pinyin_hanzi():
            str_oct_unicode = str(ord(hanzi))
            if not (str_oct_unicode in self.marged_font["cmap"]):
                raise Exception("グリフが見つかりません.\n  unicode: {}".format(str_oct_unicode))
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            # ss00 は ピンインのないグリフ なので、ピンインのグリフは "ss{:02}".format(len) まで
            for i in range( len(pinyins)+1 ):
                self.marged_font["cmap_uvs"]["{0} {1}".format(str_oct_unicode, IVS + i)] = "{}.ss{:02}".format(cid, i)

    def add_glyph_order(self):
        """
        e.g.: 
        "glyph_order": [
            ...
            "uni4E0D","uni4E0D.ss00","uni4E0D.ss01","uni4E0D.ss02","uni4E0D.ss03",
            ...
        ]
        """
        # 漢字グリフ追加
        set_glyph_order = set(self.marged_font["glyph_order"])
        for (hanzi, pinyins) in utility.get_has_single_pinyin_hanzi():
            str_oct_unicode = str(ord(hanzi))
            if not (str_oct_unicode in self.marged_font["cmap"]):
                raise Exception("グリフが見つかりません.\n  unicode: {:x}".format(int(str_oct_unicode)))
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            set_glyph_order.add("{}.ss00".format(cid))

        for (hanzi, pinyins) in utility.get_has_multiple_pinyin_hanzi():
            str_oct_unicode = str(ord(hanzi))
            if not (str_oct_unicode in self.marged_font["cmap"]):
                raise Exception("グリフが見つかりません.\n  unicode: {:x}".format(int(str_oct_unicode)))
            # ss00 は ピンインのないグリフ なので、ピンインのグリフは "ss{:02}".format(len) まで
            for i in range( len(pinyins)+1 ):
                cid = utility.convert_str_hanzi_2_cid(hanzi)
                set_glyph_order.add("{}.ss{:02}".format(cid, i))
        
        # ピンインのグリフを追加
        set_glyph_order = set_glyph_order | set(self.py_alphablet.keys())
        new_glyph_order = list(set_glyph_order)
        new_glyph_order.sort()
        self.marged_font["glyph_order"] = new_glyph_order
        # print(self.marged_font["glyph_order"])

    def generate_hanzi_glyf_with_normal_pinyin(self, cid):
        (advance_width, _) = self.get_advance_size_of_hanzi()
        (_, added_pinyin_height, added_pinyin_vertical_origin) = self.get_advance_size_of_pinyin_glyf()
        hanzi_glyf = {
                         "advanceWidth": advance_width,
                         "advanceHeight": added_pinyin_height,
                         "verticalOrigin": added_pinyin_vertical_origin,
                         "references": [
                             {"glyph":"{}.ss01".format(cid),"x":0, "y":0, "a":1, "b":0, "c":0, "d":1}
                         ]
                     }
        return hanzi_glyf

    def generate_hanzi_glyf_with_pinyin(self, cid, pronunciation):
        (advance_width, _) = self.get_advance_size_of_hanzi()
        (_, added_pinyin_height, added_pinyin_vertical_origin) = self.get_advance_size_of_pinyin_glyf()
        simpled_pronunciation = utility.simplification_pronunciation( pronunciation )
        # ピンインと無印の漢字(ss00) を組み合わせる
        glyf_data = self.pronunciation[simpled_pronunciation]
        # ミュータブルなオブジェクトは参照元に追加してしまうので、copy する。
        references = copy.copy(glyf_data["references"])
        references.append( {"glyph":"{}.ss00".format(cid), "x":0, "y":0, "a":1, "b":0, "c":0, "d":1} )
        hanzi_glyf = {
                         "advanceWidth": advance_width,
                         "advanceHeight": added_pinyin_height,
                         "verticalOrigin": added_pinyin_vertical_origin,
                         "references": references
                     }
        return hanzi_glyf
    
    
    # unicode 上に定義が重複している漢字があるとエラーになるので判定を入れる
    # Exception: otfccbuild : Build : [WARNING] [Stat] Circular glyph reference found in gid 11663 to gid 11664. The reference will be dropped.
    def is_added_glyf_4_duplicate_definition_of_hanzi(self, str_oct_unicode):
        duplicate_definition_of_hanzes = [str_oct_unicode for str_oct_unicode, _ in self.duplicate_definition_of_hanzes.items()]
        if str_oct_unicode in duplicate_definition_of_hanzes:
            idx = self.duplicate_definition_of_hanzes[str_oct_unicode]
            return self.is_added_glyf[idx]
        return False

    def update_status_is_added_glyf_4_duplicate_definition_of_hanzi(self, str_oct_unicode):
        duplicate_definition_of_hanzes = [str_oct_unicode for str_oct_unicode, _ in self.duplicate_definition_of_hanzes.items()]
        if str_oct_unicode in duplicate_definition_of_hanzes:
            idx = self.duplicate_definition_of_hanzes[str_oct_unicode]
            self.is_added_glyf[idx] = True
                
    def add_glyf(self):
        """
        e.g.: 
        hanzi_glyf　　　　標準の読みの拼音
        hanzi_glyf.ss00　ピンインの無い漢字グリフ。設定を変更するだけで拼音を変更できる
        hanzi_glyf.ss01　（異読のピンインがあるとき）標準の読みの拼音（uni4E0D と重複しているが GSUB の置換（多音字のパターン）を無効にして強制的に置き換えるため）
        hanzi_glyf.ss02　（異読のピンインがあるとき）以降、異読
        """
        """
        Sawarabi
        "uni4E00": {
            "advanceWidth": 1000,
            "advanceHeight": 1000,
            "verticalOrigin": 952,
        """
        # グリフ数削減のために最低限のグリフのみを作成する
        # if "hanzi_glyf" has normal pronunciation only
        # hanzi_glyf -> hanzi_glyf.ss00
        # hanzi_glyf = hanzi_glyf.ss00 + normal pronunciation
        for (hanzi, pinyins) in utility.get_has_single_pinyin_hanzi():
            str_oct_unicode = str(ord(hanzi))
            if not (str_oct_unicode in self.marged_font["cmap"]):
                raise Exception("グリフが見つかりません.\n  unicode: {}".format(str_oct_unicode))
            if self.is_added_glyf_4_duplicate_definition_of_hanzi(str_oct_unicode):
                continue
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            glyf_data = self.substance_glyf_table[cid]
            self.substance_glyf_table.update( { "{}.ss00".format(cid) : glyf_data } )
            normal_pronunciation = pinyins[pg.NORMAL_PRONUNCIATION]
            glyf_data = self.generate_hanzi_glyf_with_pinyin(cid, normal_pronunciation)
            self.substance_glyf_table.update( { cid : glyf_data } )

        # if "hanzi_glyf" has variational pronunciation
        # hanzi_glyf -> hanzi_glyf.ss00
        # hanzi_glyf.ss01 = hanzi_glyf.ss00 + normal pronunciation
        # hanzi_glyf = hanzi_glyf.ss01
        # hanzi_glyf.ss02 = hanzi_glyf.ss00 + variational pronunciation
        for (hanzi, pinyins) in utility.get_has_multiple_pinyin_hanzi():
            str_oct_unicode = str(ord(hanzi))
            if not (str_oct_unicode in self.marged_font["cmap"]):
                raise Exception("グリフが見つかりません.\n  unicode: {}".format(str_oct_unicode))
            if self.is_added_glyf_4_duplicate_definition_of_hanzi(str_oct_unicode):
                continue
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            glyf_data = self.substance_glyf_table[cid]
            # hanzi_glyf -> hanzi_glyf.ss00
            self.substance_glyf_table.update( { "{}.ss00".format(cid) : glyf_data } )
            # hanzi_glyf.ss01 = hanzi_glyf.ss00 + normal pronunciation
            normal_pronunciation = pinyins[pg.NORMAL_PRONUNCIATION]
            glyf_data = self.generate_hanzi_glyf_with_pinyin(cid, normal_pronunciation)
            self.substance_glyf_table.update( { "{}.ss01".format(cid) : glyf_data } )
            # hanzi_glyf = hanzi_glyf.ss01
            glyf_data = self.generate_hanzi_glyf_with_normal_pinyin(cid)
            self.substance_glyf_table.update( { cid : glyf_data } )
            # if hanzi_glyf has variational pronunciation
            # hanzi_glyf.ss01 = hanzi_glyf.ss00 + variational pronunciation
            for i in range( 1,len(pinyins) ):
                variational_pronunciation = pinyins[i]
                glyf_data = self.generate_hanzi_glyf_with_pinyin(cid, variational_pronunciation)
                self.substance_glyf_table.update( { "{}.ss{:02}".format(cid, pg.VARIATIONAL_PRONUNCIATION + i) : glyf_data } )
            self.update_status_is_added_glyf_4_duplicate_definition_of_hanzi(str_oct_unicode)

        new_glyf = self.marged_font["glyf"]
        new_glyf.update( self.py_alphablet )
        new_glyf.update( self.substance_glyf_table )
        self.marged_font["glyf"] = new_glyf
        print("  ==> glyf num : {}".format(len(self.marged_font["glyf"])))
        if len(self.marged_font["glyf"]) > 65536:
            raise Exception("glyf は 65536 個以上格納できません。")


    def add_GSUB(self):
        GSUB = gt.GSUBTable(self.marged_font["GSUB"], self.PATTERN_ONE_TXT, self.PATTERN_TWO_JSON, self.EXCEPTION_PATTERN_JSON)
        self.marged_font["GSUB"] = GSUB.get_GSUB_table()

    def set_about_size(self):
        (_, advanceAddedPinyinHeight, _) = self.get_advance_size_of_pinyin_glyf()
        if advanceAddedPinyinHeight > self.marged_font["head"]["yMax"]:
            # すべてのグリフの輪郭を含む範囲
            self.marged_font["head"]["yMax"] = advanceAddedPinyinHeight
        if advanceAddedPinyinHeight > self.marged_font["hhea"]["ascender"]:
            # 原点からグリフの上端までの距離
            self.marged_font["hhea"]["ascender"] = advanceAddedPinyinHeight
        # 特定の言語のベースライン
        # self.marged_font["BASE"]["hani"]

    def set_copyright(self):
        # フォント製作者によるバージョン
        self.marged_font["head"]["fontRevision"] = nt.VISION
        # 作成日(基準日：1904/01/01 00:00 GMT)
        from datetime import datetime
        base_date = datetime.strptime("1904/01/01 00:00", "%Y/%m/%d %H:%M")
        base_time = base_date.timestamp()
        now_time  = datetime.now().timestamp() 
        self.marged_font["head"]["created"] = round( now_time - base_time )
        # フォント名等を設定
        self.marged_font["name"] = nt.name_table


    def load_json(self):
        with open(self.TAMPLATE_MAIN_JSON, "rb") as read_file:
            self.marged_font = orjson.loads(read_file.read())
        with open(self.TAMPLATE_GLYF_JSON, "rb") as read_file:
            self.substance_glyf_table = orjson.loads(read_file.read())

    def save_as_json(self, TAMPLATE_MARGED_JSON):
        with open(TAMPLATE_MARGED_JSON, "wb") as f:
            serialized_glyf = orjson.dumps(self.marged_font, option=orjson.OPT_INDENT_2)
            f.write(serialized_glyf)
    
    def convert_json2otf(self, TAMPLATE_JSON, OUTPUT_FONT):
        cmd = "otfccbuild {} -o {}".format(TAMPLATE_JSON, OUTPUT_FONT)
        print(cmd)
        shell.process(cmd)

    def build(self, OUTPUT_FONT):
        self.add_cmap_uvs()
        print("cmap_uvs table を追加完了")
        self.add_glyph_order()
        print("glyph_order table を追加完了")
        self.add_glyf()
        print("glyf table を追加完了")
        self.add_GSUB()
        print("GSUB table を追加完了")
        self.set_about_size()
        self.set_copyright()
        TAMPLATE_MARGED_JSON = os.path.join(p.DIR_TEMP, "template.json")
        self.save_as_json(TAMPLATE_MARGED_JSON)
        self.convert_json2otf(TAMPLATE_MARGED_JSON, OUTPUT_FONT)