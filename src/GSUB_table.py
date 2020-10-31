# -*- coding: utf-8 -*-
#!/usr/bin/env python

import re
import orjson
import pinyin_getter as pg
import utility

class GSUBTable():
    

    # マージ先のフォントのメインjson（フォントサイズを取得するため）, ピンイン表示に使うためのglyfのjson, ピンインのグリフを追加したjson(出力ファイル)
    def __init__(self, GSUB, PATTERN_ONE_TXT, PATTERN_TWO_JSON, EXCEPTION_PATTERN_JSON):
        # 今は上書きするだけ
        # calt も rclt も featute の数が多いと有効にならない。 feature には上限がある？ので、今は初期化して使う
        # rclt は calt と似ていて、かつ無効にできないタグ [Tag:'rclt'](https://docs.microsoft.com/en-us/typography/opentype/spec/features_pt#-tag-rclt)
        # 代替文字の指定、置換条件の指定
        # self.GSUB                   = GSUB 
        self.PATTERN_ONE_TXT        = PATTERN_ONE_TXT
        self.PATTERN_TWO_JSON       = PATTERN_TWO_JSON
        self.EXCEPTION_PATTERN_JSON = EXCEPTION_PATTERN_JSON

        # 初期化
        self.GSUB = {
            # 文字体系 ごとに使用する feature を指定する
            "languages": {
                "DFLT_DFLT": {
                    "features": [
                        "aalt_00000",
                        "rclt_00000"
                    ]
                },
                # 'hani' = CJK (中国語/日本語/韓国語)
                "hani_DFLT": {
                    "features": [
                        "aalt_00001",
                        "rclt_00001"
                    ]
                },
            },
            "lookups": {
                # aalt_0 は拼音が一つのみの漢字 + 記号とか。置き換え対象が一つのみのとき
                "lookup_aalt_0" : {
                    "type": "gsub_single",
                    "flags": {},
                    "subtables": [{}]
                },
                # aalt_1 は拼音が複数の漢字
                "lookup_aalt_1" : {
                    "type": "gsub_alternate",
                    "flags": {},
                    "subtables": [{}]
                },
                # pattern one
                "lookup_rclt_0": {
                    "type": "gsub_chaining",
                    "flags": {},
                    "subtables": [
                        # {
                        #     "match": [[],[]],
                        #     "apply": [
                        #         {
                        #             "at": -1, 
                        #             "lookup": ""
                        #         }
                        #     ],
                        #     "inputBegins": -1,
                        #     "inputEnds": -1
                        # }
                    ]
                },
                # pattern two
                "lookup_rclt_1": {
                    "type": "gsub_chaining",
                    "flags": {},
                    "subtables": [
                        # {
                        #     "match": [[],[]],
                        #     "apply": [
                        #         {
                        #             "at": -1, 
                        #             "lookup": ""
                        #         }
                        #     ],
                        #     "inputBegins": -1,
                        #     "inputEnds": -1
                        # }
                    ]
                },
                # exception pattern
                "lookup_rclt_2": {
                    "type": "gsub_chaining",
                    "flags": {},
                    "subtables": [
                        # {
                        #     "match": [[],[]],
                        #     "apply": [
                        #         {
                        #             "at": -1, 
                        #             "lookup": ""
                        #         }
                        #     ],
                        #     "inputBegins": -1,
                        #     "inputEnds": -1
                        # }
                    ]
                },
            },
            # feature ごとに使用する lookup table を指定する
            "features": {
                "aalt_00000": ["lookup_aalt_0","lookup_aalt_1"],
                "aalt_00001": ["lookup_aalt_0","lookup_aalt_1"],
                "rclt_00000": ["lookup_rclt_0","lookup_rclt_1","lookup_rclt_2"],
                "rclt_00001": ["lookup_rclt_0","lookup_rclt_1","lookup_rclt_2"]
            }, 
            "lookupOrder": ["lookup_aalt_0","lookup_aalt_1","lookup_rclt_0","lookup_rclt_1","lookup_rclt_2"]
        }
        self.lookup_order = set()
        self.load_pattern_table()
        self.generate_GSUB_table()
    

    def load_pattern_table(self):
        self.pattern_one = [{}]
        self.pattern_two = {}
        self.exception_pattern = {}
        with open(self.PATTERN_ONE_TXT, mode='r', encoding='utf-8') as read_file:
            for line in read_file:
                [str_order, hanzi, pinyin, patterns] = line.rstrip('\n').split(', ')
                order = int(str_order)
                # self.PATTERN_ONE_TXT の order = 1 は標準的なピンインなので無視する
                if 1 == order:
                    continue
                # 2 から異読のピンイン。添字に使うために -2 して 0 にする。
                idx = order-2
                if len(self.pattern_one) <= idx:
                    self.pattern_one.append({})
                tmp = self.pattern_one[idx]
                tmp.update(
                    {
                        hanzi:{
                            "variational_pronunciation": pinyin,
                            "patterns": patterns
                        }
                    }
                )
                
        with open(self.PATTERN_TWO_JSON, "rb") as read_file:
            self.pattern_two = orjson.loads(read_file.read())
        with open(self.EXCEPTION_PATTERN_JSON, "rb") as read_file:
            self.exception_pattern = orjson.loads(read_file.read())

    def make_aalt_feature(self):
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
        
        lookup_tables = self.GSUB["lookups"]
        aalt_0_subtables = lookup_tables["lookup_aalt_0"]["subtables"][0]
        aalt_1_subtables = lookup_tables["lookup_aalt_1"]["subtables"][0]

        # add
        for (hanzi, _) in utility.get_has_single_pinyin_hanzi():
            str_unicode = str(ord(hanzi))
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            aalt_0_subtables.update( {cid : "{}.ss00".format(cid) } )
        self.lookup_order.add( "lookup_aalt_0" )

        for (hanzi, pinyins) in utility.get_has_multiple_pinyin_hanzi():
            str_unicode = str(ord(hanzi))
            cid = utility.convert_str_hanzi_2_cid(hanzi)
            alternate_list = []
            # ss00 は ピンインのないグリフ なので、ピンインのグリフは "ss{:02}".format(len) まで
            for i in range( len(pinyins)+1 ):
                alternate_list.append("{}.ss{:02}".format(cid, i))
            aalt_1_subtables.update( {cid : alternate_list } )
        self.lookup_order.add( "lookup_aalt_1" )

    def make_rclt0_feature(self):
        # pattern one
        max_num_of_variational_pinyin = len(self.pattern_one)
        """
        self.pattern_one の中身
        e.g.:
        [
            {
                "行":{
                    "variational_pronunciation":"háng",
                    "patterns":"[~当|~家|~间|~列|~情|~业|发~|同~|外~|银~|~话|~会|~距]"
                },
                "作":{
                    "variational_pronunciation":"zuō",
                    "patterns":"[~坊|~弄|~揖]"
                }
            },
            {
                "行":{
                    "variational_pronunciation":"hàng",
                    "patterns":"[树~子]"
                },
                "作":{
                    "variational_pronunciation":"zuó",
                    "patterns":"[~料]"
                }
            },
            {
                "行":{
                    "variational_pronunciation":"héng",
                    "patterns":"[道~]"
                },
                "作":{
                    "variational_pronunciation":"zuo",
                    "patterns":"[做~]"
                }
            }
        ]
        """
        lookup_tables = self.GSUB["lookups"]
        # init 
        if max_num_of_variational_pinyin > 10:
            raise Exception("ピンインは10通りまでしか対応していません")
        for idx in range(max_num_of_variational_pinyin):
            lookup_name = "lookup_pattern_0{}".format(idx)
            lookup_tables.update( 
                { 
                    lookup_name : {
                        "type": "gsub_single",
                        "flags": {},
                        "subtables": [{}]
                    }
                } 
            )
            self.lookup_order.add( lookup_name )
        # add
        list_rclt_0_subtables = lookup_tables["lookup_rclt_0"]["subtables"]
        for idx in range(max_num_of_variational_pinyin):
            # to lookup table for replacing
            lookup_name = "lookup_pattern_0{}".format(idx)
            lookup_table_subtables = lookup_tables[lookup_name]["subtables"][0]
            for apply_hanzi in self.pattern_one[idx].keys():
                apply_hanzi_cid = utility.convert_str_hanzi_2_cid(apply_hanzi)
                lookup_table_subtables.update( { apply_hanzi_cid : "{}.ss{:02}".format(apply_hanzi_cid, pg.SS_VARIATIONAL_PRONUNCIATION + idx) } )
                # to rclt0
                str_patterns = self.pattern_one[idx][apply_hanzi]["patterns"]
                
                patterns = str_patterns.strip("[]").split('|') 
                # まとめて記述できるもの
                # e.g.:
                # sub [uni4E0D uni9280] uni884C' lookup lookup_0 ;
                # sub uni884C' lookup lookup_0　[uni4E0D uni9280] ;
                left_match  = [s for s in patterns if re.match("^~.$", s)]
                right_match = [s for s in patterns if re.match("^.~$", s)]
                # 一つ一つ記述するもの
                # e.g.:
                # sub uni85CF' lookup lookup_0 uni7D05 uni82B1 ;
                other_match = [s for s in patterns if not (s in (left_match + right_match))]

                if len(left_match) > 0:
                    context_hanzi_cids = [ utility.convert_str_hanzi_2_cid(context_hanzi) for context_hanzi in [context_hanzi.replace("~","") for context_hanzi in left_match] ]
                    list_rclt_0_subtables.append(
                        {
                            "match": [ [apply_hanzi_cid], context_hanzi_cids ],
                            "apply": [
                                {
                                "at": 0,
                                "lookup": lookup_name
                                }
                            ],
                            "inputBegins": 0,
                            "inputEnds": 1
                        }
                    )
                
                if len(right_match) > 0:
                    context_hanzi_cids = [ utility.convert_str_hanzi_2_cid(context_hanzi) for context_hanzi in [context_hanzi.replace("~","") for context_hanzi in right_match] ]
                    list_rclt_0_subtables.append(
                        {
                            "match": [ context_hanzi_cids, [apply_hanzi_cid] ],
                            "apply": [
                                {
                                "at": 1,
                                "lookup": "lookup_pattern_0{}".format(idx)
                                }
                            ],
                            "inputBegins": 1,
                            "inputEnds": 2
                        }
                    )

                for match_pattern in other_match:
                    at = match_pattern.index("~")
                    list_rclt_0_subtables.append(
                        {
                            "match": [ [utility.convert_str_hanzi_2_cid(hanzi)] for hanzi in match_pattern.replace("~", apply_hanzi) ],
                            "apply": [
                                {
                                "at": at,
                                "lookup": "lookup_pattern_0{}".format(idx)
                                }
                            ],
                            "inputBegins": at,
                            "inputEnds": at + 1
                        }
                    )
    
    def make_rclt1_feature(self):
        # pattern two
        lookup_tables = self.GSUB["lookups"]
        # to lookup table for replacing
        for lookup_name, table in self.pattern_two["lookup_table"].items():
            # init
            lookup_tables.update( 
                { 
                    lookup_name : {
                        "type": "gsub_single",
                        "flags": {},
                        "subtables": [{}]
                    }
                } 
            )
            # add
            lookup_table_subtables = lookup_tables[lookup_name]["subtables"][0]
            # e,g. "差": "差.ss05", -> "cid16957": "cid16957.ss05"
            lookup_table_subtables.update( { utility.convert_str_hanzi_2_cid(k): v.replace(k,utility.convert_str_hanzi_2_cid(k)) for k,v in table.items() } )
            self.lookup_order.add( lookup_name )
        # to rclt1
        list_rclt_1_subtables = lookup_tables["lookup_rclt_1"]["subtables"]
        for phrase, list_pattern_table in self.pattern_two["patterns"].items():
            applies = [] 
            ats = [] 
            for i in range(len(list_pattern_table)):
                table = list_pattern_table[i]
                # 要素は一つしかない. ほかに綺麗に取り出す方法が思いつかない.
                lookup_name = list(table.values())[0]
                if lookup_name != None:
                    ats.append(i)
                    applies.append(
                        {
                            "at": i,
                            "lookup": lookup_name
                        }
                    )
            
            list_rclt_1_subtables.append(
                        {
                            "match": [ [utility.convert_str_hanzi_2_cid(hanzi)] for hanzi in phrase ],
                            "apply": applies,
                            "inputBegins": min(ats),
                            "inputEnds": max(ats) + 1
                        }
                    )
    
    def make_rclt2_feature(self):
        # exception pattern
        lookup_tables = self.GSUB["lookups"]
        # to lookup table for replacing
        for lookup_name, table in self.exception_pattern["lookup_table"].items():
            # init
            lookup_tables.update( 
                { 
                    lookup_name : {
                        "type": "gsub_single",
                        "flags": {},
                        "subtables": [{}]
                    }
                } 
            )
            # add
            lookup_table_subtables = lookup_tables[lookup_name]["subtables"][0]
            # e,g. "着": "着.ss02",, -> "cid28651": "cid28651.ss05"
            lookup_table_subtables.update( { utility.convert_str_hanzi_2_cid(k): v.replace(k,utility.convert_str_hanzi_2_cid(k)) for k,v in table.items() } )
            self.lookup_order.add( lookup_name )
        # to rclt2
        list_rclt_2_subtables = lookup_tables["lookup_rclt_2"]["subtables"]
        for phrase, setting_of_phrase in self.exception_pattern["patterns"].items():
            ignore_pattern     = setting_of_phrase["ignore"]
            list_pattern_table = setting_of_phrase["pattern"]

            # ignore のパターンがあれば記述する
            if ignore_pattern != None:
                list_ignore_pattern = ignore_pattern.split(' ')
                tmp = [ hanzi for hanzi in list_ignore_pattern if re.match(".'", hanzi) ]
                if len(tmp) == 1:
                    apply_hanzi = tmp[0]
                else:
                    # 現在は、対象('がある)漢字はひとつだけと想定している
                    raise Exception("exception pattern の ignore 記述が間違っています。: \n {}".format(ignore_pattern))
                # 空白とシングルコートを削除
                ignore_phrase = ignore_pattern.replace(" ", "").replace("'", "")
                at = list_ignore_pattern.index(apply_hanzi)
                list_rclt_2_subtables.append(
                        {
                            "match": [ [utility.convert_str_hanzi_2_cid(hanzi)] for hanzi in ignore_phrase ],
                            "apply": [],
                            "inputBegins": at,
                            "inputEnds": at + 1
                        }
                    )
            # 期待する普通のパターン
            applies = [] 
            ats = [] 
            for i in range(len(list_pattern_table)):
                table = list_pattern_table[i]
                # 要素は一つしかない. ほかに綺麗に取り出す方法が思いつかない.
                lookup_name = list(table.values())[0]
                if lookup_name != None:
                    ats.append(i)
                    applies.append(
                        {
                            "at": i,
                            "lookup": lookup_name
                        }
                    )
            list_rclt_2_subtables.append(
                        {
                            "match": [ [utility.convert_str_hanzi_2_cid(hanzi)] for hanzi in phrase ],
                            "apply": applies,
                            "inputBegins": min(ats),
                            "inputEnds": max(ats) + 1
                        }
                    )
    
    def make_lookup_order(self):
        # lookup order
        """
        e.g.:
        "lookupOrder": [
            "lookup_rclt_0",
            "lookup_rclt_1",
            "lookup_ccmp_2",
            "lookup_11_3"
        ]
        """
        union_lookup_order = set(self.GSUB["lookupOrder"]) | self.lookup_order
        list_lookup_order = list(union_lookup_order)
        list_lookup_order.sort()
        self.GSUB.update( {"lookupOrder" : list_lookup_order} )

    def generate_GSUB_table(self):
        
        self.make_aalt_feature()


        # lookups の rclt
        """
        e.g.:
        adobe version
        lookup rclt0 {
            sub [uni4E0D uni9280] uni884C' lookup lookup_0 ;
        } rclt0;
        """
        """
        json version
        "lookups": {
            "lookup_rclt_0": {
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
        self.make_rclt0_feature()
        self.make_rclt1_feature()
        self.make_rclt2_feature()

        self.make_lookup_order()

        # 保存して確認する
        # with open("GSUB.json", "wb") as f:
        #     serialized_glyf = orjson.dumps(self.GSUB, option=orjson.OPT_INDENT_2)
        #     f.write(serialized_glyf)


    def get_GSUB_table(self):
        return self.GSUB